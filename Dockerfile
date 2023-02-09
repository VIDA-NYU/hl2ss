FROM python:3.10-slim

WORKDIR /src
ADD requirements.multicast.txt .
RUN pip install --no-cache-dir -r requirements.multicast.txt
ENV PYTHONPATH "${PYTHONPATH}:/src"

ADD ./viewer /src

ENTRYPOINT [ "python" ]
