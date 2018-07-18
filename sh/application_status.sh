
#!/bin/bash
export path=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:~/bin
source /etc/profile
set -x
shell_name=$(/bin/basename $0)
wait_start_time=60
if [ $USER != "product" ];then
    echo "please use product user run"
    exit 1
fi


log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}


application_status() {
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











# application_status.sh
if [[ $# -eq 3 ]] ; then
    application_name=$1
    application_type=$2
    application_deploy_path=$3
    application_targ_dir=$(echo $application_deploy_path|sed 's#/data/#/local/#g;s#/$##g')
    application_targ_dir=$(echo ${application_targ_dir%/*})
    application_container_dir=$(echo $application_deploy_path | sed 's#/$##g;s#/data/#/local/#g;s#/webapps#/tomcat#g')
    application_container_dir=$(echo ${application_container_dir%/*})
    sleep $wait_start_time
    application_status
else
    echo $"Usage: $0 [application_name application_type application_deploy_path]"
    exit 1
fi