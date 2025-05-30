import requests
import asyncio
import aiohttp
import aiofiles
import json 

# 获取所有的章节id
# 'https://dushu.baidu.com/api/pc/getCatalog?data={"book_id":"4306063500"}'
# 拼接章节id 获取每一章节的内容
# 'https://dushu.baidu.com/api/pc/getChapterContent?data={"book_id":"4306063500","cid":"4306063500|1569782244","need_bookinfo":1}'

async def aiodownload(book_id,cid,title):
    data = {
        "book_id":book_id,
        "cid":f"{book_id}|{cid}",
        "need_bookinfo":1
    }
    data=json.dumps(data)
    url2 = f'https://dushu.baidu.com/api/pc/getChapterContent?data={data}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url2) as resp:
            dic = await resp.json()
            async with aiofiles.open("西游记/"+title+".txt","w",encoding="utf-8") as f:
                await f.write(dic['data']['novel']['content'])

async def get_catalog(url):
    resp=requests.get(url)
    res=resp.json()
    items = res['data']['novel']['items']
    tasks=[]
    for item in items:
        cid=item['cid']
        title=item['title']
        tasks.append(asyncio.create_task(aiodownload(book_id,cid,title)))
        # break
    
    await asyncio.wait(tasks)



if __name__ == "__main__":
    book_id = "4306063500"
    url ='https://dushu.baidu.com/api/pc/getCatalog?data={"book_id":"' + book_id + '"}'
    asyncio.run(get_catalog(url))
 