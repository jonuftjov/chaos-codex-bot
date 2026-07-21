FROM python:3.11-slim

WORKDIR /app

# تثبيت المتطلبات الأساسية للنظام (إذا لزم الأمر لمكتبات مثل Pillow)
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات البوت
COPY . .

# تشغيل البوت
CMD ["python", "main.py"]
