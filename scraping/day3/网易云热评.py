import requests 

from Crypto.Cipher import AES
import base64
import json
import csv
import datetime

url="https://music.163.com/weapi/comment/resource/comments/get?csrf_token="

data={
    "csrf_token":"",
    "cursor":"-1",
    "offset":"0",
    "orderType":"1",
    "pageNo":"1",
    "pageSize":"20",
    "rid":"R_SO_4_2681393627",
    "threadId":"R_SO_4_2681393627"
}

e='010001'
f='00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
g='0CoJUm6Qyw8W8jud'
i='2FB2r77Hd3G4THVi'

def get_encSecKey():
    return "003d9e616b2c6bf3236f09473d90fbaaf524d474a0837d20d71beeeec252649474785953a69abece42af66c130e5274e363520aba8feaf51a7c19ca1e846bf72f61614776ef110113da69b8d6be9f9cd27ea69e427105e41bdb0108ee110668fa365c99bf7b28a4dbe5c33528b18f03fff1a7d46b0ad18fee81fe2c87393017b"

def get_encText(data):
    first = enc_params(data,g)
    second = enc_params(first,i)
    return second

def to_16(data):
    pad = 16-len(data)%16
    data += chr(pad)*pad
    return data

def enc_params(data,key):
    iv="0102030405060708"
    data = to_16(data)
    aes = AES.new(key=key.encode("utf-8"),mode=AES.MODE_CBC,IV=iv.encode("utf-8"))
    bs=aes.encrypt(data.encode("utf-8"))
    return base64.b64encode(bs).decode("utf-8")

def timestamp_to_datetime(timestamp):
    """将毫秒时间戳转换为可读的日期时间格式"""
    if timestamp > 10000000000:  # 如果是毫秒时间戳
        timestamp = timestamp / 1000
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y年%m月%d日 %H:%M')


resp=requests.post(url,data={
    "params":get_encText(json.dumps(data)),
    "encSecKey":get_encSecKey()
})

res = json.loads(resp.text)
# print(res)

with open("网易云最新评论.csv",'w',encoding='utf-8') as f:
    writer = csv.writer(f)

    writer.writerow(['用户名','评论内容','评论时间','点赞数','评论数','ip地址'])
    
    comments = res['data']['comments']
    for comment in comments:
        name = comment['user']['nickname']
        content = comment['content']
        time = timestamp_to_datetime(comment['time'])  # 转换时间戳
        like_cnt= comment['likedCount']
        reply_cnt=comment['replyCount']
        ip = comment['ipLocation'].get('location', "未知") if comment['ipLocation'] else "未知"

        writer.writerow([name,content,time,like_cnt,reply_cnt,ip])

with open("网易云热评.csv",'w',encoding='utf-8') as f:
    writer = csv.writer(f)

    writer.writerow(['用户名','评论内容','评论时间','点赞数','评论数','ip地址'])
    
    comments = res['data']['hotComments']
    for comment in comments:
        name = comment['user']['nickname']
        content = comment['content']
        time = timestamp_to_datetime(comment['time'])  # 转换时间戳
        like_cnt= comment['likedCount']
        reply_cnt=comment['replyCount']
        ip = comment['ipLocation'].get('location', "未知") if comment['ipLocation'] else "未知"

        writer.writerow([name,content,time,like_cnt,reply_cnt,ip])
print("over")
# 加密算法
"""
# 生成随机字符串
function a(a) {
        var d, e, b = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", c = "";
        for (d = 0; a > d; d += 1)  
            e = Math.random() * b.length,
            e = Math.floor(e),
            c += b.charAt(e);
        return c
    }
    function b(a, b) {
        var c = CryptoJS.enc.Utf8.parse(b) # 加密密钥
          , d = CryptoJS.enc.Utf8.parse("0102030405060708") # 加密向量
          , e = CryptoJS.enc.Utf8.parse(a) # 加密数据
          , f = CryptoJS.AES.encrypt(e, c, { # 加密
            iv: d, # 偏移量
            mode: CryptoJS.mode.CBC # 加密模式
        });
        return f.toString() # 返回加密后的数据
    }
    function c(a, b, c) {
        var d, e;
        return setMaxDigits(131),
        d = new RSAKeyPair(b,"",c),
        e = encryptedString(d, a)
    }
    function d(d, e, f, g) {
        var h = {}
          , i = a(16); # 16位随机字符串，把他定死
        return h.encText = b(d, g), # d是数据，g是密钥
        h.encText = b(h.encText, i), # 加密后的数据，再加密一次，i是密钥
        h.encSecKey = c(i, e, f), #e，f是定死的，只要把i定死，那么key就是定死的
        h
    }
"""







