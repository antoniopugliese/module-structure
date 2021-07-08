## Configuration 
If not already configured: <br>
`$ sudo su root` <br>
`$ mkdir -p /etc/redis/` <br>
`$ touch /etc/redis/6379.conf` <br>

To write to this file:<br> 
`$ cat > /etc/redis/6379.conf <<EOF`<br>
`> port              6379`<br>
`> daemonize         yes`<br>
`> save              60 1`<br>
`> bind              127.0.0.1`<br>
`> tcp-keepalive     300`<br>
`> dbfilename        dump.rdb`<br>
`> dir               ./`<br>
`> rdbcompression    yes`<br>
`> EOF`

## Server Startup
`$ redis-server /etc/redis/6379.conf`<br>
To get the command line interface:<br>
`$ redis-cli`<br>

## Server Closing
From the command line interface:<br>
`SHUTDOWN SAVE`<br>
