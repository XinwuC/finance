FROM python:3.6

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN cat requirements.txt | xargs -L 1 pip install --no-cache-dir -U

COPY . .

CMD ["python", "./src/program.py"]


