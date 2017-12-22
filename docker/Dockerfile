FROM python:3.6

WORKDIR /usr/src/app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -U -r requirements.txt
RUN pip install --no-cache-dir tushare

COPY . .

ENTRYPOINT ["python", "./src/program.py"]


