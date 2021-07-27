This guide assumes you already have Redis [installed](https://redis.io/topics/quickstart) on your Linux system. 
See the [Redis Documentation](https://redis.io/documentation) for more information about how to use Redis.

## Configuration 
If not already configured:
```Ubuntu
$ sudo su root
$ mkdir -p /etc/redis/
$ touch /etc/redis/6379.conf
```

To write to this file:
```Ubuntu
cat > /etc/redis/6379.conf <<EOF
port              6379
daemonize         yes
save              180 1
bind              127.0.0.1
tcp-keepalive     300
dbfilename        dump.rdb
dir               ./
rdbcompression    yes
EOF
```

## Server Startup
To start the server:
```
$ redis-server /etc/redis/6379.conf
```
To get the command line interface:
```
$ redis-cli
```

## Server Shutdown
From the command line interface:
```
$ SHUTDOWN SAVE
```