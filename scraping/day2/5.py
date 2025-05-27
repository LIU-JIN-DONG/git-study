import requests
from bs4 import BeautifulSoup
import time

url = "https://www.umei.cc"
api = "/bizhitupian/shoujibizhi/"

resp =  requests.get(url+api)
resp.encoding="utf-8"

page = BeautifulSoup(resp.text,'html.parser')
divs=page.find("div",class_="item_list").find_all("div",class_="item_b")
for div in divs:
    a=div.find("a")
    href=a.get('href')

    child_resp=requests.get(url+href)
    child_resp.encoding="utf-8"
    child_page=BeautifulSoup(child_resp.text,'html.parser')
    img=child_page.find("div",class_="big-pic").find("img")
    src=img.get('src')
    # print(src)

    img_resp=requests.get(src)
    img_name=src.split("/")[-1]
    with open(f"img/{img_name}",mode="wb") as f:
        f.write(img_resp.content)
    print(f"下载完成: {img_name}")
    time.sleep(1)
print("over")