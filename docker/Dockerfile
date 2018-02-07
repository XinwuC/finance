FROM python:3.6

WORKDIR /usr/src/app

# TA-Lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
  tar -xvzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ./configure --prefix=/usr && \
  make && \
  make install

RUN rm -R ta-lib ta-lib-0.4.0-src.tar.gz

# pip install
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -U -r requirements.txt
RUN pip install --no-cache-dir tushare

# copy python source code
COPY . .

# ENTRYPOINT
ENTRYPOINT ["python", "./src/program.py"]


