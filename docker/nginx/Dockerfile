FROM nginx:alpine

RUN apk update
RUN apk add nodejs
RUN apk add nodejs-npm

WORKDIR /fib_view
COPY ./src /fib_view/src
COPY ./.babelrc /fib_view
COPY ./index.html /fib_view
COPY ./package.json /fib_view
COPY ./webpack.config.js /fib_view
COPY ./nginx.default.conf /etc/nginx/conf.d/default.conf

RUN npm install
RUN npm run prod

EXPOSE 8080
