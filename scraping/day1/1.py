from urllib.request import urlopen

url ="http://www.baidu.com"

response = urlopen(url)


with open("baidu.html","w",encoding="utf-8") as f:
    f.write(response.read().decode("utf-8"))

print("over!")

response.close()