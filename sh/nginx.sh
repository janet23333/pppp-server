#!/bin/sh

#Function:Start and stop openresty
#Lastmodify:2017-07-20

#SH_DIR=$(dirname $(which $0))
#. $SH_DIR/appenv.sh
# Source function library.
. /etc/rc.d/init.d/functions
#if this file is a link,get the original file as $initscript
if [ -L $0 ]; then
    initscript=`/bin/readlink -f $0`
else
    initscript=$0
fi

#get the filename
sysconfig=`/bin/basename $initscript`

if [ -f /etc/sysconfig/$sysconfig ]; then
    . /etc/sysconfig/$sysconfig
fi

set -x

nginx=${NGINX-/data/svr/nginx/sbin/nginx}
prog=`/bin/basename $nginx`
conffile=${CONFFILE-/data/conf/nginx/nginx.conf}
lockfile=${LOCKFILE-/var/lock/subsys/nginx}
pidfile=${PIDFILE-/data/logs/nginx/nginx.pid}
retval=0

shell_name=$(/bin/basename $0)

file_path=$(dirname $0)
#script
#dubbo="sh -x $file_path/dubbo.sh"


log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}








#start the nginx
nginx_start() {
    num=$(ps -ef |grep "nginx: master"|grep -v grep|wc -l)
    if [ $num -eq 0 ]; then
        daemon --pidfile=${pidfile} ${nginx} -c ${conffile} > /dev/null
        retval=$?
        [ $retval = 0 ] && touch ${lockfile} && log "[info] [func:nginx_start] Nginx服务启动成功"
        if [ $retval -ne 0 ];then
            log "[waring] [func:nginx_start] Nginx服务启动失败"  ;  exit 1
        fi
        return $retval
    else
        log "[info] [func:nginx_start] Nginx已启动，请不要重复启动"
    fi
}

#stop the nginx
nginx_stop() {
    num=$(ps -ef |grep "nginx: master"|grep -v grep|wc -l)
    if [ $num -eq 1 ]; then
        killproc -p ${pidfile} ${prog} > /dev/null
        retval=$?
        [ $retval = 0 ] && rm -f ${lockfile} ${pidfile} && log "[info] [func:nginx_stop] Nginx服务关闭成功"
        if [ $retval -ne 0 ];then
            log "[error] [func:nginx_stop] Nginx服务关闭失败" ; exit 1
        fi

    else
        log "[info] [func:nginx_stop] Nginx已关闭，请不要重复关闭"
    fi
}

#-HUP:starting new worker processes with a new configuration, graceful shutdown of old worker processes
nginx_reload() {
    echo -n $"Reloading $prog: "
    killproc -p ${pidfile} ${prog} -HUP
    retval=$?
    if [ $retval -ne 0 ];then
            log "[error] [func:nginx_reload] reload failed" ; exit 1
    fi
}

#test the configuration file is ok or not
nginx_configtest() {
    if [ "$#" -ne 0 ] ; then
        case "$1" in
            -q)
                FLAG=$1
                ;;
            *)
                ;;
        esac
        shift
    fi
    ${nginx} -t -c ${conffile} $FLAG
    retval=$?
    return $retval
}

#give the status of nginx,stopped or running(pid)
nginx_status() {
    #status -p ${pidfile} ${nginx}
    pid=$(cat $pidfile 2> /dev/null)
    kill -0 $pid 2> /dev/null
    retval=$? && [ $retval = 0 ] && echo "pid($(cat $pidfile)) is running ....."
    if [ $retval -ne 0 ];then
        log "[error] [func:nginx_status]  nginx is not running..... " ; exit 1
    fi
}



# See how we were called.
case "$1" in
    #if nginx is already running,exit
    start)
	    ulimit -c 1024000
        nginx_start

        ;;
    stop)
        nginx_stop
        ;;
    status)
        nginx_status
        retval=$?
        ;;
    #if the configuration file is not ok,do not restart
    restart)
        nginx_configtest -q || exit $retval
        nginx_stop
        nginx_start
        ;;
    reload)
        nginx_configtest -q || exit $retval
        nginx_reload
        ;;
    configtest)
        nginx_configtest
        ;;
    *)
        echo $"Usage: $prog {start|stop|restart|reload|status|help|configtest}"
        retval=2
esac





