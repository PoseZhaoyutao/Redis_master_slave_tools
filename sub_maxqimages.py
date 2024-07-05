# -*- coding: utf-8 -*-
# @Author  : Zhao Yutao
# @Time    : 2024/7/1 11:30
# @Function: 
# @mails: zhaoyutao22@mails.ucas.ac.cn
import os
import time
import imageio
import redis
import base64
from PIL import Image
import io
import time

connection_pool1 = redis.ConnectionPool(host="10.2.29.144", port=6379)
rc1 = redis.Redis(connection_pool=connection_pool1)  # 连接redis

connection_pool = redis.ConnectionPool(host="10.2.29.144", port=6377)
rc = redis.Redis(connection_pool=connection_pool)  # 连接redis
ps = rc.pubsub()
charecter = "img"
ps.subscribe(charecter + str(0))
count = 0

while 1:
    item = ps.get_message()
    if item:
        if type(item["data"]) is int:
            pass
        else:
            if str(item["data"],encoding='utf-8') == 'img0':
                print("图像")
                start = time.time()
                img_base64 = rc.get(item['data'])
                img_data = base64.b64decode(img_base64)  # 将拿到的base64的图片转换回来
                img = Image.open(io.BytesIO(img_data)).convert("RGB")
                imageio.imwrite('redissubimagedata/' + str(count)+".png", img)
            elif str(item["data"],encoding='utf-8') == 'img1':
                print("名字")
                img_name = str(rc.get(item['data']),encoding='utf-8')
                os.rename('redissubimagedata/' + str(count)+".png", 'redissubimagedata/' + img_name)
                print(img_name)
                rc.delete(charecter + str(0))
                count += 1
                rc1.publish("result", count)
                print("img cost time:", time.time() - start)
        time.sleep(0.01)

# for item in ps.listen():
#     count += 1
#     print("get message")
#     start = time.time()
#     if item['type'] == 'message' and item['data'] is not None:
#         img_base64 = rc.get(item['data'])
#         img_data = base64.b64decode(img_base64)  # 将拿到的base64的图片转换回来
#         img = Image.open(io.BytesIO(img_data)).convert("RGB")
#         imageio.imwrite('redis_subimagedata/' + str(count) + ".png", img)
#         rc.delete(charecter + str(0))
#         rc1.publish("result", count)
#         print("img cost time:", time.time() - start)
