#!/bin/bash
export path=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:~/bin
source /etc/profile
file_path=$(dirname $0)
#script
nginx="sudo sh $file_path/nginx.sh"
dubbo="sh $file_path/dubbo.sh"



if [ $USER != "product" ];then
    echo "请切换普通用户product下执行该脚本!"
    exit 1
fi

shell_name=$(/bin/basename $0)


# app info
base_data=~/data
base_local=~/local
backup_log_dir=~/backup/logs
kill_sleep_time=40

#test
source_url="http://10.10.50.30/project"

#product

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
                project_container_dir=${base_local}/tomcat${webapp_name#webapps}
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
        msg "[error] [func:get_pkg_type] ${project_name} 应用名称存在多个目录，请检查!"
        log "[error] [func:get_pkg_type] ${project_name} 应用名称存在多个目录，请检查!"
        exit 1
    elif [ $count -eq 0 ] ; then
        msg "[error] [func:get_pkg_type] ${project_name} 应用名称错误或部署主机不存在!"
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


auto_get_project() {
    project_name_list=""
    for dir in $(ls -d ${base_data}/* | grep -P 'webapps\d*(?=[/]|$)|mods') ; do
	    if [ $(ls ${dir}|wc -l) -ne 0 ];then
		    cd ${dir}
		    for project_name in *;do
				project_name_list="${project_name};${project_name_list}"
		    done
	    fi
    done
    if [ -z "${project_name_list}" ];then
        log "[info] [func:auto_get_project] 该主机没有部署应用！"
        exit 0
    fi
}


get_project() {
    if [ -n  "$tmp_project_name" ]; then
       project_name_list=$tmp_project_name
    else
         auto_get_project
    fi
}


list() {
    get_project
    for project_name in `echo ${project_name_list}|sed 's/;/ /g'`;do
        list_project $project_name
	    echo -e "$(echo $project_infos|sed 's/^;//g'|sed 's/;/\n/g')"
	done
}

# service
service() {
    action=$1
    get_project
    for project_name in `echo ${project_name_list}|sed 's/;/ /g'`;do
        get_pkg_type
        if [ "${project_type}"x == "mod"x ];then
            # 关闭进程
            app_status=$(ps -ef |grep "Dapp=${project_name}\b" | grep -v grep)
            appids=$(ps -ef |grep "Dapp=${project_name}\b" | grep -v grep |awk '{print $2}')
            if [ "$action" == "stop" ] ; then
                if [ -n "$appids" ];then
                    [ "${project_type}"x == "mod"x ] && $dubbo $project_name disable &&  log "[info] [func:service] ${project_name} Dubbo 禁用成功......."
                    if [ $? -ne 0 ];then
                        log "[error] [func:service] ${project_name} Dubbo 禁用失败......"  &&  exit 1
                    fi
                    log "[info] [func:service] ${project_name} 正在关闭服务......"
                    for p in $appids;do
                        kill $p &>/dev/null
                        sleep $kill_sleep_time
                        #kill $p
                        if [ -d "/proc/$p" ] ; then
                            kill -9 $p
                        fi
                    done
                    log "[info] [func:service] ${project_name} 服务关闭成功......."
                else
                     log "[info] [func:service] ${project_name} 服务没有开启, 不需要关闭......"
                fi
            fi
            if [ "$action" == "start" ] ; then
                # 启动服务
                 if [ -n "$app_status" ];then
                    log "[info] [func:service] ${project_name} (pid  ${appids}) is running, 不需要重复启动......."
                 else
                    #mod_run.sh ${project_name} > /dev/null &&  log "[info] [func:service] ${project_name} 服务启动成功......."
                    modpath="$HOME/local/mods/${project_name}"
                    if [ -f "$modpath/run.sh" ]; then
                      cd $modpath
                      chmod +x run.sh
                      ./run.sh
                    fi
                    JMXIP=`/sbin/ip address|grep inet|grep -v "127.0.0.1\|inet6"|tr -s " "|awk -F '[ /]' '{print $3}'`
                    JMXPORT=$[RANDOM%1000 + 50000]
                    grep "^${project_name}" ~/.yunnex/startopts >/dev/null 2>&1 || echo "${project_name} = -Xms1024m -Xmx1024m -XX:PermSize=128M -XX:MaxPermSize=128M -XX:+HeapDumpOnOutOfMemoryError -XX:AutoBoxCacheMax=20000 -Xloggc:/dev/shm/gc-${project_name}.log -XX:+PrintGCDateStamps -XX:+PrintGCDetails -XX:+PrintGCApplicationStoppedTime -XX:+UseGCLogFileRotation -XX:NumberOfGCLogFiles=10 -XX:GCLogFileSize=1M -Djava.rmi.server.hostname=$JMXIP -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=$JMXPORT -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false" >> ~/.yunnex/startopts
                    opts_conf=`grep "^${project_name}" ~/.yunnex/startopts |awk '{print gensub(/.* =/,"","g")}'`
                    opts=`echo $opts_conf|sed -e 's/JMXHOST/'"${JMXIP}"'/' -e 's/JMXPORT/'"${JMXPORT}"'/'`
                    sed -i '/^'"${project_name}/s/JMXPORT/${JMXPORT}"'/' ~/.yunnex/startopts
                    sleep 1
                    #TODO:CD到mod目录
                    cd $modpath
                    nohup java -Dapp=${project_name} $opts -classpath '.:./*:lib/*' yunnex.saofu.core.Portal > /dev/null 2>&1 &
                    log "[info] [func:service] ${project_name} 服务启动成功......."
                  fi
            fi
            if [ "$action" == "status" ] ; then
                # 服务状态
                if [ -n "$app_status" ];then
                    log "[info] [func:service] ${project_name} (pid ${appids}) is running........."
                else
                    log "[info] [func:service] ${project_name} 没有运行......."

                fi
            fi
        elif [ "${project_type}"x == "app"x ];then
            app_status=$(ps -ef| grep java | grep "${project_container_dir}/bin/bootstrap.jar" | grep -v grep)
            appids=$(ps -ef| grep java | grep "${project_container_dir}/bin/bootstrap.jar" | grep -v grep | awk '{print $2}')
            # 关闭进程
            if [ ! -x "${project_container_dir}/bin/shutdown.sh" ];then
                log "[error] [func:service] app部署脚本${project_container_dir}/bin/shutdown.sh 不存在请检查！"
                exit 1
            fi
            if [ "$action" == "stop" ] ; then
                if [ -n "$appids" ] ; then
                    [ "${project_type}"x == "app"x ] && $nginx stop > /dev/null && log "[info] [func:service] ${project_name} Nginx关闭成功......."
                    if [ $? -ne 0 ];then
                        log "[error] [func:service] ${project_name} Nginx关闭失败......" && exit 1
                    fi
                    if [ "${project_name}" == "order-mod-facade" -o "${project_name}" == "cashier-mod-service" -o "${project_name}" == "saofu-mod-broker" -o "${project_name}" == "saofu-mod-ditui" -o "${project_name}" == "yunnex-mod-foundation" -o "${project_name}" == "mall-mod-cart" -o "${project_name}" == "open-mod-api" ];then
                        $nginx stop  && log "[info] [func:service] ${project_name} Nginx关闭成功......."
                        if [ $? -ne 0];then
                            log "[error] [func:service] ${project_name} Nginx关闭失败......" && exit 1
                        fi

                    fi
                    if [ "${project_name}" == "waimai" -o "${project_name}" == "canyin" -o "${project_name}" == "marketing" ]; then
                        $dubbo disable && log "[info] [func:service] ${project_name} Dubbo 禁用成功......."
                        if [ $? -ne 0 ];then
                            log "[error] [func:service] ${project_name} Dubbo 禁用失败......" && exit 1
                        fi
                    fi
                    log "[info] [func:service] ${project_name} 正在关闭服务进程......"
                    ${project_container_dir}/bin/shutdown.sh &> /dev/null
                    sleep $kill_sleep_time
                    for p in $appids;do
                        if [ -d "/proc/$p" ] ; then
                            kill -9 $p
                        fi
                    done
                    log "[info] [func:service] ${project_name} 服务关闭成功......."
                else
                    log "[info] [func:service] ${project_name} 服务没有开启, 不需要关闭......"
                fi
            fi
            # 启动进程
            if [ "$action" == "start" ] ; then
                if [ -n "$app_status" ];then
                    log "[info] [func:service] ${project_name} (pid ${appids}) is running, 不需要重复启动......."
                else
                    nohup ${project_container_dir}/bin/startup.sh  >/dev/null 2>&1 && log "[info] [func:service] ${project_name} 服务启动成功......."
                fi
            fi
            if [ "$action" == "status" ] ; then
                # 服务状态
                if [ -n "$app_status" ];then
                    log "[info] [func:service] ${project_name} (pid ${appids}) is running......."
                else
                    log "[error] [func:service] ${project_name} 没有运行......."
                fi
            fi
        else
            log "[error] [func:service] project_type:${project_type} 应用类型错误！"
            exit 1
        fi
    done
    unset project_name
}





if [[ $# -eq 2 ]] ; then
    project_name=$1
    action=$2
    tmp_project_name=$1
elif [[ $# -eq 1 ]]; then
    action=$1

else
    echo $"Usage: $0 {application_name|null] {start|stop|status|restart|list}"
    exit 1
fi
case $action in
    stop)
        service stop
    ;;
     start)
        service start
    ;;
    restart)
        service stop && service start
    ;;
    status)
        service status
    ;;
    list)
        list
    ;;
    *)
        echo $"Usage: $0 {application_name|null] {start|stop|status|restart|list}"
        exit 1
    ;;
esac

