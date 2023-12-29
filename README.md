# Simple Pentair Screenlogic Pool Controller

Flask Web Application to controller a Pentair Screenlogic System

With special thanks to the developers of [screenlogic.py](https://github.com/dieselrabbit/screenlogicpy/tree/master)


## Building and Running

Build
```
docker build --tag pool-controller --build-arg VERSION=$(head -1 version.txt | cut -d = -f 2) .
```

Run
```
docker stop pool-controller;docker rm pool-controller;docker run -d -p 5000:5000 --name pool-controller pool-controller
```

## Reverse Proxy Configuration

Configure to be behind an **nginx** reverse proxy

Update proxy configuration (default.conf)
```
# Pool CController
server {
        listen 80;
        server_name <poolcontroller>;  # FQDN of the pool controller name

        location / {
                include /etc/nginx/conf.d/proxy.conf;
                proxy_pass http://<dockerhost>:5000; # FQDN of the docker host running the container
        }

        #access_log off;
        access_log /var/log/nginx/poolcontroller.log;
        error_log  /var/log/nginx/poolcontroller.err warn;
}
```

Add a DNS entry for the pool controller pointing to the host running the **nginx** reverse proxy container

## Docker Compose Configuration

Update the **docker-compose** configuration (compose.yaml)
```
  poolcontroller:
    image: poolcontroller
    container_name: poolcontroller
    restart: always
    ports:
      - "5000:5000"
```
