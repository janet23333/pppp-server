#!/bin/bash
export path=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:~/bin
set -x
shell_name=$(/bin/basename $0)


log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}

if [ $USER != "product" ];then
    log "请切换普通用户product下执行该脚本!"
    exit 1
fi




http_get_package() {
    base_version=$(echo $version|awk -F'-' '{print $1}')
    log "[info] [func:http_get_package] ${application_name} ${version} 准备下载工程包......."
    if [ ! -d ${application_deploy_path} ];then
        mkdir ${application_deploy_path} -p && log "[info] [func:http_get_package] ${application_deploy_path}目录不存在, 创建 ${application_deploy_path} 成功"
    fi
    #project_group=`curl -s ${source_url}/project_list.txt|awk -f ':' '/'"${application_name}"'/{print $1}'`
	#project_group=`curl -s ${source_url}/project_list.txt|grep -P "\b${application_name}\b"|grep -v "\-${application_name}"|grep -v "${application_name}\-"|awk -f ':' '{print $1}'`
#	project_group=`curl -s ${source_url}/project_list.txt|grep -P "\b${application_name}\b"|expand|tr -s ' '|awk -v application_name=${application_name} -F '[ :]' '{for(i=3;i<=NF;i++){if($i == application_name)print $1}}'`
#    if [ -z "project_group" ];then
#        log "[error] [[func:http_get_package]] ${source_url}/project_list.txt 中没有维护${application_name}对应组信息,请检查!"
#        exit 1
#    fi
    if [ "${application_type}"x == "web"x ];then
        project_sour_url="${source_url}/${application_name}/${version}/${application_name}-${base_version}.war"
        project_sour_url_info="${source_url}/${application_name}/${version}/${application_name}-${base_version}.war.info"
        if [ -d ${application_deploy_path}/${version} ];then
            log "[warning] [func:http_get_package] ${application_name} ${version} 已经存在......"
        else
            if [ `curl -I -s -w "%{http_code}" "${project_sour_url}" -o /dev/null` == "200" ];then
                mkdir ${application_deploy_path}/${version} -p
                cd ${application_deploy_path}/${version} && wget -q "${project_sour_url}" &&  wget -q "${project_sour_url_info}" && log "[info] [func:http_get_package] $application_name ${version} 下载包成功"
                unzip ${application_name}-${base_version}.war -d ${application_name} &> /dev/null
                if [ $? -ne 0 ];then
                    log "[error] [func:http_get_package] $application_name 包解压失败.请确认包是否损坏!"
                    exit 1
                else
                    log "[info] [func:http_get_package] $application_name ${version} 解压成功."
                fi
            else
                log "[error] [func:http_get_package] $project_sour_url 资源不存在,请检查！"
                exit 1
            fi
        fi
    elif [ "${application_type}"x == "mod"x ];then
        project_sour_url="${source_url}/${application_name}/${version}/${application_name}-${base_version}-bin.zip"
        project_sour_url_info="${source_url}/${application_name}/${version}/${application_name}-${base_version}-bin.zip.info"
        if [ -d ${application_deploy_path}/${version} ];then
            log "[warning] [func:http_get_package] ${application_name} ${version} 已经存在......"
        else
            if [ `curl -I -s -w "%{http_code}" "${project_sour_url}" -o /dev/null` == "200" ];then
                mkdir ${application_deploy_path}/${version} -p
                cd ${application_deploy_path}/${version} && wget -q "${project_sour_url}" && wget -q "${project_sour_url_info}"  && log "[info] [func:http_get_package] $application_name ${version} 下载包成功"
                unzip ${application_name}-${base_version}-bin.zip &> /dev/null
                if [ $? -ne 0 ];then
                    log "[error] [func:http_get_package] $application_name 包解压失败.请确认包是否损坏!"
                    exit 1
                else
                    log "[info] [func:http_get_package] $application_name ${version} 解压成功."
                fi
            else
                log "[error] [func:http_get_package] $project_sour_url 不存在,请检查！"
                exit 1
            fi
        fi
    else
        echo "[error] [func:http_get_package] application_type:{application_type} 应用类型错误！"
        exit 1
    fi
}




# get_package.sh
if [[ $# -eq 5 ]] ; then
    application_name=$1
    application_type=$2
    version=$3
    application_deploy_path=$4
    source_url=$5
    http_get_package
else
    echo $"Usage: $0 {application_name application_type version application_deploy_path source_url]"
    exit 1
fi






