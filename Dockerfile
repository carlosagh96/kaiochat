FROM python:3.9.6-slim-buster
RUN mkdir /webapp && chmod 777 /webapp
WORKDIR /webapp
ENV DEBIAN_FRONTEND=noninteractive
COPY . .
RUN pip3 install -r requirements.txt
CMD ["python","-m","kaiochat"]
