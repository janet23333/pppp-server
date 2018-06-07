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

nginx=${NGINX-/data/svr/nginx/sbin/nginx}
prog=`/bin/basename $nginx`
conffile=${CONFFILE-/data/conf/nginx/nginx.conf}
lockfile=${LOCKFILE-/var/lock/subsys/nginx}
pidfile=${PIDFILE-/data/logs/nginx/nginx.pid}
RETVAL=0

shell_name=$(/bin/basename $0)

file_path=$(dirname $0)
#script
dubbo="sh -x $file_path/dubbo.sh"


log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}








#start the nginx
nginx_start() {
    num=$(ps -ef |grep "nginx: master"|grep -v grep|wc -l)
    if [ $num -eq 0 ]; then
        #echo -n $"Starting $prog: "
        daemon --pidfile=${pidfile} ${nginx} -c ${conffile} > /dev/null
        RETVAL=$?
        #echo
        [ $RETVAL = 0 ] && touch ${lockfile} && log "[info] [func:nginx_start] Nginx服务启动成功"
        if [ $? -ne 0 ];then
            log "[waring] [func:nginx_stop] Nginx服务关闭失败" &&  exit 1
        fi
        if `find /home/product/local/{webapps,webapps8030} -type l 2>/dev/null | xargs -i ls -l {} | awk -F'/' '{print $NF}' | egrep 'marketing$|canyin$|waimai$' >/dev/null` ;then
            su - product -c "$dubbo enable" && log "[info] [func:nginx_start] Dubbo服务启用成功"
            if [ $? -ne 0 ];then
                log "[error] [func:nginx_start] Dubbo服务启动失败." && exit 1
            fi
        fi
        return $RETVAL
    else
        log "[info] [func:nginx_start] Nginx已启动，请不要重复启动"
    fi
}

#stop the nginx
nginx_stop() {
    num=$(ps -ef |grep "nginx: master"|grep -v grep|wc -l)
    if [ $num -eq 1 ]; then
        if `find /home/product/local/{webapps,webapps8030} -type l 2>/dev/null | xargs -i ls -l {} | awk -F'/' '{print $NF}' | egrep 'marketing$|canyin$|waimai$' >/dev/null` ;then
            su - product -c "$dubbo disable" && log "[info] [func:nginx_stop] Dubbo服务关闭成功"
            if [ $? -ne 0 ];then
                log "[error] [func:nginx_stop] Dubbo服务关闭失败." && exit 1
            fi
        fi
        #echo -n $"Stopping $prog: "
        killproc -p ${pidfile} ${prog} > /dev/null
        RETVAL=$?
        #echo
        [ $RETVAL = 0 ] && rm -f ${lockfile} ${pidfile} && log "[info] [func:nginx_stop] Nginx服务关闭成功"
        if [ $? -ne 0 ];then
            log "[error] [func:nginx_stop] Dubbo服务关闭失败."  && exit 1
        fi
    else
        log "[info] [func:nginx_stop] Nginx已关闭，请不要重复关闭"
    fi
}

#-HUP:starting new worker processes with a new configuration, graceful shutdown of old worker processes
nginx_reload() {
    echo -n $"Reloading $prog: "
    killproc -p ${pidfile} ${prog} -HUP
    RETVAL=$?
    echo
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
    RETVAL=$?
    return $RETVAL
}

#give the status of nginx,stopped or running(pid)
nginx_status() {
    status -p ${pidfile} ${nginx}
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
        RETVAL=$?
        ;;
    #if the configuration file is not ok,do not restart
    restart)
        nginx_configtest -q || exit $RETVAL
        nginx_stop
        nginx_start
        ;;
    reload)
        nginx_configtest -q || exit $RETVAL
        nginx_reload
        ;;
    configtest)
        nginx_configtest
        ;;
    *)
        echo $"Usage: $prog {start|stop|restart|reload|status|help|configtest}"
        RETVAL=2
esac





