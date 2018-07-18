#!/bin/bash
export path=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:~/bin
source /etc/profile
set -x
shell_name=$(/bin/basename $0)

if [ $USER != "product" ];then
    echo "please use product user run"
    exit 1
fi


log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}

change_link() {
    if [ -z "${application_name}" ]; then
        log "[error] [func:change_link] application_name is not defined"
        exit 1
    fi
    if [ ! -d "${application_sour_dir}/${version}/${application_name}" ];then
        log "[info] [func:change_link] ${application_name} 指定版本的应用不存在."
        exit 1
    fi
    if [ "${application_type}"x == "mod"x ];then
        # 部署模块
        log "[info] [func:change_link] ${application_name} 为应用创建软链接......"
        log "[info] [func:change_link] 应用源目录: ${application_sour_dir}"
        [ ! -d ${application_targ_dir} ]&& mkdir -p ${application_targ_dir}
            ln -sfn ${application_sour_dir}/${version}/${application_name} ${application_targ_dir}/${application_name}
    elif [ "${application_type}"x == "web"x ];then
        # 创建应用软链
        log "[info] [func:change_link] ${application_name} 为应用创建软链接......"
        log "[info] [func:change_link] 应用源目录: ${application_sour_dir}"
        [ ! -d ${application_targ_dir} ]&& mkdir -p ${application_targ_dir}
        if [ "${application_name}" == "saofu-weixin" ];then
            ln -sfn ${application_sour_dir}/${version}/${application_name} ${application_targ_dir}/pay
        elif [ "${application_name}" == "canyin" ];then
            ln -sfn ${application_sour_dir}/${version}/${application_name} ${application_targ_dir}/ROOT
        elif [ "${application_name}" == "pos-api-gw" ];then
            ln -sfn ${application_sour_dir}/${version}/${application_name} ${application_targ_dir}/ROOT
        elif [ "${application_name}" == "advertise-web-admin" ];then
            ln -sfn ${application_sour_dir}/${version}/${application_name} ${application_targ_dir}/juyinke-web-admin
        elif [ "${application_name}" == "advertise-web-oem" ];then
            ln -sfn ${application_sour_dir}/${version}/${application_name} ${application_targ_dir}/juyinke-web-oem
		else
            ln -sfn ${application_sour_dir}/${version}/${application_name} ${application_targ_dir}/${application_name}
        fi
    else
        log "[error] [func:change_link] application_type error :${application_type}"
        exit 1
    fi
    retval=$?
    return $retval
}



# change_link.sh
if [[ $# -eq 4 ]] ; then
    application_name=$1
    application_type=$2
    version=$3
    application_deploy_path=$4
    application_targ_dir=$(echo $application_deploy_path|sed 's#/data/#/local/#g;s#/$##g')
    application_targ_dir=$(echo ${application_targ_dir%/*})
    application_sour_dir=${application_deploy_path}
    change_link || exit 1
else
    echo $"Usage: $0 [application_name application_type version application_deploy_path]"
    exit 1
fi
