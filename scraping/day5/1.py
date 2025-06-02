# 下面的链接已经失效了，只是为了跟着敲一下

import requests
import re

obj = re.compile(r"url: '(?P<url>.*?)',",re.S)  
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

url="https://www.91kanju.com/vod-play/54812-1-1.html"

resp =requests.get(url,headers=headers) 
m3u8_url = obj.search(resp.text).group("url")
resp.close()

# 下载m3u8文件
resp2 = requests.get(m3u8_url,headers=headers)

with open('哲仁王后.m3u8',"wb") as f:
    f.write(resp2.content)
resp2.close()
print("m3u8文件下载完成")

# 解析m3u8文件
n=0;
with open('哲仁王后.m3u8','r',encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith("#"):
            continue
        resp3=requests.get(line)
        f=open(f"video/{n}.ts","wb")
        f.write(resp3.content)
        f.close()
        resp3.close()
        n+=1


