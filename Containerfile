FROM sabotagecla6/python

ENV PULSE_COOKIE=/tmp/pulse/cookie
ENV PULSE_SERVER=unix:/tmp/pulse/native

# ***********************************************
# setting for create user
# ***********************************************
ENV USER_ID=1000
ENV GROUP_ID=1000
ENV USER=ubuntu
ENV ROOT_PASSWD=ubuntu
ENV NO_PASSWD=true


RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg python3.12-venv grep

COPY ./src/ /usr/local/text2mp3/
RUN . /usr/local/text2mp3/instal-edge-tts.sh
RUN chmod a+x /usr/local/text2mp3/text2mp3.sh

CMD ["/bin/bash"]

