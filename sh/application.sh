#!/bin/bash
export path=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:~/bin
source /etc/profile
set -x
file_path=$(dirname $0)
shell_name=$(/bin/basename $0)
# info
wait_pid_timeout=40
wait_start_time=60

if [ $USER != "product" ];then
    echo "please use product user run"
    exit 1
fi


log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}


wait_for_pid () {
  pid="$1"   # process ID
  i=0
  while test $i -ne $wait_pid_timeout ; do
    if test -n "$pid"; then
      if kill -0 "$pid" 2>/dev/null; then
        :
      else
        log "[info] wait (pid: $pid) close time: ${i}s ......"
        i='' &&  break
      fi
    else
        echo "args is not exits" ; return 1
    fi
    i=`expr $i + 1`
    sleep 1
    #log "[info] wait (pid: $pid) close time: ${i}s"
  done
  if test -z "$i" ; then
    return 0
  else
    return 1
  fi
}




stop() {
   if [ "$action" == "stop" ] ; then
       if [ -n "$appids" ];then
           log "[info] [func:stop] ${application_name} 正在关闭服务......"
           for p in $appids;do
               kill $p &>/dev/null
               wait_for_pid $p ; retval=$? && [ $retval = 0 ] && continue
               if [ $retval -ne 0 ]; then
                   kill -9 $p 2> /dev/null
                   wait_for_pid $p ; retval=$? && [ $retval = 0 ] && continue
                   if [ $retval -ne 0 ]; then
                        log "[error] [func:stop] ${application_name} 服务关闭失败......." ; exit 1
                   fi
               fi
           done
           log "[info] [func:stop] ${application_name} 服务关闭成功......."
       else
            log "[info] [func:stop] ${application_name} 服务没有开启, 不需要关闭......"
       fi
    fi
}



start() {
    if [ "${application_type}"x == "mod"x ];then
             if [ -n "$app_status" ];then
                log "[info] [func:start] ${application_name} (pid  ${appids}) is running, 不需要重复启动......."
             else
                #mod_run.sh ${application_name} > /dev/null &&  log "[info] [func:start] ${application_name} 服务启动成功......."
                modpath="$HOME/local/mods/${application_name}"
                if [ -f "$modpath/run.sh" ]; then
                  cd $modpath
                  chmod +x run.sh
                  ./run.sh
                fi
                JMXIP=`/sbin/ip address|grep inet|grep -v "127.0.0.1\|inet6"|tr -s " "|awk -F '[ /]' '{print $3}'`
                JMXPORT=$[RANDOM%1000 + 50000]
                grep "^${application_name}" ~/.yunnex/startopts >/dev/null 2>&1 || echo "${application_name} = -Xms1024m -Xmx1024m -XX:PermSize=128M -XX:MaxPermSize=128M -XX:+HeapDumpOnOutOfMemoryError -XX:AutoBoxCacheMax=20000 -Xloggc:/dev/shm/gc-${application_name}.log -XX:+PrintGCDateStamps -XX:+PrintGCDetails -XX:+PrintGCApplicationStoppedTime -XX:+UseGCLogFileRotation -XX:NumberOfGCLogFiles=10 -XX:GCLogFileSize=1M -Djava.rmi.server.hostname=$JMXIP -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=$JMXPORT -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false" >> ~/.yunnex/startopts
                opts=`grep "^${application_name}" ~/.yunnex/startopts |awk '{print gensub(/.* =/,"","g")}'`
                cd $modpath
                if [ -f /home/product/.yunnex/skywalking-agent/skywalking-agent.jar ];then
                    nohup java -Dapp=${application_name} $opts -Dskywalking.agent.application_code=${application_name} -javaagent:/home/product/.yunnex/skywalking-agent/skywalking-agent.jar -classpath '.:./*:lib/*' yunnex.saofu.core.Portal > /dev/null 2>&1  &
                else
                    nohup java -Dapp=${application_name} $opts -classpath '.:./*:lib/*' yunnex.saofu.core.Portal > /dev/null 2>&1  &
                fi
             fi
    elif [ "${application_type}"x == "web"x ];then
             if [ -n "$app_status" ];then
                    log "[info] [func:start] ${application_name} (pid ${appids}) is running, 不需要重复启动......."
             else
                    nohup ${application_container_dir}/bin/startup.sh > /dev/null 2>&1
             fi

    else
         log "[error] [func:start] application_type:${application_type} 应用类型错误！"
         exit 1
    fi
    application_status
}

