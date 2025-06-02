import requests 
from bs4 import BeautifulSoup
import re
import asyncio
import aiohttp
import aiofiles
from Crypto.Cipher import AES
import os

def get_iframe_src(url):
    resp = requests.get(url)
    main_page = BeautifulSoup(resp.text,"html.parser")
    src = main_page.find("iframe").get("src")
    return src
    # return "https://boba.52kuyun.com/share/xfPs9NPHvYGhNzFp"

def get_first_m3u8_url(src):
    resp = requests.get(src)
    obj = re.compile(r'var main = "(?P<m3u8_url>.*?)";',re.S)
    m3u8_url=obj.search(resp.text).group("m3u8_url")
    return m3u8_url

def download_m3u8_file(url,name):
    resp = requests.get(url)
    with open(name,"wb") as f:
        f.write(resp.content)

async def download_ts(url,name,session):
    async with session.get(url) as resp:
        async with aiofiles.open(f"《越狱》第一季第一集/{name}","wb") as f:
            await f.write(await resp.content.read())


async def aio_download(up_url):
    tasks=[]
    async with aiohttp.ClientSession() as session:
        async with aiofiles.open("《越狱》第一季第一集_second_m3u8.txt","r",encoding='utf-8') as f:
            async for line in f:
                line = line.strip()
                if line.startswith("#"):
                    continue
                ts_url = up_url+line
                task = asyncio.create_task(download_ts(ts_url,line,session))
                tasks.append(task)
            
             await asyncio.wait(tasks)

def get_key(url):
    resp= requests.get(url)
    return resp.text
    # return "c5878c26baaaac8c"

async def dec_ts(name,key):
    aes = AES.new(key =key,mode=AES.MODE_CBC,IV=b"0000000000000000")
    async with aiofiles.open(f"《越狱》第一季第一集/{name}","rb") as f1,\
        aiofiles.open(f"《越狱》第一季第一集/temp_{name}",mode="wb") as f2:

        bs = await f1.read()
        await f2.write(aes.decrypt(bs))

async def aio_dec(key):
    tasks = []
    async with aiofiles.open("《越狱》第一季第一集_second_m3u8.txt","r",encoding="utf-8") as f:
        async for line in f:
            line = line.strip()
            if line.startswith("#"):
                continue
            task = asyncio.create_task(dec_ts(line,key))
            tasks.append(task)
        
            await asyncio.wait(tasks)

def merge_ts():
    lst = []
    with open("《越狱》第一季第一集_second_m3u8.txt","r",encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                continue
            lst.append(f"《越狱》第一季第一集/temp_{line}")
    s=" ".join(lst)
    os.system(f"cat {s} > 《越狱》第一季第一集.mp4")

    
def main(url):
    # 获取iframe_src
    iframe_src = get_iframe_src(url)
    first_m3u8_url=get_first_m3u8_url(iframe_src)
    # 获取第一个m3u8_url
    iframe_domain = iframe_src.split("/share")[0]
    first_m3u8_url=iframe_domain+first_m3u8_url

    # 下载第一个m3u8_url
    download_m3u8_file(first_m3u8_url,"《越狱》第一季第一集_first_m3u8.txt")

    # 下载第二个m3u8_url
    with open("《越狱》第一季第一集_first_m3u8.txt","r",encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                continue
            second_m3u8_url=first_m3u8_url.split("index.m3u8")[0] +line
            download_m3u8_file(second_m3u8_url,"《越狱》第一季第一集_second_m3u8.txt")

    # 下载视频文件
    second_m3u8_url_up = second_m3u8_url.replace("index.m3u8","")
    # 异步协程下载视频文件
    asyncio.run(aio_download(second_m3u8_url))
    
    # 获取密钥
    key_url = second_m3u8_url_up + "key.key"
    key = get_key(key_url)
    # 解密视频文件
    asyncio.run(aio_dec(key))

    # 合并视频
    merge_ts()



if __name__ == "__main__":
    url = https://www.91kanju.com/vod-play/541-2-1.html
    main(url)