# FastAPI示例应用

这是一个使用FastAPI框架创建的简单RESTful API示例。

## 功能

- 商品的增删改查操作
- 自动生成交互式API文档

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务器

```bash
python app.py
```

或者也可以使用uvicorn直接启动：

```bash
uvicorn app:app --reload
```

服务器将启动在 http://localhost:8000

## API文档

启动服务器后，可以访问以下URL查看自动生成的API文档：

- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

## API端点

| 方法   | URL              | 描述             |
| ------ | ---------------- | ---------------- |
| GET    | /                | 返回欢迎信息     |
| GET    | /items           | 获取所有商品     |
| GET    | /items/{item_id} | 获取指定ID的商品 |
| POST   | /items           | 创建新商品       |
| PUT    | /items/{item_id} | 更新指定ID的商品 |
| DELETE | /items/{item_id} | 删除指定ID的商品 |

## 示例请求

### 创建商品

```bash
curl -X 'POST' \
  'http://localhost:8000/items' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "示例商品",
  "description": "这是一个示例商品",
  "price": 99.99,
  "is_available": true
}'
```

### 获取所有商品

```bash
curl -X 'GET' \
  'http://localhost:8000/items' \
  -H 'accept: application/json'
``` 