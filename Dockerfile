FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir pandas openpyxl watchdog xlrd colorama pdfplumber

# Config folder, with all bank files setup >>
COPY conf/ .

CMD ["python", "-u", "automata.py"]