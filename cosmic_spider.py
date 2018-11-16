# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2018/11/16 10:02 AM
# @Author : cxa
# @File : cosmic.py
# @Software: PyCharm
# encoding: utf-8
from requests_html import HTMLSession
import aiohttp
import asyncio
import hashlib
import os
from traceback import format_exc
import base64
from cryptography.fernet import Fernet
# 文件下载也要是异步
import aiofiles
import multiprocessing
from tomorrow import threads
from retrying import retry

workers = multiprocessing.cpu_count() * 2 + 1
# 开始索引数
strat_num = 227002
# 结束索引数
end_num = 250606
key = "X0JxSkg4NFVBQVBPODlUM0VzT1liNnloeWtLcndkSldRT2xURzQ4MEM5RT0="
page_num_xpath = "//p[@class='selectpage']/select[@id='page_number']/option[last()]/@file"
page_id_xpath = "//img[@id='thumbnail']/@src"


def aes_cbc_decrypt(message):
    decrypted_text = Fernet(base64.b64decode(key).decode("utf8")).decrypt(bytes("{}".format(message), encoding="utf8"))
    return decrypted_text.decode("utf8")


# 漫画题目
cosmic_name = "//head//title/text()"
# 漫画id
cosmic_id = "//img[@id='curPic']/@src"
main_url = aes_cbc_decrypt(
    "gAAAAABbNdhqCnxkaJwZ2VL7HUXne_IOic-NsHtE30W-J68oecVmgm0dzO_lLXgTlI7a5_NbUWlkGm7FqLwY81XIBddNWbac4rCgBA9NFAECsNISkhTvdRl4uDSaS6bHY8sbcJJwO13Z")
cosmic_urllist = [main_url.format(i) for i in range(strat_num, end_num + 1)]
pagenum_xpath = "//font[@id='TotalPage']/text()"
full_url = aes_cbc_decrypt(
    "gAAAAABbNdk5FLeX55hOiDAXxgCwwYmGrokYvU3Nd1AOYuOE7OdIEcBdAmSG_Q3kOltealBKMOgUBKDuPUJtzFFPwqoxL-FUip"
    "VNQU-JmBW_K5qxgzTQ3IOla_F61Rscy0fJOaN-mEXKPqrakctyDRN7OVm1LARTMhylQELLuBnJgIT4WXilchg=")  # 漫画的总id，序号的id和格式使用(jpg)
session = HTMLSession()
sema = asyncio.Semaphore(5)
session = HTMLSession()


async def getbuff(url, c_name):
    async with aiohttp.ClientSession() as session2:
        async with session2.get(url, timeout=60) as r:
            buff = await r.read()
            if not len(buff):
                url = url.replace(".jpg", ".png")
                async with session2.get(url, timeout=60) as r2:
                    buff = await r2.read()
            print("nowurl:", url)
            await getimg(url, buff, c_name)


async def run(url, c_name):
    with (await sema):
        await getbuff(url, c_name)


#
@threads(30)
@retry(stop_max_attempt_number=3)
def asyc_get_req(url):
    req = session.get(url, timeout=15)
    if req.status_code == 200:
        return req
    else:
        raise ValueError("访问出错")


def spider(req):
    try:
        if req.status_code == 200:
            root = req.html
            name = root.xpath(cosmic_name)[0]
            print(name)
            with open("1.html", 'a', encoding='utf-8') as fs:
                fs.write(req.text)
            print(full_url)
            id = root.xpath(page_id_xpath)[0].split('/')[-2]
            max_page = root.xpath(page_num_xpath)[0].split('.')[0]
            full_urllist = [full_url.format(id, i, "jpg") for i in range(1, int(max_page) + 1)]
            event_loop = asyncio.get_event_loop()
            tasks = [run(url, name) for url in full_urllist]
            results = event_loop.run_until_complete(asyncio.wait(tasks))
    except:
        print(format_exc())


async def getimg(url, buff, c_name):
    # 题目那层目录
    filepath = os.path.join(os.getcwd(), "comics_images", c_name)
    # 如果标题太长就转md5，然后单独启动一个text写入内容为标题
    md5name = hashlib.md5(c_name.encode("utf-8")).hexdigest()
    filepath2 = os.path.join(os.getcwd(), "comics_images", md5name)

    id = url.split('/')[-1]
    image_id = os.path.join(filepath, id)
    image_id2 = os.path.join(filepath2, md5name)

    # 题目层目录是否存在
    if not os.path.exists(filepath) and not os.path.exists(filepath2):
        try:
            os.makedirs(filepath)
        except:
            os.makedirs(filepath2)
            image_id = image_id2
            fs = await aiofiles.open(os.path.join(filepath2, "title.txt"), 'w')
            await fs.write(c_name)

    # 文件是否存在
    if not os.path.exists(image_id) and not os.path.exists(image_id2):
        print("savepath:", image_id)
        f = await aiofiles.open(image_id, 'wb')
        await f.write(buff)


if __name__ == '__main__':
    # with ThreadPool(workers) as pool:
    #     pool.map(spider, cosmic_urllist)
    req_list = []
    for url in cosmic_urllist:
        req = asyc_get_req(url)
        req_list.append(req)

    for req in req_list:
        spider(req)
