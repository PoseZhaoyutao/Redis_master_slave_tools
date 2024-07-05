# -*- coding: utf-8 -*-
# @Author  : Zhao Yutao
# @Time    : 2024/7/1 12:29
# @Function: 测试redis服务端发送图像
# @mails: zhaoyutao22@mails.ucas.ac.cn
import os
import re
import redis
import cv2
import scipy.misc
import time
import base64
import _thread
from scipy.spatial.transform import Rotation as R

# 四元数转矩阵
def quaternion2rot(quaternion):
    r = R.from_quat(quaternion)
    rot = r.as_matrix()
    return rot


# 矩阵转四元数
def rot2quaternion(rot):
    r = R.from_matrix(rot)
    qua = r.as_quat()
    return qua


# 四元数转欧拉角 外旋
def quaternion2euler(quaternion):
    r = R.from_quat(quaternion)
    euler = r.as_euler('zyx', degrees=True)
    return euler


# 欧拉角转四元数
def euler2quaternion(euler):
    r = R.from_euler('zyx', euler, degrees=True)
    quaternion = r.as_quat()
    return quaternion

def natural_sort_key(s):
    """
    按文件名的结构排序，即依次比较文件名的非数字和数字部分
    """
    # 将字符串按照数字和非数字部分分割，返回分割后的子串列表
    sub_strings = re.split(r'(\d+)', s)
    # 如果当前子串由数字组成，则将它转换为整数；否则返回原始子串
    sub_strings = [int(c) if c.isdigit() else c for c in sub_strings]
    # 根据分割后的子串列表以及上述函数的返回值，创建一个新的列表
    # 按照数字部分从小到大排序，然后按照非数字部分的字典序排序
    return sub_strings

def nameQ2euler2gtQ(name):
    '''
    qx_qy_qz_qw需要转成欧拉角后加上内旋（0,0,23.439291）然后再转为四元数进行命名
    :param name:
    :return:
    '''
    name_s = name.split("_")
    nameq = list(map(float,name.split("_")[7:11]))
    name_rot= quaternion2rot(nameq)
    rpy = quaternion2euler(nameq)
    new_rpy = (rpy[0],rpy[1],rpy[2]+23.439291)
    # xxxx1 = quaternion2rot(euler2quaternion((0,0,-23.439291)))
    # new_nameq = rot2quaternion(name_rot @ xxxx1)
    new_nameq = euler2quaternion(new_rpy)
    name_s[7:11] = list(map(str,new_nameq))
    new_name = '_'.join(name_s)
    return new_name


connection_pool = redis.ConnectionPool(host="10.2.29.214", port=6380)
rc = redis.Redis(connection_pool=connection_pool)  # 连接redis
connection_pool1 = redis.ConnectionPool(host="10.2.29.214", port=6378)
rc1 = redis.Redis(connection_pool=connection_pool1)  # 连接redis
ps = rc1.pubsub()
pipe = rc.pipeline(transaction=False)

def pubsub_callback_img(path):
    filepath = path
    imgname_list = os.listdir(filepath)
    imgname_list = sorted(imgname_list,key=natural_sort_key)
    Max_index = len(imgname_list)
    i = 0
    img_path = os.path.join(filepath, imgname_list[i])
    img = cv2.imread(img_path)
    img_str = cv2.imencode('.png', img)[1].tostring()
    data = base64.b64encode(img_str)  # 将图片转换成base64再传输
    charecter = "img"
    imgname = nameQ2euler2gtQ(imgname_list[i])
    pipe.set(charecter + str(0), data)
    pipe.set(charecter + str(1), imgname)
    pipe.publish(charecter + str(0), charecter + str(0))
    pipe.publish(charecter + str(0), charecter + str(1))
    pipe.execute()
    # rc.set(charecter + str(0), data)
    # rc.publish(charecter + str(0), charecter + str(0))
    ps.subscribe("result")

    while 1:
        item = ps.get_message()
        if item:
    # for item in ps.listen():
            if item['type'] == 'message' and item["data"] is not None:
                i+=1
                rc1.set("result","")
                try:
                    img_path = os.path.join(filepath, imgname_list[i])
                    img = cv2.imread(img_path)
                    img_str = cv2.imencode('.png', img)[1].tostring()
                    data = base64.b64encode(img_str)  # 将图片转换成base64再传输
                    # rc.set(charecter + str(0), data)
                    # rc.publish(charecter + str(0), charecter + str(0))
                    imgname = nameQ2euler2gtQ(imgname_list[i])
                    pipe.set(charecter + str(0), data)
                    pipe.set(charecter + str(1), imgname)
                    pipe.publish(charecter + str(0),charecter + str(0))
                    pipe.publish(charecter + str(0),charecter + str(1))
                    pipe.execute()
                except IndexError as e:
                    while len(imgname_list) <= Max_index:
                        imgname_list = os.listdir(filepath)
                        imgname_list = sorted(imgname_list, key=natural_sort_key)
                    Max_index = len(imgname_list)
                except Exception as e:
                    while len(imgname_list) <= Max_index:
                        imgname_list = os.listdir(filepath)
                        imgname_list = sorted(imgname_list, key=natural_sort_key)
                    Max_index = len(imgname_list)
                    img_path = os.path.join(filepath, imgname_list[Max_index-1])
                    img = cv2.imread(img_path)
                    img_str = cv2.imencode('.png', img)[1].tostring()
                    data = base64.b64encode(img_str)  # 将图片转换成base64再传输
                    # rc.set(charecter + str(0), data)
                    # rc.publish(charecter + str(0), charecter + str(0))
                    imgname = nameQ2euler2gtQ(imgname_list[Max_index-1])
                    pipe.set(charecter + str(0), data)
                    pipe.set(charecter + str(1), imgname)
                    pipe.publish(charecter + str(0),charecter + str(0))
                    pipe.publish(charecter + str(0),charecter + str(1))
                    pipe.execute()
                    print(e)
                finally:
                    # 实现每渲染一张图像就可以发送一次
                    while len(imgname_list) <= Max_index:
                        imgname_list = os.listdir(filepath)
                        imgname_list = sorted(imgname_list, key=natural_sort_key)
                    Max_index = len(imgname_list)
                print("---------",int(item["data"]),"-------------")


if __name__ == '__main__':
    pubsub_callback_img(r"D:\Max_datasets\normal")
