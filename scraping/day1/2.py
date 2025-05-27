import requests
query = input("请输入要搜索的内容：")
url = f"https://www.sogou.com/web?query={query}"



headers={
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}

res = requests.get(url,headers=headers)
print(res.text)
res.close()