import requests

url="https://fanyi.baidu.com/sug"

query = input("请输入要翻译的内容：")

data = {
    "kw":query
}

resp = requests.post(url,data=data)
print(resp.json())
resp.close()