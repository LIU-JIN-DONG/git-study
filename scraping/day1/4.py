import requests

url="https://movie.douban.com/j/chart/top_list"

params={
    "type": 24,
    "interval_id": "100:90",
    "action": "",
    "start": 0,
    "limit": 20
}
headers={
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
 }

response = requests.get(url,params=params,headers=headers)

print(response.json())
response.close()