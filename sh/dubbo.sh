#!/bin/bash
export path=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:~/bin
if [ $USER != "product" ];then
    echo "请切换普通用户product下执行该脚本!"
    exit 1
fi

# test
# doubbo service
authkey=yunnex
yunnex_admin_url='http://192.168.1.88:8020/yunnex-admin'



#product
#authkey=9kY4205CxfBo
#yunnex_admin_url='http://10.13.55.161:8010/yunnex-admin'




dubbo_app_api_url="${yunnex_admin_url}/dubbo/app/switch2"
dubbo_app_list_url="${yunnex_admin_url}/dubbo/app/list"
shell_name=$(/bin/basename $0)

file_path=$(dirname $0)
#script
nginx="sudo sh -x $file_path/nginx.sh"





log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}

get_local_ip() {
    # usage: localip=$(get_local_ip)
    if [ -n "$1" ] ; then
            interface=$1
            localip=$(/sbin/ip addr | grep -oP '10\.[0-9.]+(?=/)|192\.168\.[0-9.]+(?=/)|172\.16\.[0-9.]+(?=/)' | head -1)
    else
            localip=$(/sbin/ip addr | grep -oP '10\.[0-9.]+(?=/)|192\.168\.[0-9.]+(?=/)|172\.16\.[0-9.]+(?=/)' | head -1)
    fi
    echo $localip
}

ip=$(get_local_ip)


dubbo_disable(){
    if [ -n "${project_name}" ];then
        #response=`/usr/bin/curl -s -d "authkey="${authkey}"&action=disable&ip="${ip}"&app="${project_name}"" ${dubbo_app_api_url}`
        response=`/usr/bin/curl -s -d "authkey="${authkey}"&action=disable&ip="${ip}"" ${dubbo_app_api_url}`
    else
        response=`/usr/bin/curl -s -d "authkey="${authkey}"&action=disable&ip="${ip}"" ${dubbo_app_api_url}`
    fi
    #log "[info] [func:dubbo_enable] response: $response"
    if echo "${response}"|grep '"success":true' &>/dev/null ;then
        log "[info] [func:dubbo_disable] 模块:${project_name} dubbo服务已禁用."
    elif echo "${response}"|grep '"reason":"没有找到匹配的应用"' &> /dev/null; then
        log "[info] [func:dubbo_disable] 模块:${project_name} 未运行或无dubbo服务提供者或者模块第一次部署."
    else
        sleep 3
        response=`/usr/bin/curl -s -d "authkey="${authkey}"&action=disable&ip="${ip}"" ${dubbo_app_api_url}`
        #log "[info] [func:dubbo_enable_2] response: $response"
        if echo "${response}"|grep '"success":true' &>/dev/null ;then
            log "[info] [func:dubbo_disable_2] 模块:${project_name} dubbo服务已禁用."
        elif echo "${response}"|grep '"reason":"没有找到匹配的应用"' &> /dev/null; then
            log "[info] [func:dubbo_disable_2] 模块:${project_name} 未运行或无dubbo服务提供者或者模块第一次部署."
        else
            log "[error] [func:dubbo_disable_2] 主机:${ip} dubbo服务禁用异常，请检查!"
            log "[error] [func:dubbo_disable_2] ${response}."
            exit 1
        fi
    fi
    dubbo_disable_check
}
dubbo_enable(){
    if [ -n "${project_name}" ];then
        #response=`/usr/bin/curl -s -d "authkey="${authkey}"&action=enable&ip="${ip}"&app="${project_name}"" ${dubbo_app_api_url}`
        response=`/usr/bin/curl -s -d "authkey="${authkey}"&action=enable&ip="${ip}"" ${dubbo_app_api_url}`
    else
        response=`/usr/bin/curl -s -d "authkey="${authkey}"&action=enable&ip="${ip}"" ${dubbo_app_api_url}`
    fi
    #log "[info] [func:dubbo_enable] response: $response"
    if echo "${response}"|grep '"success":true' &>/dev/null ;then
        log "[info] [func:dubbo_enable] 模块:${project_name} dubbo服务已启用."
    elif echo "${response}"|grep '"reason":"没有找到匹配的应用"' &> /dev/null; then
        log "[info] [func:dubbo_enable] 模块:${project_name} 未运行或无dubbo服务提供者."
    else
        response=`/usr/bin/curl -s -d "authkey="${authkey}"&action=enable&ip="${ip}"" ${dubbo_app_api_url}`
        #log "[info] [func:dubbo_enable] response: $response"
        if echo "${response}"|grep '"success":true' &>/dev/null ;then
            log "[info] [func:dubbo_enable] 模块:${project_name} dubbo服务已启用."
        elif echo "${response}"|grep '"reason":"没有找到匹配的应用"' &> /dev/null; then
            log "[info] [func:dubbo_enable] 模块:${project_name} 未运行或无dubbo服务提供者."
        else
            log "[warning] [func:dubbo_enable_2] 主机:${ip} dubbo服务启用异常，请检查!"
            log "[error] [func:dubbo_enable_2] ${response}."
            exit 1
        fi
    fi
    dubbo_enable_check

}
dubbo_status(){
    response=$(/usr/bin/curl -s "${dubbo_app_list_url}?ip=${ip}&authkey=${authkey}")
    #log "[info] [func:dubbo_status] response: $response"
    if ! echo "${response}"|grep '"success":true' &>/dev/null ;then
        log "[error] [func:dubbo_status] ${dubbo_app_list_url}?ip=${ip}&authkey=${authkey}请求异常！"
        log "[error] [func:dubbo_status] ${response}."
        exit 1
    else
        echo "${response}"|grep -o '\[.*\]'|grep -o '{.*}'|sed -e 's/"//g' -e 's/,{/\n{/g'
    fi
}


