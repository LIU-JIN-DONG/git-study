import requests
from lxml import etree

url="https://movie.douban.com/top250"
headers={
    "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}
resp =  requests.get(url,headers=headers)

html = etree.HTML(resp.text)

lis=html.xpath("/html/body/div[3]/div[1]/div/div[1]/ol/li")
for li in lis:
    name= li.xpath("./div/div[2]/div[1]/a/span[1]/text()")[0]

    rating_num=li.xpath("./div/div[2]/div[2]/div/span[2]/text()")[0]
    # rating_num=li.xpath("./div/div[@class='info']/div[@class='bd']/div/span[@class='rating_num']/text()")
    
    review_people=li.xpath("./div/div[2]/div[2]/div/span[4]/text()")[0]
    print(name)
    print(rating_num)
    print(review_people)
    
