import aiohttp
import asyncio

urls=[
    "https://www.umei.cc/d/file/20230913/small447aa57416e3429b3eeb65d8590e52081694568848.jpg",
    "https://www.umei.cc/d/file/20230913/small60b099d70171783d8359a7c7507db02f1694568532.jpg",
    "https://www.umei.cc/d/file/20230913/small8efc325c03b0e6c295f5dd28eb4481d81694568457.jpg"
]

async def aiodownload(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            with open(f"{url.split('/')[-1]}","wb") as f:
                f.write(await resp.content.read())
    print(f"{url}下载完成")

async def main():
    tasks=[]
    for url in urls:
        tasks.append(asyncio.create_task(aiodownload(url)))
    
    await asyncio.wait(tasks)

if __name__ == "__main__":
    asyncio.run(main())