enable_dubbo_nginx() {
        dubbo_enable && if [ `find /home/product/local/mods -type l 2>/dev/null| xargs -i ls -l {} | awk -F'/' '{print $NF}' \
        | egrep 'order-mod-facade$|cashier-mod-service$|saofu-mod-broker$|saofu-mod-ditui$|yunnex-mod-foundation$|mall-mod-cart$|open-mod-api$' 2>/dev/null` ];then
            $nginx start &&  log "[info] [func:enable_dubbo_nginx] 模块:${project_name} Nginx服务启动成功."
            if [ $? -ne 0 ];then
                log "[error] [func:enable_dubbo_nginx] 模块:${project_name} Nginx服务启动失败"  && exit 1
            fi
        fi || exit 1
}


dubbo_enable_check(){
    check_response=$(/usr/bin/curl -s "${dubbo_app_list_url}?ip=${ip}&authkey=${authkey}")
    if echo "${check_response}"|grep '"enable":false' &>/dev/null ;then
	    log "[error] [func:dubbo_enable_check] ${check_response}."
        exit 1
    fi
}
dubbo_disable_check(){
    check_response=$(/usr/bin/curl -s "${dubbo_app_list_url}?ip=${ip}&authkey=${authkey}")
    if echo "${check_response}"|grep '"enable":true' &>/dev/null ;then
	    log "[error] [func:dubbo_disable_check] ${check_response}."
        exit 1
    fi
}

#dubbo.sh

if [[ $# -eq 2 ]] ; then
    project_name=$1
    action=$2
elif [[ $# -eq 1 ]]; then
    action=$1
else
    echo $"Usage: $0 {application|null] {enable|disable|status}"
    exit 1
fi
case $action in
    disable)
        dubbo_disable
    ;;
    enable)
        enable_dubbo_nginx
    ;;
    status)
        dubbo_status
    ;;
    *)
        echo $"Usage: $0 {application_name|null] {enable|disable|status}"
        exit 1
    ;;
esac


