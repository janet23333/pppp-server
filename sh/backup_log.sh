#!/bin/bash
export path=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:~/bin
source /etc/profile
set -x
#info
base_data=~/data
base_local=~/local
backup_log_dir=~/backup/logs
shell_name=$(/bin/basename $0)


log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}

# 备份日志文件
backup_log() {
    log "[info] [func:backup_logs] 备份${application_name}日志......."
    date=$(date +%F-%H-%M)
    if [ -z "$application_name" ];then
        log "[error] [func:backup_logs] 请指定application_name！"
        exit 1
    fi
    if [ "${application_type}"x == "web"x ];then
        project_container_dir=$(echo $application_deploy_path | sed 's#/$##g;s#/data/#/local/#g;s#/webapps/#/tomcat/#g;s#/$##g' )
        project_container_dir=$(echo ${project_container_dir%/*})
        if [ -d ${project_container_dir}/logs ] ; then
            cd ${project_container_dir}/logs
            [ ! -d ${backup_log_dir}/${application_name} ] && mkdir -p ${backup_log_dir}/${application_name} &>/dev/null
            [ -f ${application_name}.log ] && mv ${application_name}.log ${backup_log_dir}/${application_name}/${application_name}-${date}.log
            [ -f ${application_name}-error.log ] && mv ${application_name}-error.log ${backup_log_dir}/${application_name}/${application_name}-${date}-error.log
            log "[info] [func:backup_logs] 备份${application_name}日志完成"
        else
            log "[warning] func:backup_logs 应用日志目录 ${project_container_dir}/logs 不存在！"
        fi
    elif [ "${application_type}"x == "mod"x ];then
        if [ -d ${base_local}/mods/${application_name}/logs ] ; then
            cd ${base_local}/mods/${application_name}/logs
            [ ! -d ${backup_log_dir}/${application_name} ] && mkdir -p ${backup_log_dir}/${application_name}
            [ -f ${application_name}.log ] && mv ${application_name}.log ${backup_log_dir}/${application_name}/${application_name}-${date}.log
            [ -f ${application_name}-error.log ] && mv ${application_name}-error.log ${backup_log_dir}/${application_name}/${application_name}-${date}-error.log
            log "[info] [func:backup_logs] 备份${application_name}日志完成"
        else
            log "warning [func:backup_logs] 应用日志目录 ${base_local}/mods/${application_name}/logs  不存在！"
        fi
    else
        log "[error] func:backup_logs application_type:{application_type} 应用类型错误！"
        exit 1
    fi
}

if [ $USER != "product" ];then
    echo "please use product user run"
    exit 1
fi

# backup_log.sh
if [[ $# -eq 3 ]] ; then
    application_name=$1
    application_type=$2
    application_deploy_path=$3
    backup_log
else
    echo $"Usage: $0 [application_name application_type application_deploy_path]"
    exit 1
fi
