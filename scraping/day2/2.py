import re
import requests
import csv


url="https://movie.douban.com/top250"
headers={
    "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}
response = requests.get(url,headers=headers)
page =  response.text

obj =  re.compile(r'<li>.*?<span class="title">(?P<name>.*?)</span>'
r'.*?<br>(?P<year>.*?)&nbsp'
r'.*?<span class="rating_num" property="v:average">(?P<score>.*?)</span>'
r'.*?<span>(?P<num>.*?)人评价</span>',re.S)
res= obj.finditer(page)
with open("douban.csv","w",newline="",encoding="utf-8") as f:
    csvwriter = csv.writer(f)
    for it in res:
        # print(it.group("name"))
        # print(it.group("year").strip())
        # print(it.group("score"))
        # print(it.group('num'))
        dic = it.groupdict()
        dic['year'] =dic['year'].strip()
        csvwriter.writerow(dic.values())

print("over")   
