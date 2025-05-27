import re

# list= re.findall(r"\d+","我的电话是10086，不是10010")
# print(list)


# it= re.finditer(r"\d+","我的电话是10086，不是10010")
# for i in it:
#     print(i.group())


# s= re.search(r"\d+","我的电话是10086，不是10010")
# print(s.group())

# m= re.match(r"\d+","10086，不是10010")
# print(m.group())

# obj =  re.compile(r"\d+")

# ret = obj.finditer("我的电话是10086，不是10010")
# for it in ret:
#     print(it.group())


s= """<div class='j-r-list-item1'>123</div>
<div class='j-r-list-item2'>456</div>
<div class='j-r-list-item3'>789</div>
"""

obj = re.compile(r"<div class='.*?'>(?P<nihao>.*?)</div>",re.S)

res =  obj.finditer(s)
for it in res:
    print(it.group("nihao"))

