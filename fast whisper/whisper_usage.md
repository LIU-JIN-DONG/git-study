# Fast Whisper 语音识别接口使用说明

这个API提供了基于Faster Whisper的语音识别功能，可以将上传的音频文件转换为文本。

## 依赖安装

确保您已安装所有必要的依赖：

```bash
pip install -r requirements.txt
```

## API端点

| 方法 | URL         | 描述                       |
| ---- | ----------- | -------------------------- |
| POST | /transcribe | 上传音频文件并返回转录结果 |

## 支持的音频格式

- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- OGG (.ogg)
- FLAC (.flac)

## 请求示例

### 使用curl上传音频文件

```bash
curl -X 'POST' \
  'http://localhost:8000/transcribe' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'audio_file=@/path/to/your/audio/file.mp3'
```

### 使用Python请求

```python
import requests

url = "http://localhost:8000/transcribe"
files = {"audio_file": open("path/to/your/audio/file.mp3", "rb")}

response = requests.post(url, files=files)
result = response.json()

print(result["text"])  # 完整转录文本
print(result["language"])  # 检测到的语言
print(result["processing_time"])  # 处理时间(秒)
```

## 响应示例

```json
{
  "text": "这是一段语音转录的示例文本。",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 3.5,
      "text": "这是一段语音转录的示例文本。",
      "words": [
        {
          "word": "这是",
          "start": 0.0,
          "end": 0.7,
          "probability": 0.95
        },
        {
          "word": "一段",
          "start": 0.8,
          "end": 1.2,
          "probability": 0.98
        },
        // ... 更多词
      ]
    }
    // ... 更多段落
  ],
  "language": "zh",
  "processing_time": 2.5
}
```

## 注意事项

1. API使用了"tiny"模型进行演示，如需更高准确度可在服务器端修改为"base"、"small"、"medium"或"large"模型
2. 目前使用CPU进行处理，处理大文件可能需要较长时间
3. 文件大小限制取决于FastAPI默认设置，通常为100MB 