## Configuration 
If not already configured:
``$ sudo su root``
``$ mkdir -p /etc/redis/``
``$ touch /etc/redis/6379.conf``

To write to this file:
``$ cat > /etc/redis/6379.conf <<EOF``
``> port              6379``
``> daemonize         yes``
``> save              60 1``
``> bind              127.0.0.1``
``> tcp-keepalive     300``
``> dbfilename        dump.rdb``
``> dir               ./``
``> rdbcompression    yes``
``> EOF``

## Server Startup
``$ redis-server /etc/redis/6379.conf``
To get the command line interface:
``$ redis-cli``

## Server Closing
From the command line interface:
``SHUTDOWN SAVE``
