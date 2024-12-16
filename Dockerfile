# 使用官方Python运行时作为父镜像
FROM python:3.8

# 设置工作目录为/app
WORKDIR /app

# 将当前目录内容复制到位于/app中的容器中
COPY . /app

# 设置国内的pip下载源，例如使用清华大学的源
RUN pip install --upgrade pip 
  

# 安装项目依赖
RUN pip install --no-cache-dir edge-tts streamlit asyncio websockets

# 使端口7860可供外界访问
EXPOSE 5001


# 在容器启动时运行app.py
CMD ["streamlit", "run", "stream_tts.py", "--server.port=5001", "--server.address=0.0.0.0"]
