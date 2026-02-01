FROM sabotagecla6/python-dev

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

RUN . /usr/bin/create-user.sh
RUN apt install -y ffmpeg 

ENTRYPOINT ["/usr/bin/entrypoint.sh"]
CMD ["vscode"]

