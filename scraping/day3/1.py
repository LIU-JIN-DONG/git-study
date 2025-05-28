import requests

url = "https://www.pearvideo.com/video_1799674" 
contId = url.split("_")[-1]

videoStatus=f"https://www.pearvideo.com/videoStatus.jsp?contId={contId}&mrd=0.6088947159947197"
headers={
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Referer":url
}

resp= requests.get(videoStatus,headers=headers)
dic = resp.json()
video_url=dic['videoInfo']['videos']['srcUrl']
systemTime=dic['systemTime']

video_url=video_url.replace(systemTime,f"cont-{contId}")
# print(video_url)

with open("video.mp4",mode="wb") as f:
    res = requests.get(video_url)
    f.write(res.content)
print("over")
 
