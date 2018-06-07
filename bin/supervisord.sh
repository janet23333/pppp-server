#!/bin/bash
#
# supervisord   This scripts turns supervisord on
#
# Author:       Mike McGrath <mmcgrath@redhat.com> (based off yumupdatesd)
#
# chkconfig:    3 95 04
#
# description:  supervisor is a process control utility.  It has a web based
#               xmlrpc interface as well as a few other nifty features.
# processname:  supervisord
#

# source function library
. /etc/rc.d/init.d/functions

CONF=/data/conf/supervisor/supervisord.conf

RETVAL=0

start() {
    echo -n $"Starting supervisord: "
    daemon "supervisord -c $CONF"
    RETVAL=$?
    echo
}

stop() {
    echo -n $"Stopping supervisord: "
    killproc supervisord
    echo
}

restart() {
    stop
    start
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart|force-reload|reload)
    restart
    ;;
  condrestart)
    [ -f /var/lock/subsys/supervisord ] && restart
    ;;
  status)
    status supervisord
    RETVAL=$?
    ;;
  *)
    echo $"Usage: $0 {start|stop|status|restart|reload|force-reload|condrestart}"
    exit 1
esac

exit $RETVAL
