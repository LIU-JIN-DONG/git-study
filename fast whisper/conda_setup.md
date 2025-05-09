# 使用Conda设置FastAPI环境

## 初始化Conda

如果您是第一次使用conda或看到"Run 'conda init' before 'conda activate'"错误，请先运行：

```bash
conda init zsh  # 对于zsh shell
# 或
# conda init bash  # 对于bash shell
```

执行此命令后，关闭并重新打开终端，或运行以下命令使更改生效：

```bash
source ~/.zshrc  # 对于zsh shell
# 或
# source ~/.bashrc  # 对于bash shell
```

## 创建虚拟环境

```bash
conda create -n fastapi-demo python=3.10
```

## 激活环境

```bash
conda activate fastapi-demo
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
python app.py
```

## 验证安装

安装成功后，可以访问以下地址查看API文档：
- http://localhost:8000/docs
- http://localhost:8000/redoc 