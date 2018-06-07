#!/bin/bash

GROUPNAME=celery_worker
PIDPATH=/var/run
CONF=/data/conf/supervisor/supervisord.conf
USER=product
PROGRAM="/usr/bin/supervisorctl -c $CONF"




if [ ! -d $PIDPATH ]; then
    mkdir $PIDPATH
    chown $USER $PIDPATH
fi

RETVAL=0

start() {
    $PROGRAM start $GROUPNAME:*
    RETVAL=$?
}

stop() {
    $PROGRAM stop $GROUPNAME:*
    RETVAL=$?
}

restart() {
    $PROGRAM restart $GROUPNAME:*
    RETVAL=$?
}

status() {
    $PROGRAM status $GROUPNAME:*
    RETVAL=$?
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    restart
    ;;
  status)
    status
    ;;
  *)
    echo $"Usage: $0 {start|stop|status|restart}"
    exit 1
esac

exit $RETVAL
