FROM nginx:alpine

RUN apk update
RUN apk add gcc
RUN apk add musl-dev
RUN apk add nginx
RUN apk add python3
RUN apk add python3-dev
RUN python3 -m pip install --upgrade pip

WORKDIR /fibapp
COPY ./fib-app /fibapp
COPY ./fib-app/nginx.default.conf /etc/nginx/conf.d/default.conf

#RUN npm install
#RUN npm run prod
RUN python3 -m pip install -r requirements.txt
RUN nohup python3 backend/main.py &

#EXPOSE 8080
