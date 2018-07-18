#!/bin/bash
export path=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:~/bin

source /etc/profile
file_path=$(dirname $0)

#script
nginx="sudo sh -x $file_path/nginx.sh"
dubbo="sh -x $file_path/dubbo.sh"
cmdb_agent="sh -x $file_path/cmdb-agent.sh"
service="sh -x $file_path/service.sh"

# app info
base_data=~/data
base_local=~/local
svr_dir=~/local
backup_log_dir=~/backup/logs
kill_sleep_time=40
wait_start_time=60
shell_name=$(/bin/basename $0)

#test
source_url="http://10.10.50.30/project"

#product



if [ $USER != "product" ];then
    echo "请切换普通用户product下执行该脚本!"
    exit 1
fi








log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}





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



list_project() {
    projects=
    project_infos=
    search=$1
    for dir in $(ls -d ${base_data}/* | grep -P 'webapps\d*(?=[/]|$)|mods') ; do
	    if [ $(ls ${dir}|wc -l) -ne 0 ];then
	        cd ${dir}
	        for project_name in *;do
	            if [ -n "$search" ]; then
	                if [ "$project_name" == "$search" ];then
	                    project_name=$search
	                    flag=1
	                else
	                    continue
	                fi
	            fi
                cur_version=
	    	    if [ $project_name != "*" ];then
	    	        get_pkg_type
	    	        if [ "${project_name}"x == "saofu-weixin"x ];then
	    		         if [ -L "${project_targ_dir}/pay" ];then
	    		    	     cur_version=$(ls -l ${project_targ_dir}/pay 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
	    		          fi
	    	        elif [ "${project_name}x" == "canyin"x ];then
	    		         if [ -L "${project_targ_dir}/ROOT" ];then
	    		    	     cur_version=$(ls -l ${project_targ_dir}/ROOT 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
	    		         fi
	    	        elif [ "${project_name}x" == "pos-api-gw"x ];then
	    		         if [ -L "${project_targ_dir}/ROOT" ];then
	    		    	     cur_version=$(ls -l ${project_targ_dir}/ROOT 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
	    		         fi
	    	        elif [ "${project_name}" == "advertise-web-admin" ];then
                         if [ -L "${project_targ_dir}/juyinke-web-admin" ];then
                              cur_version=$(ls -l ${project_targ_dir}/juyinke-web-admin 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
                          fi
                    elif [ "${project_name}" == "advertise-web-oem" ];then
	    		         if [ -L "${project_targ_dir}/juyinke-web-oem" ];then
                               cur_version=$(ls -l ${project_targ_dir}/juyinke-web-oem 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
                         fi
	    	        else
	    		         if [ -L "${project_targ_dir}/${project_name}" ];then
	    		    	       cur_version=$(ls -l ${project_targ_dir}/${project_name} 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
	    		    	 fi
	    		    fi
	    		    project_infos="$project_infos;${project_name} ${cur_version:-未部署}"
	    		    projects="${project_name} ${projects}"
	            fi
	            if [ -n "$flag" ];then
	                break
	            fi
	        done
	    fi
	    if [ -n "$flag" ];then
	        unset flag
	        break
	    fi
    done

    [ -z "$projects" ]&&(log "[info] [func:list_project] 该主机未部署应用!";exit 0)

}


# 备份mod日志文件
backup_logs() {
    log "[info] [func:backup_logs] 备份${project_name}日志......."
    date=$(date +%F-%H-%M)
    if [ -z "$project_name" ];then
        log "[error] [func:backup_logs] 请指定project_name！"
        exit 1
    fi
    if [ "${project_type}"x == "app"x ];then
        if [ -d ${project_container_dir}/logs ] ; then
            cd ${project_container_dir}/logs
            [ ! -d ${backup_log_dir}/${project_name} ] && mkdir -p ${backup_log_dir}/${project_name} &>/dev/null
            [ -f ${project_name}.log ] && mv ${project_name}.log ${backup_log_dir}/${project_name}/${project_name}-${date}.log
            [ -f ${project_name}-error.log ] && mv ${project_name}-error.log ${backup_log_dir}/${project_name}/${project_name}-${date}-error.log
            log "[info] [func:backup_logs] 备份${project_name}日志完成"
        else
            log "[warning] func:backup_logs 应用日志目录 ${project_container_dir}/logs 不存在！"
        fi
    elif [ "${project_type}"x == "mod"x ];then
        if [ -d ${base_local}/mods/${project_name}/logs ] ; then
            cd ${base_local}/mods/${project_name}/logs
            [ ! -d ${backup_log_dir}/${project_name} ] && mkdir -p ${backup_log_dir}/${project_name}
            [ -f ${project_name}.log ] && mv ${project_name}.log ${backup_log_dir}/${project_name}/${project_name}-${date}.log
            [ -f ${project_name}-error.log ] && mv ${project_name}-error.log ${backup_log_dir}/${project_name}/${project_name}-${date}-error.log
            log "[info] [func:backup_logs] 备份${project_name}日志完成"
        else
            log "warning [func:backup_logs] 应用日志目录 ${base_local}/mods/${project_name}/logs  不存在！"
        fi
    else
        log "[error] func:backup_logs project_type:{project_type} 应用类型错误！"
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
		    done
	    fi
    done
    if [ -z "${project_name_list}" ];then
        log "[info] [func:auto_get_project] 该主机无${version}应用需要部署！"
    fi
}


get_project() {
       if [ -n "${tmp_project_name}" ];then
            project_name_list=${tmp_project_name}
       else
            auto_get_project
       fi
}

# 部署项目
project_deploy() {
    # 判断指定版本的应用是否存在
    if [ -z "${project_name}" ]; then
        log "[error] [func:project_deploy] project_name is not defined"
        exit 1
    fi
    if [ ! -d "${project_sour_dir}/${version}/${project_name}" ];then
        log "[info] [func:project_deploy] ${project_name} 指定版本的应用不存在."
        exit 1
    fi
    if [ "${project_type}"x == "mod"x ];then
        # 部署模块
        log "[info] [func:project_deploy] ${project_name} 为应用创建软链接......"
        log "[info] [func:project_deploy] 应用源目录: ${project_sour_dir}"
        [ ! -d ${project_targ_dir} ]&& mkdir -p ${project_targ_dir}
        /bin/rm -f ${project_targ_dir}/${project_name} && ln -sf ${project_sour_dir}/${version}/${project_name} ${project_targ_dir}/${project_name}
    elif [ "${project_type}"x == "app"x ];then
        # 创建应用软链
        log "[info] [func:project_deploy] ${project_name} 为应用创建软链接......"
        log "[info] [func:project_deploy] 应用源目录: ${project_sour_dir}"
        [ ! -d ${project_targ_dir} ]&& mkdir -p ${project_targ_dir}
        if [ "${project_name}" == "saofu-weixin" ];then
            /bin/rm -f ${project_targ_dir}/pay;ln -sf ${project_sour_dir}/${version}/${project_name} ${project_targ_dir}/pay
        elif [ "${project_name}" == "canyin" ];then
		    /bin/rm -f ${project_targ_dir}/ROOT;ln -sf ${project_sour_dir}/${version}/${project_name} ${project_targ_dir}/ROOT
        elif [ "${project_name}" == "pos-api-gw" ];then
		    /bin/rm -f ${project_targ_dir}/ROOT;ln -sf ${project_sour_dir}/${version}/${project_name} ${project_targ_dir}/ROOT
        elif [ "${project_name}" == "advertise-web-admin" ];then
            /bin/rm -f ${project_targ_dir}/juyinke-web-admin;ln -sf ${project_sour_dir}/${version}/${project_name} ${project_targ_dir}/juyinke-web-admin
        elif [ "${project_name}" == "advertise-web-oem" ];then
            /bin/rm -f ${project_targ_dir}/juyinke-web-oem;ln -sf ${project_sour_dir}/${version}/${project_name} ${project_targ_dir}/juyinke-web-oem
		else
            /bin/rm -f ${project_targ_dir}/${project_name};ln -sf ${project_sour_dir}/${version}/${project_name} ${project_targ_dir}/${project_name}
        fi
    else
        log "[error] [func:project_deploy] $project_type:{project_type} 应用类型错误！"
        exit 1
    fi
}


project_status() {
    if [ "$project_type" == "mod" ];then
        pid=$(ps -ef |grep "Dapp=${project_name}\b" |grep -v grep |awk '{print $2}')
        echo -e "\n################################### ${project_name} ##################################"
        if [ -n "$pid" ];then
            port_num=$(/usr/sbin/ss -lnpt |grep "\b$pid\b" |wc -l)
            if [ "$port_num" -gt 0 ];then
                log "[info] [func:project_status] ${project_name} 进程端口运行正常."
            else
                log "[error] [func:project_status] ${project_name} 服务无端口监听，请再次执行查看状态！"
            fi
            if [ -f ${project_targ_dir}/${project_name}/logs/${project_name}-error.log ];then
                project_err_cnt=`grep '^[0-9]\{4\}-[0-9]\{2\}' ${project_targ_dir}/${project_name}/logs/${project_name}-error.log|wc -l`
                log "[info] [func:project_status] ${project_name} 异常日志行数:  ${project_err_cnt}"
            else
                log "[warning] [func:project_status] ${project_targ_dir}/${project_name}/logs/${project_name}-error.log 不存在"
            fi
        else
            log "[error] [func:project_status] ${project_name} 服务运行异常！"
        fi
    elif [ "$project_type" == "app" ];then
        echo -e "\n################################### ${project_name} ##################################"
        pid=$(ps -ef| grep java | grep "${project_container_dir}/bin/bootstrap.jar" | grep -v grep | awk '{print $2}')
        if [ -n "$pid" ];then
            port_num=$(/usr/sbin/ss -lnpt |grep "\b$pid\b" |wc -l)
            if [ "$port_num" -gt 0 ];then
                log "[info] [func:project_status] ${project_name} 进程端口运行正常."
            else
                log "[error] [func:project_status] ${project_name} 服务无端口监听，请再次执行查看状态！"
            fi
            if [ -f ${project_container_dir}/logs/${project_name}-error.log ];then
                project_err_cnt=`grep '^[0-9]\{4\}-[0-9]\{2\}' ${project_container_dir}/logs/${project_name}-error.log|wc -l`
                log "[info] [func:project_status] ${project_name} 异常日志行数:  ${project_err_cnt}"
            else
                log "[warning] [func:project_status] ${project_container_dir}/${project_name}/logs/${project_name}-error.log 不存在"
            fi
        else
            log "[error] [func:project_status] ${project_name} 服务运行异常！"
        fi
    else
        log "[info] [func:project_status] $project_type:{project_type} 应用类型错误！"
        exit 1
    fi
}




deploy() {
    #if echo "${version}"|grep "[0-9]\{1,\}\.[0-9]\{1,\}\.[0-9]\{1,\}" > /dev/null;then
    if [ -n ${version} ] ;then
        get_project
        tmp_version=$version
        for project_name in `echo ${project_name_list}|sed 's/;/ /g'`;do
            version=$tmp_version
            get_pkg_type
            if echo ${version} | grep "^[0-9]\{6,\}$" >/dev/null ;then
                version=`curl -s  $source_url/index/${version}.index | grep "^${project_name}\ " | awk '{print $2}'`
            fi
            if [ ! -d "${project_sour_dir}/${version}/${project_name}" ];then
                log "[warning] [func:deploy] ${project_name} $version 指定版本的应用不存在."
                exit 1
            fi
            backup_logs
            $service $project_name stop || exit 1
            project_deploy || exit 1
            $service $project_name start || exit 1
            $cmdb_agent refresh
            retval=$?
            if [ $retval = 0 ];then
                log "[info] [func:deploy] ${project_name} cmdb 更新成功.............."
            else
                log "[waring] [func:deploy] ${project_name} cmdb 更新失败.............." ; exit 1
            fi
        done
        sleep $wait_start_time
        for project_name in `echo ${project_name_list}|sed 's/;/ /g'`;do
            get_pkg_type
            project_status
            list_project $project_name
            current_verison=$(echo -e "$(echo $project_infos|sed 's/^;//g'|sed 's/;/\n/g')")
            log "[info] [func:deploy] ${project_name} 当前版本: ${current_verison}"
        done
    else
        log "[error] [func:deploy] 请输入正确的版本号 [${version}]"
        exit 1
    fi

}





# deploy.sh
if [[ $# -eq 2 ]] ; then
    project_name=$1
    version=$2
    tmp_project_name=$1
    deploy
elif [[ $# -eq 1 ]]; then
    version=$1
    deploy
else
    echo $"Usage: $0 {application_name|null version]"
    exit 1
fi

