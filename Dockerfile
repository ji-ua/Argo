FROM python:3

WORKDIR /home/Argo

RUN useradd -M -s /bin/false nonroot


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER nonroot

ENTRYPOINT ["python", "./argo.py", "fetch", "-q", "Fork"]