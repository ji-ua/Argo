FROM python:3

WORKDIR /home/Argo

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "./argo.py", "fetch", "-q", "Fork"]