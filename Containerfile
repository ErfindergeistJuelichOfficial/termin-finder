FROM python:3.12-slim

# LibreOffice converts the generated workbooks to ODS.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libreoffice-calc-nogui \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY generate_calendar.py planning.py ./
COPY planungen planungen
CMD ["python", "generate_calendar.py"]
