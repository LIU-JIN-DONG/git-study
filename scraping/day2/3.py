import re
import requests
import csv


domain="https://www.dytt8.com"
headers={
    "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}
resp=requests.get(domain,verify=False,headers=headers)
resp.encoding = "gb2312"
page = resp.text

obj1=re.compile(r'2025新片精品.*?<ul>(?P<ul>.*?)</ul>',re.S)
obj2=re.compile(r"]<a href='(?P<href>.*?)'",re.S)
obj3=re.compile(r'译　　名　(?P<tName>.*?)(?:/|<br).*?片　　名　(?P<name>.*?)(?:/|<br).*?'
r'<font color=red>磁力链下载器：<a href="(?P<download>.*?)"',re.S)

child_herf_list=[]
res1=obj1.finditer(page)
for it in res1:
    ul = it.group("ul")
    res2 = obj2.finditer(ul)
    for itt in res2:
        child_herf= domain +itt.group('href')
        child_herf_list.append(child_herf)

f = open('dytt.csv',mode='w',encoding='utf-8')
csvwriter = csv.writer(f)
for href in child_herf_list:
    child_resp= requests.get(href,verify=False,headers=headers)
    child_resp.encoding = "gb2312"
    res3 = obj3.search(child_resp.text) 
    # print(res3.group('tName'))
    # print(res3.group('name'))
    # print(res3.group('download'))
    dic=res3.groupdict()
    csvwriter.writerow(dic.values())
f.close()
print("over")