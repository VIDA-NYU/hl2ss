FROM python:3.10-slim

RUN apt-get update -qyy && \
    apt-get install -y  python3-opencv && apt-get remove -y python3-opencv \
    && pip install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
ADD requirements.multicast.txt .
RUN pip install --no-cache-dir -r requirements.multicast.txt
ENV PYTHONPATH "${PYTHONPATH}:/src"

ADD ./viewer /src

ENTRYPOINT [ "python" ]