status() {
    if [ -n "$app_status" ];then
         log "[info] [func:status] ${application_name} (pid ${appids}) is running........."
    else
         log "[info] [func:status] ${application_name} is not running......." ; exit 1
    fi
}

init_variable() {
    if [ "${application_type}"x == "mod"x ];then
        app_status=$(ps -ef |grep "Dapp=${application_name}\b" | grep -v grep)
        appids=$(ps -ef |grep "Dapp=${application_name}\b" | grep -v grep |awk '{print $2}')
    elif [ "${application_type}"x == "web"x ];then
        application_container_dir=$(echo $application_deploy_path | sed 's#/$##g;s#/data/#/local/#g;s#/webapps#/tomcat#g')
        application_container_dir=$(echo ${application_container_dir%/*})
        app_status=$(ps -ef| grep java | grep "${application_container_dir}/bin/bootstrap.jar" | grep -v grep)
        appids=$(ps -ef| grep java | grep "${application_container_dir}/bin/bootstrap.jar" | grep -v grep | awk '{print $2}')
    else
        log "[error] [func:init_variable] application_type error: ${application_type} error"
        exit 1
    fi
}



list() {
    version=$(ls -dl $link_path| awk -F'/' '{print $(NF-1)}')
    echo "application_name: $application_name $version"
}


restart() {
    stop && start
}


application_status() {
    sleep $wait_start_time
    if [ "$application_type" == "mod" ];then
        pid=$(ps -ef |grep "Dapp=${application_name}\b" |grep -v grep |awk '{print $2}')
        echo -e "\n################################### ${application_name} ##################################"
        if [ -n "$pid" ];then
            port_num=$(/usr/sbin/ss -lnpt |grep "\b$pid\b" |wc -l)
            if [ "$port_num" -gt 0 ];then
                log "[info] [func:application_status] ${application_name} 进程端口运行正常."
            else
                log "[error] [func:application_status] ${application_name} 服务无端口监听，请再次执行查看状态！" ; exit 1
            fi
            if [ -f ${project_targ_dir}/${application_name}/logs/${application_name}-error.log ];then
                project_err_cnt=`grep '^[0-9]\{4\}-[0-9]\{2\}' ${project_targ_dir}/${application_name}/logs/${application_name}-error.log|wc -l`
                log "[info] [func:application_status] ${application_name} 异常日志行数:  ${project_err_cnt}"
            else
                log "[warning] [func:application_status] ${project_targ_dir}/${application_name}/logs/${application_name}-error.log 不存在"
            fi
        else
            log "[error] [func:application_status] ${application_name} 服务运行异常！" ; exit 1
        fi
    elif [ "$application_type" == "web" ];then
        echo -e "\n################################### ${application_name} ##################################"
        pid=$(ps -ef| grep java | grep "${application_container_dir}/bin/bootstrap.jar" | grep -v grep | awk '{print $2}')
        if [ -n "$pid" ];then
            port_num=$(/usr/sbin/ss -lnpt |grep "\b$pid\b" |wc -l)
            if [ "$port_num" -gt 0 ];then
                log "[info] [func:application_status] ${application_name} 进程端口运行正常."
            else
                log "[error] [func:application_status] ${application_name} 服务无端口监听，请再次执行查看状态！" ; exit 1
            fi
            if [ -f ${application_container_dir}/logs/${application_name}-error.log ];then
                project_err_cnt=`grep '^[0-9]\{4\}-[0-9]\{2\}' ${application_container_dir}/logs/${application_name}-error.log|wc -l`
                log "[info] [func:application_status] ${application_name} 异常日志行数:  ${project_err_cnt}"
            else
                log "[warning] [func:application_status] ${application_container_dir}/logs/${application_name}-error.log 不存在"
            fi
        else
            log "[error] [func:application_status] ${application_name} 服务运行异常！" ; exit 1
        fi
    else
        log "[info] [func:application_status] application_type error :${application_type}"
        exit 1
    fi
}


if [[ $# -eq 4 ]] ; then
    application_name=$1
    application_type=$2
    application_deploy_path=$3
    action=$4
    init_variable
else
    echo $"Usage: $0 [application_name application_type application_deploy_path start|stop|status|restart|list]"
    exit 1
fi
case $action in
    stop)
        $action
    ;;
     start)
        $action
    ;;
    restart)
        $action
    ;;
    status)
        $action
    ;;
    list)
        $action
    ;;
    *)
        echo $"Usage: $0 [application_name application_type application_deploy_path start|stop|status|restart|list]"
        exit 1
    ;;
esac

