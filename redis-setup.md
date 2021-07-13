## Configuration 
If not already configured: <br>
`$ sudo su root` <br>
`$ mkdir -p /etc/redis/` <br>
`$ touch /etc/redis/6379.conf` <br>

To write to this file:
```
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
`$ redis-server /etc/redis/6379.conf`<br>
To get the command line interface:<br>
`$ redis-cli`<br>

## Server Closing
From the command line interface:<br>
`SHUTDOWN SAVE`<br>
