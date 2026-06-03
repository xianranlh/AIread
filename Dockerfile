FROM python:3.12-slim

WORKDIR /srv/radar

# 基础依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 可选：本地 embedding（BGE-M3 语义去重/相关推荐）。
# 镜像会大 ~2GB；不需要可注释掉下面两行，并在 .env 设 EMBEDDING_ENABLED=false
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir sentence-transformers

COPY app ./app

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
