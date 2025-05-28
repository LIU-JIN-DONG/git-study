from lxml import etree

xml = """
<book>
    <name>Python</name>
    <author>Guido van Rossum</author>
    <author>Guido van Rossum</author>
    <author>Guido van Rossum</author>
    <year>1990</year>
</book>
"""
tree=etree.XML(xml)
author_list = tree.xpath("/book/author")
for a in author_list:
    print(a.xpath("./text()"))

