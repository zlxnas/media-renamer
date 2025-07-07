FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 仅复制app目录下的内容到容器
COPY app/ .
EXPOSE 3005
CMD ["python", "app.py"]