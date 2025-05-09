# Fast Whisper 实时转录应用

这是一个使用Fast Whisper实现实时语音转录的Web应用，前端使用HTML、CSS和JavaScript，后端使用FastAPI。

## 功能

- 实时录音和转录
- 上传音频文件进行转录
- 显示转录历史记录
- 支持多种音频格式: MP3, WAV, M4A, OGG, FLAC

## 安装依赖

1. 确保您已安装Python 3.7+
2. 安装依赖库:

```bash
pip install -r requirements.txt
```

## 启动应用

```bash
python app.py
```

或者使用uvicorn直接启动:

```bash
uvicorn app:app --reload
```

服务器将启动在 http://localhost:8000

## 使用方法

1. 打开浏览器访问 http://localhost:8000
2. 点击"开始录音"按钮进行实时录音和转录
3. 点击"停止录音"按钮结束录音并获取转录结果
4. 或者点击"上传音频"按钮上传已有的音频文件进行转录

## API文档

启动服务器后，可以访问以下URL查看API文档:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 