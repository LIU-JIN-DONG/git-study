import requests
from concurrent.futures import ThreadPoolExecutor
import csv
import os
import time
url="http://www.xinfadi.com.cn/getPriceData.html"

f=open('新发地.csv',"w",encoding="utf-8")
writer=csv.writer(f)
writer.writerow(["品名","最低价","平均价","最高价","产地","单位"])


def get_one_page(url,data):
    resp=requests.post(url=url,data=data)
    res=resp.json()
    data_list =  res["list"]
    for data in data_list:
        prodName=data["prodName"]
        lowPrice=data["lowPrice"]
        avgPrice=data["avgPrice"]
        highPrice=data["highPrice"]
        place=data["place"] if data["place"] else '未知'
        unitInfo=data["unitInfo"]
        writer.writerow([prodName,lowPrice,avgPrice,highPrice,place,unitInfo])



if __name__ == "__main__":
    # get_one_page(url=url,data={"limit":20,"current":1})
    # print("over")   
    with ThreadPoolExecutor(50) as t:
        for i in range(1,51):
            t.submit(get_one_page,url=url,data={"limit":20,"current":i})
            time.sleep(0.5)
    print("over")
            