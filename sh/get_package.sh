#!/bin/bash
export path=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:~/bin

shell_name=$(/bin/basename $0)

# app info
base_data=~/data
base_local=~/local
svr_dir=~/local

#test
source_url="http://10.10.50.30/project"

#product


log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}

if [ $USER != "product" ];then
    log "请切换普通用户product下执行该脚本!"
    exit 1
fi

get_pkg_type() {
    # 判断部署类型mod|app
    if [ -z "$project_name" ];then
        log "[error] [func:get_pkg_type] 请指定project_name！"
        exit 1
    fi
    #project_type=$(ls -d ${base_data}/*/* |grep "${project_name}$")
    project_sour_list=$(ls -d ${base_data}/*/* |grep -v "grep"|grep "${project_name}$")
    count=0
    if [ -n "$project_sour_list" ] ; then
        for p in $project_sour_list ; do
            webapp_name=$(echo $p | grep -oP 'webapps\d*(?=[/]|$)')
            if [ -n "$webapp_name" ] ; then
                project_type=app
                project_targ_dir=${base_local}/$webapp_name
                project_container_dir=${svr_dir}/tomcat${webapp_name#webapps}
                project_sour_dir=$p
                let count++
            elif [[ ${p} =~ "mods" ]] ; then
                project_type=mod
                project_targ_dir=${base_local}/mods
                project_sour_dir=$p
                let count++
            fi
        done
    fi
    if [ $count -gt 1 ] ; then
        log "[error] [func:get_pkg_type] ${project_name} 应用名称存在多个目录，请检查!"
        exit 1
    elif [ $count -eq 0 ] ; then
        log "[error] [func:get_pkg_type] ${project_name} 应用名称错误或部署主机不存在!"
        exit 1
    fi
}


auto_get_project() {
    project_name_list=""
    if [ -z "$version" ];then
        log "[error] [func:auto_get_project] version不能为空"
        exit 1
    else
        base_version=${version%-*}
    fi
    for dir in $(ls -d ${base_data}/* | grep -P 'webapps\d*(?=[/]|$)|mods') ; do
	    if [ $(ls ${dir}|wc -l) -ne 0 ];then
		    cd ${dir}
		    for project_name in *;do
		        project_group=`curl -s ${source_url}/project_list.txt|grep -P "\b${project_name}\b"|expand|tr -s ' '|awk -v project_name=${project_name} -F '[ :]' '{for(i=3;i<=NF;i++){if($i == project_name)print $1}}'`
				if [ -z "$project_group" ];then
					log "[error] [[func:dis_project]] ${source_url}/project_list.txt 中没有维护${project_name}对应组信息,请检查!"
					exit 1
				fi
				if [[ -d ${dir} && ${dir} =~ "webapps" ]];then
                     if echo "${version}"|grep "^[0-9]\{6,\}$" > /dev/null;then
                          #curl  -s $source_url/index/${version}.index | grep ${project_name}
                          rversion=`curl -s  $source_url/index/${version}.index | grep "^${project_name}\ " | awk '{print $2}'`
                          rbase_version=${rversion%-*}
                          if [ ! -z $rversion ];then
                              project_sour_url="${source_url}/${project_group}/${project_name}/${rversion}/${project_name}-${rbase_version}.war"
                          fi
                     else
					     project_sour_url="${source_url}/${project_group}/${project_name}/${version}/${project_name}-${base_version}.war"
                     fi
				elif [[ -d ${dir} && ${dir} =~ "mods" ]];then
                      if echo "${version}"|grep "^[0-9]\{6,\}$" > /dev/null;then
                         #curl  -s $source_url/index/${version}.index | grep ${project_name}
                         rversion=`curl -s  $source_url/index/${version}.index | grep "^${project_name}\ " | awk '{print $2}'`
                         rbase_version=${rversion%-*}
                         if [ ! -z $rversion ];then
                             project_sour_url="${source_url}/${project_group}/${project_name}/${rversion}/${project_name}-${rbase_version}-bin.zip"
                         fi
                      else
				      	  #project_sour_url="${source_url}/${project_group}/${project_name}/${version}/${project_name}-${base_version}.war"
				      	  project_sour_url="${source_url}/${project_group}/${project_name}/${version}/${project_name}-${base_version}-bin.zip"
                      fi
				fi
				if [ `curl -i -s -w "%{http_code}" "${project_sour_url}" -o /dev/null` == "200" ];then
					project_name_list="${project_name};${project_name_list}"
				fi
			    if [ -z "${project_name_list}" ];then
                    log "[info] [func:auto_get_project] 该主机无${version}应用需要部署！"
                fi
		    done
	    fi
    done
    if [ -z "${project_name_list}" ];then
        log "[INFO] [func:auto_get_project] 该主机无${version}应用需要部署！"
    fi
}


get_project() {
       if [ -n "${tmp_project_name}" ];then
            project_name_list=${tmp_project_name}
       else
            auto_get_project
       fi
}



# 获取部署包
http_get_package() {
    #log ${project_name} ${version}
    if echo ${version} | grep "^[0-9]\{6,\}$" >/dev/null ;then
        version=`curl -s  $source_url/index/${version}.index | grep "^${project_name}\ " | awk '{print $2}'`
    fi
    log "[info] [func:http_get_package] ${project_name} ${version} 准备下载工程包......."
    #log "http_get_package:"${project_name} ${version}
    #exit
    if [ -n "${project_name}" -a -n "${version}" ];then
        base_version=${version%-*}
    else
        log "[error] [func:http_get_package] project_name and version不能为空!"
        exit 1
    fi
    if [ ! -d ${project_sour_dir} ];then
        log "[error] [func:http_get_package] ${project_sour_dir}目录不存在,请确认是否需在本机部署"
        exit 1
    fi
    #project_group=`curl -s ${source_url}/project_list.txt|awk -f ':' '/'"${project_name}"'/{print $1}'`
	#project_group=`curl -s ${source_url}/project_list.txt|grep -P "\b${project_name}\b"|grep -v "\-${project_name}"|grep -v "${project_name}\-"|awk -f ':' '{print $1}'`
	project_group=`curl -s ${source_url}/project_list.txt|grep -P "\b${project_name}\b"|expand|tr -s ' '|awk -v project_name=${project_name} -F '[ :]' '{for(i=3;i<=NF;i++){if($i == project_name)print $1}}'`
    if [ -z "project_group" ];then
        log "[error] [[func:http_get_package]] ${source_url}/project_list.txt 中没有维护${project_name}对应组信息,请检查!"
        exit 1
    fi
    if [ "${project_type}"x == "app"x ];then
        project_sour_url="${source_url}/${project_group}/${project_name}/${version}/${project_name}-${base_version}.war"
        project_sour_url_info="${source_url}/${project_group}/${project_name}/${version}/${project_name}-${base_version}.war.info"
        if [ -d ${project_sour_dir}/${version} ];then
            log "[warning] [func:http_get_package] ${project_name} ${version} 已经存在......"
        else
            if [ `curl -I -s -w "%{http_code}" "${project_sour_url}" -o /dev/null` == "200" ];then
                mkdir ${project_sour_dir}/${version}
                cd ${project_sour_dir}/${version} && wget -q "${project_sour_url}" &&  wget -q "${project_sour_url_info}" && log "[info] [func:http_get_package] $project_name ${version} 下载包成功"
                unzip ${project_name}-${base_version}.war -d ${project_name} &> /dev/null
                if [ $? -ne 0 ];then
                    log "[error] [func:http_get_package] $project_name 包解压失败.请确认包是否损坏!"
                    exit 1
                else
                    log "[info] [func:http_get_package] $project_name ${version} 解压成功."
                fi
            else
                log "[error] [func:http_get_package] $project_sour_url 资源不存在,请检查！"
                exit 1
            fi
        fi
    elif [ "${project_type}"x == "mod"x ];then
        project_sour_url="${source_url}/${project_group}/${project_name}/${version}/${project_name}-${base_version}-bin.zip"
        project_sour_url_info="${source_url}/${project_group}/${project_name}/${version}/${project_name}-${base_version}-bin.zip.info"
        if [ -d ${project_sour_dir}/${version} ];then
            log "[warning] [func:http_get_package] ${project_name} ${version} 已经存在......"
        else
            if [ `curl -I -s -w "%{http_code}" "${project_sour_url}" -o /dev/null` == "200" ];then
                mkdir ${project_sour_dir}/${version}
                cd ${project_sour_dir}/${version} && wget -q "${project_sour_url}" && wget -q "${project_sour_url_info}"  && log "[info] [func:http_get_package] $project_name ${version} 下载包成功"
                unzip ${project_name}-${base_version}-bin.zip &> /dev/null
                if [ $? -ne 0 ];then
                    log "[error] [func:http_get_package] $project_name 包解压失败.请确认包是否损坏!"
                    exit 1
                else
                    log "[info] [func:http_get_package] $project_name ${version} 解压成功."
                fi
            else
                log "[error] [func:http_get_package] $project_sour_url 不存在,请检查！"
                exit 1
            fi
        fi
    else
        echo "[error] [func:http_get_package] project_type:{project_type} 应用类型错误！"
        exit 1
    fi
}



main() {
    get_project
    tmp_version=$version
    for project_name in `echo ${project_name_list}|sed 's/;/ /g'`;do
        version=$tmp_version
        get_pkg_type
        http_get_package
    done
}

# get_package.sh
if [[ $# -eq 2 ]] ; then
    project_name=$1
    version=$2
    tmp_project_name=$1
    main
elif [[ $# -eq 1 ]]; then
    version=$1
    main
else
    echo $"Usage: $0 {application_name|null version]"
    exit 1
fi






