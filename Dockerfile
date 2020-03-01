FROM python:3.7-slim-stretch

LABEL maintainer="alexandre.abadie@inria.fr"

RUN apt-get update && apt-get install -y git && apt-get autoremove && apt-get autoclean
RUN apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_13.x | bash -
RUN apt-get install -y nodejs

RUN cd /opt && git clone https://github.com/aabadie/ota-server
RUN pip3 install -r /opt/ota-server/requirements.txt
RUN cd /opt/ota-server/otaserver/static && npm install && cd

ADD run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 8080

CMD ["/run.sh"]
