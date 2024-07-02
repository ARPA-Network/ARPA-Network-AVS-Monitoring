FROM python:3.8

COPY exporter.py /app/exporter.py
COPY requirements.txt /app/requirements.txt
COPY addresses.json /app/addresses.json
COPY abi /app/abi
WORKDIR /app
RUN pip install -r requirements.txt
ENV HITL_URL $HITL_URL
CMD ["python3", "/app/exporter.py"]