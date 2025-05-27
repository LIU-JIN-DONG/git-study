from bs4 import BeautifulSoup
import requests

url = "http://www.vegnet.com.cn/Sell/List_%e8%be%a3%e6%a4%92.html"
resp = requests.get(url)


page = BeautifulSoup(resp.text,'html.parser')

table = page.find("div",attrs={"class":"mid_685"})
divs = table.find_all("div",attrs={"class":"frame_list1"})
for div in divs:
    h1= div.find("h1")
    a=h1.find("a")
    name =a.text.strip()
    print(name)