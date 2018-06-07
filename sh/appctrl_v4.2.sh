#!/bin/bash
# ----------------------------------
# Author:   Hushaowei
# Version:  v4.0
# Description:  应用部署及dubbo服务启用禁用


export PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:~/bin

# 基本变量
# Basic
source /etc/profile
# Shell info
SHELL_DIR=$(cd "$(dirname "$0")"; pwd)
SHELL_NAME=$(/bin/basename $0)
SHELL_LOCK_FILE="/tmp/$SHELL_NAME.lock"
SHELL_LOG="/tmp/$SHELL_NAME.log"
SHELL_PID_FILE="/tmp/${SHELL_NAME}.pid"
NGINX_SCRIPT="/data/sh/nginx.sh"
ZABBIX_SCRIPT="/data/sh/zabbix_agentd.sh"
CMDB_SCRIPT="/data/sh/cmdb-agent.sh"

# App Info
BASE_DATA=~/data
BASE_LOCAL=~/local
BACKUP_LOG_DIR=~/backup/logs
SVR_DIR=~/local

KILL_SLEEP_TIME=40



#test
#SOURCE_URL="http://10.10.50.30/project"
# doubbo service
#AUTHKEY=yunnex
#YUNNEX_ADMIN_URL='http://192.168.1.88:8020/yunnex-admin'




#product
# Package Repo
SOURCE_URL="http://10.13.29.122/project"
# Doubbo Service
AUTHKEY=9kY4205CxfBo
YUNNEX_ADMIN_URL='http://10.13.55.161:8010/yunnex-admin'
#AUTHKEY=admin
#YUNNEX_ADMIN_URL='http://10.10.50.114:8020/yunnex-admin'







DUBBO_APP_API_URL="${YUNNEX_ADMIN_URL}/dubbo/app/switch2"
DUBBO_APP_LIST_URL="${YUNNEX_ADMIN_URL}/dubbo/app/list"

 
log() {
    LOG_INFO=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $$ $SHELL_NAME: $LOG_INFO" >> $SHELL_LOG
}

msg() {
    MSG_INFO=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $$ $SHELL_NAME: $MSG_INFO"
}

# func logs 日志显示或记录到文件
logs(){
    CONSOLE=$1
    if [ "${CONSOLE}"x == "logfile"x -o "${CONSOLE}"x == "console"x -o "${CONSOLE}"x == "all"x ];then
        LEVEL=$2
        LOG_INFO=$3
        PID=`printf "%5s\n" $$`
        if [ "${CONSOLE}"x == "all"x ];then
            if [ "${LEVEL}"x == "info"x ];then
                echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $PID $SHELL_NAME: [INFO]  [func:${FUNCNAME[1]}] $LOG_INFO" | tee -a $SHELL_LOG 
            elif [ "${LEVEL}"x == "warn"x ];then
                echo -e "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $PID $SHELL_NAME: \033[33m[WARN]\033[0m  [func:${FUNCNAME[1]}] $LOG_INFO" | tee -a $SHELL_LOG 
            elif [ "${LEVEL}"x == "error"x ];then
                echo -e "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $PID $SHELL_NAME: \033[31m[ERROR]\033[0m [func:${FUNCNAME[1]}] $LOG_INFO" | tee -a $SHELL_LOG
            else
                echo "logs Usage:  logs logfile|console|all | info|warn|error \"LOG_INFO\""
            fi
        elif [ "${CONSOLE}"x == "logfile"x ];then
            if [ "${LEVEL}"x == "info"x ];then
                echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $PID $SHELL_NAME: [INFO]  [func:${FUNCNAME[1]}] $LOG_INFO" >> $SHELL_LOG
            elif [ "${LEVEL}"x == "warn"x ];then
                echo -e "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $PID $SHELL_NAME: \033[33m[WARN]\033[0m  [func:${FUNCNAME[1]}] $LOG_INFO" >> $SHELL_LOG 
            elif [ "${LEVEL}"x == "error"x ];then
                echo -e "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $PID $SHELL_NAME: \033[31m[ERROR]\033[0m [func:${FUNCNAME[1]}] $LOG_INFO" >> $SHELL_LOG
            else
                echo "logs Usage:  logs logfile|console|all | info|warn|error \"LOG_INFO\""
            fi
        elif [ "${CONSOLE}"x == "console"x ];then
            if [ "${LEVEL}"x == "info"x ];then
                echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $PID $SHELL_NAME: [INFO]  [func:${FUNCNAME[1]}] $LOG_INFO"
            elif [ "${LEVEL}"x == "warn"x ];then
                echo -e "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $PID $SHELL_NAME: \033[33m[WARN]\033[0m  [func:${FUNCNAME[1]}] $LOG_INFO" 
            elif [ "${LEVEL}"x == "error"x ];then
                echo -e "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] $PID $SHELL_NAME: \033[31m[ERROR]\033[0m [func:${FUNCNAME[1]}] $LOG_INFO"
            else
                echo "logs Usage:  logs logfile|console|all | info|warn|error \"LOG_INFO\""
            fi
        fi
    else
        echo "logs Usage:  logs logfile|console|all | info|warn|error \"LOG_INFO\""
    fi
}

shell_lock() {
    touch $SHELL_LOCK_FILE
    echo $$ > $SHELL_PID_FILE
}

shell_unlock() {
    if [ -f "$SHELL_PID_FILE" ];then
        PID=`cat $SHELL_PID_FILE`
        if [ $PID -eq $$ ] ; then
            [ -f $SHELL_LOCK_FILE ] && /bin/rm -f $SHELL_LOCK_FILE
            [ -f $SHELL_PID_FILE ] && /bin/rm -f $SHELL_PID_FILE
            exit
        fi
    fi
}

    
#退出执行unlock
#HUP(1)　　　　挂起，通常因终端掉线或用户退出而引发
#INT(2)　　　　中断，通常因按下Ctrl+C组合键而引发
#QUIT(3)　　退出，通常因按下Ctrl+组合键而引发
#ABRT(6)　　中止，通常因某些严重的执行错误而引发
#ALRM(14)　　报警，通常用来处理超时
#TERM(15)　　终止，通常在系统关机时发送
#(0)  exit
trap "shell_unlock" 0 1 2 3 6 14 15 


# 获取本机IP
#IP=$(/sbin/ifconfig eth0 |grep 'inet addr' |sed 's/.*inet addr:\([^ ]*\).*/\1/g')
get_local_ip() {
    # usage: LOCALIP=$(get_local_ip)
    if [ -n "$1" ] ; then
            interface=$1
            LOCALIP=$(/sbin/ip addr show $interface | grep -oP '10\.[0-9.]+(?=/)|192\.168\.[0-9.]+(?=/)|172\.16\.[0-9.]+(?=/)' | head -1)
    else
            LOCALIP=$(/sbin/ip addr | grep -oP '10\.[0-9.]+(?=/)|192\.168\.[0-9.]+(?=/)|172\.16\.[0-9.]+(?=/)' | head -1)
    fi
    echo $LOCALIP
}


get_pkg_type() {
    # 判断部署类型mod|app
    if [ -z "$PROJECT_NAME" ];then
	logs all error "请指定PROJECT_NAME！"
        exit 1
    fi
    #PROJECT_TYPE=$(ls -d ${BASE_DATA}/*/* |grep "${PROJECT_NAME}$")
    PROJECT_SOUR_LIST=$(ls -d ${BASE_DATA}/*/* |grep -v "grep"|grep "${PROJECT_NAME}$")
    COUNT=0
    if [ -n "$PROJECT_SOUR_LIST" ] ; then
        for p in $PROJECT_SOUR_LIST ; do
            WEBAPP_NAME=$(echo $p | grep -oP 'webapps\d*(?=[/]|$)')
            if [ -n "$WEBAPP_NAME" ] ; then
                PROJECT_TYPE=app
                PROJECT_TARG_DIR=${BASE_LOCAL}/$WEBAPP_NAME
                PROJECT_CONTAINER_DIR=${SVR_DIR}/tomcat${WEBAPP_NAME#webapps}
                PROJECT_SOUR_DIR=$p
                let COUNT++
            elif [[ ${p} =~ "mods" ]] ; then
                PROJECT_TYPE=mod
                PROJECT_TARG_DIR=${BASE_LOCAL}/mods
                PROJECT_SOUR_DIR=$p
                let COUNT++
            fi
        done
    fi
    if [ $COUNT -gt 1 ] ; then
        logs all error "应用名称存在多个目录，请检查!"
        exit 1
    elif [ $COUNT -eq 0 ] ; then
        logs all error "应用名称错误或部署主机不存在!"
        exit 1
    fi
}

# 备份mod日志文件
backup_logs() {
    logs logfile info "备份${PROJECT_NAME}日志......." 
    DATE=$(date +%F-%H-%M)
    if [ -z "$PROJECT_NAME" ];then
        logs all error "请指定PROJECT_NAME！"
        exit 1
    fi
    if [ "${PROJECT_TYPE}"x == "app"x ];then
        if [ -d ${PROJECT_CONTAINER_DIR}/logs ] ; then
            cd ${PROJECT_CONTAINER_DIR}/logs
            [ ! -d ${BACKUP_LOG_DIR}/${PROJECT_NAME} ] && mkdir -p ${BACKUP_LOG_DIR}/${PROJECT_NAME} &>/dev/null
            [ -f ${PROJECT_NAME}.log ] && mv ${PROJECT_NAME}.log ${BACKUP_LOG_DIR}/${PROJECT_NAME}/${PROJECT_NAME}-${DATE}.log
            [ -f ${PROJECT_NAME}-error.log ] && mv ${PROJECT_NAME}-error.log ${BACKUP_LOG_DIR}/${PROJECT_NAME}/${PROJECT_NAME}-${DATE}-error.log
            logs logfile info "备份${PROJECT_NAME}日志完成"
        else
            logs logfile warn "应用日志目录  ${PROJECT_CONTAINER_DIR}/logs  不存在！"
        fi
    elif [ "${PROJECT_TYPE}"x == "mod"x ];then
        if [ -d ${BASE_LOCAL}/mods/${PROJECT_NAME}/logs ] ; then
            cd ${BASE_LOCAL}/mods/${PROJECT_NAME}/logs
            [ ! -d ${BACKUP_LOG_DIR}/${PROJECT_NAME} ] && mkdir -p ${BACKUP_LOG_DIR}/${PROJECT_NAME}
            [ -f ${PROJECT_NAME}.log ] && mv ${PROJECT_NAME}.log ${BACKUP_LOG_DIR}/${PROJECT_NAME}/${PROJECT_NAME}-${DATE}.log
            [ -f ${PROJECT_NAME}-error.log ] && mv ${PROJECT_NAME}-error.log ${BACKUP_LOG_DIR}/${PROJECT_NAME}/${PROJECT_NAME}-${DATE}-error.log
            logs logfile info "备份${PROJECT_NAME}日志完成"
        else
            logs logfile warn "应用日志目录 ${BASE_LOCAL}/mods/${PROJECT_NAME}/logs  不存在！"
        fi
    else
        logs all error "PROJECT_TYPE:{PROJECT_TYPE} 应用类型错误！"
        exit 1
    fi
}


# 获取部署包
http_get_package() {
    logs logfile info "准备下载工程包......."
    #echo ${PROJECT_NAME} ${VERSION}
    if echo ${VERSION} | grep "^[0-9]\{6\}$" >/dev/null ;then 
        VERSION=`curl -s  $SOURCE_URL/index/${VERSION}.index | grep "^${PROJECT_NAME}\ " | awk '{print $2}'`
    fi
    #echo "http_get_package:"${PROJECT_NAME} ${VERSION}
    #exit
    if [ -n "${PROJECT_NAME}" -a -n "${VERSION}" ];then
        BASE_VERSION=${VERSION%-*}
    else
        logs all error "PROJECT_NAME and VERSION不能为空!"
        exit 1  
    fi
    if [ ! -d ${PROJECT_SOUR_DIR} ];then
        logs all error "${PROJECT_SOUR_DIR}目录不存在,请确认是否需在本机部署,如需部署请指定--new参数"
        exit 1
    fi
    #PROJECT_GROUP=`curl -s ${SOURCE_URL}/project_list.txt|awk -F ':' '/'"${PROJECT_NAME}"'/{print $1}'`
	#PROJECT_GROUP=`curl -s ${SOURCE_URL}/project_list.txt|grep -P "\b${PROJECT_NAME}\b"|grep -v "\-${PROJECT_NAME}"|grep -v "${PROJECT_NAME}\-"|awk -F ':' '{print $1}'`
	PROJECT_GROUP=`curl -s ${SOURCE_URL}/project_list.txt|grep -P "\b${PROJECT_NAME}\b"|expand|tr -s ' '|awk -v PROJECT_NAME=${PROJECT_NAME} -F '[ :]' '{for(i=3;i<=NF;i++){if($i == PROJECT_NAME)print $1}}'`
    if [ -z "PROJECT_GROUP" ];then
        logs all error "${SOURCE_URL}/project_list.txt 中没有维护${PROJECT_NAME}对应组信息,请检查!"
        exit 1
    fi
    if [ "${PROJECT_TYPE}"x == "app"x ];then
        PEOJECT_SOUR_URL="${SOURCE_URL}/${PROJECT_GROUP}/${PROJECT_NAME}/${VERSION}/${PROJECT_NAME}-${BASE_VERSION}.war"
        PEOJECT_SOUR_URL_INFO="${SOURCE_URL}/${PROJECT_GROUP}/${PROJECT_NAME}/${VERSION}/${PROJECT_NAME}-${BASE_VERSION}.war.info"
        if [ -d ${PROJECT_SOUR_DIR}/${VERSION} ];then
            logs all warn "${PROJECT_NAME} 版本${VERSION}已经存在,准备重启服务......"
        else
            if [ `curl -I -s -w "%{http_code}" "${PEOJECT_SOUR_URL}" -o /dev/null` == "200" ];then
                mkdir ${PROJECT_SOUR_DIR}/${VERSION}
                cd ${PROJECT_SOUR_DIR}/${VERSION} && wget -q "${PEOJECT_SOUR_URL}" &&  wget -q "${PEOJECT_SOUR_URL_INFO}"
                unzip ${PROJECT_NAME}-${BASE_VERSION}.war -d ${PROJECT_NAME} &> /dev/null
                if [ $? -ne 0 ];then
                    logs all error "$PROJECT_NAME 包解压失败.请确认包是否损坏!"
                    exit 1
                else
                    logs logfile info "$PROJECT_NAME 解压成功." 
                fi
            else
                logs all error "$PEOJECT_SOUR_URL 资源不存在,请检查！"
                exit 1
            fi
        fi
    elif [ "${PROJECT_TYPE}"x == "mod"x ];then
        PEOJECT_SOUR_URL="${SOURCE_URL}/${PROJECT_GROUP}/${PROJECT_NAME}/${VERSION}/${PROJECT_NAME}-${BASE_VERSION}-bin.zip"
        PEOJECT_SOUR_URL_INFO="${SOURCE_URL}/${PROJECT_GROUP}/${PROJECT_NAME}/${VERSION}/${PROJECT_NAME}-${BASE_VERSION}-bin.zip.info"
        if [ -d ${PROJECT_SOUR_DIR}/${VERSION} ];then
            logs all warn "${PROJECT_NAME} 版本${VERSION}已经存在,准备重启服务......"
        else
            if [ `curl -I -s -w "%{http_code}" "${PEOJECT_SOUR_URL}" -o /dev/null` == "200" ];then
                mkdir ${PROJECT_SOUR_DIR}/${VERSION}
                cd ${PROJECT_SOUR_DIR}/${VERSION} && wget -q "${PEOJECT_SOUR_URL}" && wget -q "${PEOJECT_SOUR_URL_INFO}"
                unzip ${PROJECT_NAME}-${BASE_VERSION}-bin.zip &> /dev/null
                if [ $? -ne 0 ];then
                    logs all error "$PROJECT_NAME 包解压失败.请确认包是否损坏!"
                    exit 1
                else
                    logs logfile info "$PROJECT_NAME 解压成功." 
                fi
            else
                logs all error "$PEOJECT_SOUR_URL 不存在,请检查！"
                exit 1
            fi
        fi
    else
        logs all error "PROJECT_TYPE:{PROJECT_TYPE} 应用类型错误！"
        exit 1
    fi  
}


# 部署项目
project_deploy() {
    # 判断指定版本的工程是否存在
    if [ -z "${PROJECT_NAME}" ]; then
        logs all error "PROJECT_NAME is not defined"
        exit 1
    fi
    if [ ! -d "${PROJECT_SOUR_DIR}/${VERSION}/${PROJECT_NAME}" ];then
        logs all error "${PROJECT_NAME} 指定版本的工程不存在."
        exit 1
    fi
    if [ "${PROJECT_TYPE}"x == "mod"x ];then
        # 关闭进程 
        source ~/.bash_profile
        if [ ! `which mod_run.sh` ];then
            logs all error "mod部署脚本mod_run.sh不存在请检查！"
            exit 1
        fi
        logs logfile info "${PROJECT_NAME} 正在关闭服务......"
        APPIDS=$(ps -ef |grep "Dapp=${PROJECT_NAME}\b" | grep -v grep |awk '{print $2}')
        if [ -n "$APPIDS" ];then
            for p in $APPIDS;do
                kill $p &>/dev/null
                sleep $KILL_SLEEP_TIME
                if [ -d "/proc/$p" ] ; then
                    kill -9 $p
                fi
            done
        fi

        # 部署模块
        logs logfile info "${PROJECT_NAME} 为工程创建软链接......"
        logs logfile info "工程源目录: ${PROJECT_SOUR_DIR}"
        [ ! -d ${PROJECT_TARG_DIR} ]&& mkdir -p ${PROJECT_TARG_DIR}
        /bin/rm -f ${PROJECT_TARG_DIR}/${PROJECT_NAME} && ln -sf ${PROJECT_SOUR_DIR}/${VERSION}/${PROJECT_NAME} ${PROJECT_TARG_DIR}/${PROJECT_NAME}

        # 启动服务
        logs logfile info "${PROJECT_NAME} 正在启动服务......."
        mod_run.sh ${PROJECT_NAME} > /dev/null
    elif [ "${PROJECT_TYPE}"x == "app"x ];then
        # 关闭进程
        if [ ! -x "${PROJECT_CONTAINER_DIR}/bin/shutdown.sh" ];then
            logs all error "app部署脚本${PROJECT_CONTAINER_DIR}/bin/shutdown.sh不存在请检查！"
            exit 1
        fi
        logs logfile info "${PROJECT_NAME} 正在关闭服务进程......"
        APPIDS=$(ps -ef| grep java | grep "${PROJECT_CONTAINER_DIR}/bin/bootstrap.jar" | grep -v grep | awk '{print $2}')
        if [ -n "$APPIDS" ] ; then
            ${PROJECT_CONTAINER_DIR}/bin/shutdown.sh &> /dev/null
            sleep $KILL_SLEEP_TIME
            for p in $APPIDS;do
                if [ -d "/proc/$p" ] ; then
                    kill -9 $p
                fi
            done
        fi
        # 创建工程软链
        logs logfile info "${PROJECT_NAME} 为工程创建软链接......"
        logs logfile info "工程源目录: ${PROJECT_SOUR_DIR}"
        [ ! -d ${PROJECT_TARG_DIR} ]&& mkdir -p ${PROJECT_TARG_DIR}
        if [ "${PROJECT_NAME}" == "saofu-weixin" ];then
            /bin/rm -f ${PROJECT_TARG_DIR}/pay;ln -sf ${PROJECT_SOUR_DIR}/${VERSION}/${PROJECT_NAME} ${PROJECT_TARG_DIR}/pay
        elif [ "${PROJECT_NAME}" == "canyin" ];then		
		    /bin/rm -f ${PROJECT_TARG_DIR}/ROOT;ln -sf ${PROJECT_SOUR_DIR}/${VERSION}/${PROJECT_NAME} ${PROJECT_TARG_DIR}/ROOT
        elif [ "${PROJECT_NAME}" == "pos-api-gw" ];then		
		    /bin/rm -f ${PROJECT_TARG_DIR}/ROOT;ln -sf ${PROJECT_SOUR_DIR}/${VERSION}/${PROJECT_NAME} ${PROJECT_TARG_DIR}/ROOT
        elif [ "${PROJECT_NAME}" == "advertise-web-admin" ];then
            /bin/rm -f ${PROJECT_TARG_DIR}/juyinke-web-admin;ln -sf ${PROJECT_SOUR_DIR}/${VERSION}/${PROJECT_NAME} ${PROJECT_TARG_DIR}/juyinke-web-admin
        elif [ "${PROJECT_NAME}" == "advertise-web-oem" ];then
            /bin/rm -f ${PROJECT_TARG_DIR}/juyinke-web-oem;ln -sf ${PROJECT_SOUR_DIR}/${VERSION}/${PROJECT_NAME} ${PROJECT_TARG_DIR}/juyinke-web-oem
		else
            /bin/rm -f ${PROJECT_TARG_DIR}/${PROJECT_NAME};ln -sf ${PROJECT_SOUR_DIR}/${VERSION}/${PROJECT_NAME} ${PROJECT_TARG_DIR}/${PROJECT_NAME} 
        fi 
        # 启动进程
        logs logfile info "${PROJECT_NAME} 正在启动服务......."
        nohup ${PROJECT_CONTAINER_DIR}/bin/startup.sh >/dev/null 2>&1
    else
        logs all error "$PROJECT_TYPE:{PROJECT_TYPE} 应用类型错误！"
        exit 1
    fi
}

project_status() {
    if [ "$PROJECT_TYPE" == "mod" ];then
        PID=$(ps -ef |grep "Dapp=${PROJECT_NAME}\b" |grep -v grep |awk '{print $2}')
        echo -e "###${PROJECT_NAME}"
        if [ -n "$PID" ];then
            PORT_NUM=$(ss -lnpt |grep "\b$PID\b" |wc -l)
            if [ "$PORT_NUM" -gt 0 ];then
                logs all info "${PROJECT_NAME} 进程端口运行正常."
            else
                logs all info "${PROJECT_NAME} 服务无端口监听，请再次执行查看状态！"
            fi
            if [ -f ${PROJECT_TARG_DIR}/${PROJECT_NAME}/logs/${PROJECT_NAME}-error.log ];then
                PROJECT_ERR_CNT=`grep '^[0-9]\{4\}-[0-9]\{2\}' ${PROJECT_TARG_DIR}/${PROJECT_NAME}/logs/${PROJECT_NAME}-error.log|wc -l`
                logs all info "${PROJECT_NAME} 异常日志行数:  ${PROJECT_ERR_CNT}"
            else 
                logs all info "${PROJECT_TARG_DIR}/${PROJECT_NAME}/logs/${PROJECT_NAME}-error.log 不存在"
            fi
        else
            logs all info "${PROJECT_NAME} 服务运行异常！"
        fi

    elif [ "$PROJECT_TYPE" == "app" ];then
        echo -e "###${PROJECT_NAME}"
        PID=$(ps -ef| grep java | grep "${PROJECT_CONTAINER_DIR}/bin/bootstrap.jar" | grep -v grep | awk '{print $2}')
        if [ -n "$PID" ];then
            PORT_NUM=$(ss -lnpt |grep "\b$PID\b" |wc -l)
            if [ "$PORT_NUM" -gt 0 ];then
                logs all info "${PROJECT_NAME} 进程端口运行正常."
            else
                logs all error "${PROJECT_NAME} 服务无端口监听，请再次执行查看状态！"
            fi
            if [ -f ${PROJECT_CONTAINER_DIR}/logs/${PROJECT_NAME}-error.log ];then
                PROJECT_ERR_CNT=`grep '^[0-9]\{4\}-[0-9]\{2\}' ${PROJECT_CONTAINER_DIR}/logs/${PROJECT_NAME}-error.log|wc -l`
                logs all info "${PROJECT_NAME} 异常日志行数:  ${PROJECT_ERR_CNT}"
            else 
                logs all info "${PROJECT_CONTAINER_DIR}/${PROJECT_NAME}/logs/${PROJECT_NAME}-error.log 不存在"
            fi
        else
            logs all info "${PROJECT_NAME} 服务运行异常！"
        fi
    else
        logs all info "$PROJECT_TYPE:{PROJECT_TYPE} 应用类型错误！"
        exit 1
    fi
    echo ''
}

dis_project() {
    PROJECT_DEPLOY_LIST=""
    if [ -z "$VERSION" ];then
        logs all info "VERSION不能为空"
        usage
    else
        BASE_VERSION=${VERSION%-*}
    fi
    for dir in $(ls -d ${BASE_DATA}/* | grep -P 'webapps\d*(?=[/]|$)|mods') ; do
		if [ $(ls ${dir}|wc -l) -ne 0 ];then
			cd ${dir}
			for PROJECT_NAME in *;do
                local PEOJECT_SOUR_URL=
				#PROJECT_GROUP=`curl -s ${SOURCE_URL}/project_list.txt|awk -F ':' '/'"${PROJECT_NAME}"'/{print $1}'`
				#PROJECT_GROUP=`curl -s ${SOURCE_URL}/project_list.txt|grep -P "\b${PROJECT_NAME}\b"|grep -v "\-${PROJECT_NAME}"|grep -v "${PROJECT_NAME}\-"|awk -F ':' '{print $1}'`
				PROJECT_GROUP=`curl -s ${SOURCE_URL}/project_list.txt|grep -P "\b${PROJECT_NAME}\b"|expand|tr -s ' '|awk -v PROJECT_NAME=${PROJECT_NAME} -F '[ :]' '{for(i=3;i<=NF;i++){if($i == PROJECT_NAME)print $1}}'`
				if [ -z "$PROJECT_GROUP" ];then
					logs all error "${SOURCE_URL}/project_list.txt 中没有维护${PROJECT_NAME}对应组信息,请检查!"
					exit 1
				fi
				if [[ -d ${dir} && ${dir} =~ "webapps" ]];then
                                        if echo "${VERSION}"|grep "^[0-9]\{6\}$" > /dev/null;then
                                            #curl  -s $SOURCE_URL/index/${VERSION}.index | grep ${PROJECT_NAME}  
                                            RVERSION=`curl -s  $SOURCE_URL/index/${VERSION}.index | grep "^${PROJECT_NAME}\ " | awk '{print $2}'`
                                            RBASE_VERSION=${RVERSION%-*}
                                            if [ ! -z $RVERSION ];then
                                                PEOJECT_SOUR_URL="${SOURCE_URL}/${PROJECT_GROUP}/${PROJECT_NAME}/${RVERSION}/${PROJECT_NAME}-${RBASE_VERSION}.war"
                                            fi
                                        else
					    PEOJECT_SOUR_URL="${SOURCE_URL}/${PROJECT_GROUP}/${PROJECT_NAME}/${VERSION}/${PROJECT_NAME}-${BASE_VERSION}.war"
                                        fi
				elif [[ -d ${dir} && ${dir} =~ "mods" ]];then
                                        if echo "${VERSION}"|grep "^[0-9]\{6\}$" > /dev/null;then
                                            #curl  -s $SOURCE_URL/index/${VERSION}.index | grep ${PROJECT_NAME}  
                                            RVERSION=`curl -s  $SOURCE_URL/index/${VERSION}.index | grep "^${PROJECT_NAME}\ " | awk '{print $2}'`
                                            RBASE_VERSION=${RVERSION%-*}
                                            if [ ! -z $RVERSION ];then
                                                PEOJECT_SOUR_URL="${SOURCE_URL}/${PROJECT_GROUP}/${PROJECT_NAME}/${RVERSION}/${PROJECT_NAME}-${RBASE_VERSION}-bin.zip"
                                            fi
                                        else
					    #PEOJECT_SOUR_URL="${SOURCE_URL}/${PROJECT_GROUP}/${PROJECT_NAME}/${VERSION}/${PROJECT_NAME}-${BASE_VERSION}.war"
					    PEOJECT_SOUR_URL="${SOURCE_URL}/${PROJECT_GROUP}/${PROJECT_NAME}/${VERSION}/${PROJECT_NAME}-${BASE_VERSION}-bin.zip"
                                        fi
				fi
				if [ `curl -I -s -w "%{http_code}" "${PEOJECT_SOUR_URL}" -o /dev/null` == "200" ];then
					PROJECT_DEPLOY_LIST="${PROJECT_NAME};${PROJECT_DEPLOY_LIST}"
				fi
			done
                        #echo "list:"$PROJECT_DEPLOY_LIST
		fi
    done
    if [ -z "${PROJECT_DEPLOY_LIST}" ];then
        logs all info "该主机无${VERSION}应用需要部署！"
    fi
}

list_project() {
    PROJECTS=
    PROJECT_INFOS=
    for dir in $(ls -d ${BASE_DATA}/* | grep -P 'webapps\d*(?=[/]|$)|mods') ; do
		if [ $(ls ${dir}|wc -l) -ne 0 ];then
			cd ${dir}
			for PROJECT_NAME in *;do
                CUR_VERSION=
				if [ $PROJECT_NAME != "*" ];then
					get_pkg_type
					if [ "${PROJECT_NAME}"x == "saofu-weixin"x ];then
						if [ -L "${PROJECT_TARG_DIR}/pay" ];then
							CUR_VERSION=$(ls -l ${PROJECT_TARG_DIR}/pay 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
						fi
					elif [ "${PROJECT_NAME}x" == "canyin"x ];then	
						if [ -L "${PROJECT_TARG_DIR}/ROOT" ];then
							CUR_VERSION=$(ls -l ${PROJECT_TARG_DIR}/ROOT 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
						fi                    					
					elif [ "${PROJECT_NAME}x" == "pos-api-gw"x ];then	
						if [ -L "${PROJECT_TARG_DIR}/ROOT" ];then
							CUR_VERSION=$(ls -l ${PROJECT_TARG_DIR}/ROOT 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
						fi                    					
			        elif [ "${PROJECT_NAME}" == "advertise-web-admin" ];then
                        if [ -L "${PROJECT_TARG_DIR}/juyinke-web-admin" ];then
                            CUR_VERSION=$(ls -l ${PROJECT_TARG_DIR}/juyinke-web-admin 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
                        fi
                    elif [ "${PROJECT_NAME}" == "advertise-web-oem" ];then
			            if [ -L "${PROJECT_TARG_DIR}/juyinke-web-oem" ];then
                            CUR_VERSION=$(ls -l ${PROJECT_TARG_DIR}/juyinke-web-oem 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
                        fi
					else  
						if [ -L "${PROJECT_TARG_DIR}/${PROJECT_NAME}" ];then
							CUR_VERSION=$(ls -l ${PROJECT_TARG_DIR}/${PROJECT_NAME} 2> /dev/null|awk -F '[ /]' '{print $(NF-1)}')
						fi
					fi
					PROJECT_INFOS="$PROJECT_INFOS;${PROJECT_NAME} ${CUR_VERSION:-未部署}"
					PROJECTS="${PROJECT_NAME} ${PROJECTS}"
				fi
			done
		fi
    done
    [ -z "$PROJECTS" ]&&(msg "[INFO] [func:list_project] 该主机未部署任何应用!";exit 0)
}

app() {
if [ "$1"x == "deploy"x ];then
    #if echo "${VERSION}"|grep "[0-9]\{1,\}\.[0-9]\{1,\}\.[0-9]\{1,\}" > /dev/null;then
    if echo "${VERSION}"|egrep "[0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}\-|^[0-9]{6}$" > /dev/null;then
        VERSION_TMP=${VERSION}
        if [ -n "${PROJECT_NAME}" ];then
            PROJECT_DEPLOY_LIST=${PROJECT_NAME}
        else
            dis_project
        fi
        for PROJECT_NAME in `echo ${PROJECT_DEPLOY_LIST}|sed 's/;/ /g'`;do 
            get_pkg_type
            http_get_package
	    #[ "${PROJECT_TYPE}"x == "app"x ] && zabbix stop
            [ "${PROJECT_TYPE}"x == "app"x ] && nginx stop
            [ "${PROJECT_TYPE}"x == "mod"x ] && dubbo disable
            [ "${PROJECT_NAME}" == "order-mod-facade" -o "${PROJECT_NAME}" == "cashier-mod-service" -o "${PROJECT_NAME}" == "saofu-mod-broker" -o "${PROJECT_NAME}" == "saofu-mod-ditui" -o "${PROJECT_NAME}" == "yunnex-mod-foundation" -o "${PROJECT_NAME}" == "mall-mod-cart" -o "${PROJECT_NAME}" == "open-mod-api" ] && nginx stop
            [ "${PROJECT_NAME}" == "waimai" -o "${PROJECT_NAME}" == "canyin" -o "${PROJECT_NAME}" == "marketing" ] && dubbo disable
            backup_logs
            project_deploy
            sleep 60
            project_status
            VERSION=${VERSION_TMP}
        done
        cmdb refresh
    else
        logs all error "请输入正确的版本号 [${VERSION}]"
        exit 1
    fi
    elif [ "$1"x == "list"x ];then
        list_project
        echo -e "`echo $PROJECT_INFOS|sed 's/;/\\n/g'`"
    elif [ "$1"x == "status"x ];then
        if [ -n "${PROJECT_NAME}" ];then
            get_pkg_type
            project_status
        else
            list_project
            for PROJECT_NAME in ${PROJECTS};do 
                get_pkg_type
                project_status
            done
        fi
    elif [ "$1"x == "new"x ];then
        if [[ -n "$PROJECT_NAME" && -n "$RUN_TYPE" && `echo "$RUN_TYPE" |grep -P 'webapps\d*(?=[/]|$)|mods'` ]];then
            [ ! -d $BASE_DATA/$RUN_TYPE/$PROJECT_NAME ]&&mkdir -p $BASE_DATA/$RUN_TYPE/$PROJECT_NAME
            if [ -n "$VERSION" ];then
                app deploy
            fi
        else
            logs all error "请指定部署项目及运行方式 mods|webapps|webapps8030"
            exit 1
        fi
    else
        logs all error "APP_ACTION must be <deploy|list|status|new>"
        usage
    fi
}

# zabbix_agentd.sh check #检查脚本是否存在
zabbix_check(){
    if [ ! -e ${ZABBIX_SCRIPT} ];then
        logs all warn "${ZABBIX_SCRIPT}文件不存在,请检查!"
        exit 1
    fi
}

# 关闭zabbix_agentd服务
zabbix_agentd_stop(){
    result=$(ss -lnpt |grep "*:10050\b" |wc -l)
    if [ ${result} -eq 0 ];then
        logs all info "zabbix_agentd服务已停止!"
    else
        sudo ${ZABBIX_SCRIPT} stop >/dev/null
        result=$(ss -lnpt |grep "*:10050\b" |wc -l)
        if [ ${result} -eq 0 ];then
            logs all info "zabbix_agentd服务已停止!"
        else
            logs all error "zabbxi_agentd服务停止异常,请检查!"
            exit 1
        fi
    fi
}

# 开启zabbix_agentd服务
zabbix_agentd_start(){
    result=$(ss -lnpt |grep "*:10050\b" |wc -l)
    if [ ${result} -eq 1 ];then
        logs all info "zabbix_agentd服务已启动!"
    else
        sudo ${ZABBIX_SCRIPT} start >/dev/null
        result=$(ss -lnpt |grep "*:10050\b" |wc -l)
        if [ ${result} -eq 1 ];then
            logs all info "zabbix_agentd服务已启动!"
        else
            logs all error "zabbxi_agentd服务启动异常,请检查!"
            exit 1
        fi
    fi
}

# 关闭zabbix_agentd服务
zabbix_agentd_restart(){
    sudo ${ZABBIX_SCRIPT} restart >/dev/null
    result=$(ss -lnpt |grep "*:10050\b" |wc -l)
    if [ ${result} -eq 1 ];then
        logs all info "zabbix_agentd服务已启动!"
    else
        logs all error "zabbxi_agentd服务启动异常,请检查!"
        exit 1
    fi
}

# 查看zabbix_agentd服务状态
zabbix_agentd_status(){
    sudo ${ZABBIX_SCRIPT} status 
}

# zabbxi_agentd main
zabbix(){
    IP=$(get_local_ip)
    zabbix_check
    case $1 in
        stop)
            zabbix_agentd_stop
        ;;
        start)
            zabbix_agentd_start
        ;;
        restart)
            zabbix_agentd_restart
        ;;
        status)
            zabbix_agentd_status
        ;;
        *)
            echo "Usage: `basename ${0}` --zabbix -a [stop|start|status|restart]"
            usage
        ;;
    esac
}

# nginx.sh check
nginx_check(){
    if [ ! -e ${NGINX_SCRIPT} ];then
        logs all warn "${NGINX_SCRIPT}文件不存在,请检查!"
        exit 1
    fi
}

# 开启nginx服务
nginx_start(){
    result=$(ss -lnpt |grep "*:80\b" |wc -l)
    if [ ${result} -eq 1 ];then
        logs all info "nginx服务已启动!"
    else
        sudo ${NGINX_SCRIPT} start >/dev/null
        result=$(ss -lnpt |grep "*:80\b" |wc -l)
        if [ ${result} -eq 1 ];then
            logs all info "nginx服务已启动!"
        else
            logs all error "nginx服务启动异常,请检查!"
            exit 1
        fi
    fi
}

# 停止nginx服务
nginx_stop(){
    result=$(ss -lnpt |grep "*:80\b" |wc -l)
    if [ ${result} -eq 0 ];then
        logs all info "nginx服务已停止!"
    else
        sudo ${NGINX_SCRIPT} stop >/dev/null
        result=$(ss -lnpt |grep "*:80\b" |wc -l)
        if [ ${result} -eq 0 ];then
            logs all info "nginx服务已停止!"
        else
            logs all error "nginx服务停止异常,请检查!"
            exit 1
        fi
    fi
}

# 查看nginx状态
nginx_status(){
    sudo ${NGINX_SCRIPT} status >/dev/null
    result=$(ss -lnpt |grep "*:80\b" |wc -l)
    if [ ${result} -eq 1 ];then
        logs all info "nginx服务80端口监听正常!"
    else
        logs all info "nginx服务停止状态!"
    fi
}

# reload nginx
nginx_reload(){
    sudo ${NGINX_SCRIPT} reload
    logs all info  "nginx服务reload完成!"
}

# restart nginx
nginx_restart(){
    sudo ${NGINX_SCRIPT} restart
    logs all info "nginx服务restart完成!"
}

# configtest nginx
nginx_configtest(){
    sudo ${NGINX_SCRIPT} configtest
}

# nginx main
nginx(){
    IP=$(get_local_ip)
    nginx_check
    case $1 in 
        start)
            nginx_start
        ;;
        stop)
            nginx_stop
        ;;
        status)
            nginx_status
        ;;
        reload)
            nginx_reload
        ;;
        restart)
            nginx_restart
        ;;
        configtest)
            nginx_configtest
        ;;
        *)
            echo "Usage: `basename ${0}` --nginx -a [start|stop|status|reload|restart|configtest]"
            usage
        ;;
    esac
}

# cmdb-agent.sh check 
cmdb_check() {
    if [ ! -e ${CMDB_SCRIPT} ];then
        logs all warn "${CMDB_SCRIPT}文件不存在,请检查!"
        #exit 1
    fi
}

#cmdb-agent stop
cmdb_agent_stop(){
    result=$(ps -ef | grep cmdb-agent.py | grep -v grep | wc -l)
    if [ ${result} -eq 0 ];then
        logs all info "cmdb-agent服务已停止!"
    else
        /bin/bash ${CMDB_SCRIPT} stop       
        result=$(ps -ef | grep cmdb-agent.py | grep -v grep | wc -l)
        if [ ${result} -eq 0 ];then
            logs all info "cmdb-agent服务已停止!"
        else
            logs all error "cmdb-agent停止异常,请检查!"
        fi
    fi
}

#cmdb-agent start
cmdb_agent_start(){
    result=$(ps -ef | grep cmdb-agent.py | grep -v grep | wc -l)
    if [ ${result} -eq 1 ];then
        logs all info "cmdb-agent服务已启动!"
    else
        /bin/bash ${CMDB_SCRIPT} start 2>/dev/null
        result=$(ps -ef | grep cmdb-agent.py | grep -v grep | wc -l)
        if [ ${result} -eq 1 ];then
            logs all info "cmdb-agent服务已启动!"
        else
            logs all error "cmdb-agent服务启动异常,请检查!"
        fi
    fi
}

#cmdb-agent restart
cmdb_agent_restart(){
    /bin/bash ${CMDB_SCRIPT} restart
    result=$(ps -ef | grep cmdb-agent.py | grep -v grep | wc -l)
    if [ ${result} -eq 1 ];then
        logs all info "cmdb-agent重启完成!"
    else
        logs all error "cmdb-agent重启异常,请检查!"
    fi
}

#cmdb-agent status
cmdb_agent_status(){
    /bin/bash ${CMDB_SCRIPT} status
}

#cmdb-agent refresh
cmdb_agent_refresh() {
    /bin/bash ${CMDB_SCRIPT} refresh >/dev/null
    cmd_status=$?
    #result=$(ps -ef | grep cmdb-agent.py | grep -v grep | wc -l)
    #if [ ${result} -ge 1 ];then
    if [ $cmd_status -eq 0 ];then
        logs all info "cmdb-agent服务refresh完成!"
    else
        logs all error "cmdb-agent服务refresh异常,请检查!"
    fi
}


#cmdb-agent main
cmdb(){
    IP=$(get_local_ip)
    cmdb_check
    case $1 in
        start)
            cmdb_agent_start
        ;;
        stop)
            cmdb_agent_stop
        ;;
        status)
            cmdb_agent_status
        ;;
        refresh)
            cmdb_agent_refresh
        ;;
        restart)
            cmdb_agent_restart
        ;;
        *)
            echo "Usage: `basename ${0}` --cmdb -a [start|stop|status|refresh|restart]"
            usage
        ;;
    esac
}

dubbo_disable(){
    if [ -n "${PROJECT_NAME}" ];then
        #RESPONSE=`/usr/bin/curl -s -d "authkey="${AUTHKEY}"&action=disable&ip="${IP}"&app="${PROJECT_NAME}"" ${DUBBO_APP_API_URL}`
        RESPONSE=`/usr/bin/curl -s -d "authkey="${AUTHKEY}"&action=disable&ip="${IP}"" ${DUBBO_APP_API_URL}`
    else
        RESPONSE=`/usr/bin/curl -s -d "authkey="${AUTHKEY}"&action=disable&ip="${IP}"" ${DUBBO_APP_API_URL}`
    fi
    logs logfile info "RESPONSE:${RESPONSE}" 
    if echo "${RESPONSE}"|grep '"success":true' &>/dev/null ;then
        logs all info "模块:${PROJECT_NAME} Dubbo服务已禁用."
    elif echo "${RESPONSE}"|grep '"reason":"没有找到匹配的应用"' &> /dev/null; then
        logs all info "模块:${PROJECT_NAME} 未运行或无dubbo服务提供者."
    else
        sleep 3
        RESPONSE=`/usr/bin/curl -s -d "authkey="${AUTHKEY}"&action=disable&ip="${IP}"" ${DUBBO_APP_API_URL}`
        if echo "${RESPONSE}"|grep '"success":true' &>/dev/null ;then
            logs all info "模块:${PROJECT_NAME} Dubbo服务已禁用."
        elif echo "${RESPONSE}"|grep '"reason":"没有找到匹配的应用"' &> /dev/null; then
            logs all info "模块:${PROJECT_NAME} 未运行或无dubbo服务提供者."
        else
            logs all info "Dubbo服务禁用异常，请检查!"
            logs logfile error "RESPONSE:${RESPONSE}."
            exit 1
        fi
    fi
    dubbo_disable_check
}
dubbo_enable(){
    if [ -n "${PROJECT_NAME}" ];then
        #RESPONSE=`/usr/bin/curl -s -d "authkey="${AUTHKEY}"&action=enable&ip="${IP}"&app="${PROJECT_NAME}"" ${DUBBO_APP_API_URL}`
        RESPONSE=`/usr/bin/curl -s -d "authkey="${AUTHKEY}"&action=enable&ip="${IP}"" ${DUBBO_APP_API_URL}`
    else
        RESPONSE=`/usr/bin/curl -s -d "authkey="${AUTHKEY}"&action=enable&ip="${IP}"" ${DUBBO_APP_API_URL}`
    fi
    logs logfile info "RESPONSE:${RESPONSE}" 
    if echo "${RESPONSE}"|grep '"success":true' &>/dev/null ;then
        logs all info "模块:${PROJECT_NAME} Dubbo服务已启用."
    elif echo "${RESPONSE}"|grep '"reason":"没有找到匹配的应用"' &> /dev/null; then
        logs all info "模块:${PROJECT_NAME} 未运行或无dubbo服务提供者."
    else
        sleep 3
        RESPONSE=`/usr/bin/curl -s -d "authkey="${AUTHKEY}"&action=enable&ip="${IP}"" ${DUBBO_APP_API_URL}`
        if echo "${RESPONSE}"|grep '"success":true' &>/dev/null ;then
            logs all info "模块:${PROJECT_NAME} Dubbo服务已启用."
        elif echo "${RESPONSE}"|grep '"reason":"没有找到匹配的应用"' &> /dev/null; then
            logs all info "模块:${PROJECT_NAME} 未运行或无dubbo服务提供者."
        else
            logs all error "主机:${IP} Dubbo服务启用异常，请检查!"
            logs logfile error "RESPONSE:${RESPONSE}."
            exit 1
        fi
    fi
    dubbo_enable_check
}

dubbo_enable_check(){
    CHECK_RESPONSE=$(/usr/bin/curl -s "${DUBBO_APP_LIST_URL}?ip=${IP}&authkey=${AUTHKEY}")
    logs logfile info "CHECK_RESPONSE:${CHECK_RESPONSE}" 
    if echo "${CHECK_RESPONSE}"|grep '"enable":false' &>/dev/null ;then
        logs all error "主机:${IP} Dubbo服务启用异常，请检查!"
	    logs logfile error "CHECK_RESPONSE:${CHECK_RESPONSE}.\n"
        exit 1
    fi
}
dubbo_disable_check(){
    CHECK_RESPONSE=$(/usr/bin/curl -s "${DUBBO_APP_LIST_URL}?ip=${IP}&authkey=${AUTHKEY}")
    logs logfile info "CHECK_RESPONSE:${CHECK_RESPONSE}" 
    if echo "${CHECK_RESPONSE}"|grep '"enable":true' &>/dev/null ;then
        logs all error "主机:${IP} Dubbo服务禁用异常，请检查!"
	    logs logfile error "CHECK_RESPONSE:${CHECK_RESPONSE}.\n"
        exit 1
    fi
}

dubbo_status(){
    #Result=`/usr/bin/curl -s "http://10.13.55.161:8010/yunnex-admin/dubbo/app/list?ip=${IP}&authkey=${AUTHKEY}"|awk -vRS="{"  -F'[:,"]+' 'NR>2{print $3,$10}'|awk '{if($2=="disable")printf("%-30s \033[1;31m%-10s \033[0m \n",$1,$2);else printf("%-30s %-10s\n",$1,$2)}'`
    #echo $Result
    RESPONSE=$(/usr/bin/curl -s "${DUBBO_APP_LIST_URL}?ip=${IP}&authkey=${AUTHKEY}")
    logs logfile info "RESPONSE:${RESPONSE}" 
    if ! echo "${RESPONSE}"|grep '"success":true' &>/dev/null ;then
        logs all error "${DUBBO_APP_LIST_URL}?ip=${IP}&authkey=${AUTHKEY}请求异常！"
        logs logfile error "RESPONSE:${RESPONSE}."
        exit 1
    else
        echo "${RESPONSE}"|grep -o '\[.*\]'|grep -o '{.*}'|sed -e 's/"//g' -e 's/,{/\n{/g'|awk  '{if($0 ~ /enable:true/ && $0 ~ /status:enable/){c+=1;ENABLE[c]=$0}else{n+=1;DISABLE[n]=$0}}END{print "服务状态正常:";for(i in ENABLE){print i,ENABLE[i]};printf "\n服务状态异常:\n";for(i in DISABLE){print i,DISABLE[i]}}'
    fi
}

dubbo() {
    IP=$(get_local_ip)
    case $1 in 
        disable)
            dubbo_disable
        ;;
        enable)
            dubbo_enable
        ;;
        status)
            dubbo_status
        ;;
        *)
            echo "Usage: `basename ${0}` --type dubbo [disable|enable|status]"
            usage
        ;;
    esac
}

#appctrl_v3.sh --help|-h
#              --dubbo --action|-a enable  [--project|-p PROJECT_NAME]
#                                  disable [--project|-p PROJECT_NAME]
#                                  status
#              --app --action|-a deploy [--project|-p PROJECT_NAME] --version|-v VERSION
#                                new --project|-p PROJECT_NAME --run-type <mods|webapps|webapps8030>
#                                list
#                                status                              
#              --force|-f 
#              --journal|-j

usage() {   
cat << EOF
appctrl_v4.sh --help|-h
              --zabbix --action|-a start|stop|restart|status
              --nginx --action|-a start|stop|status|reload|restart|configtest
              --dubbo --action|-a enable  [--project|-p PROJECT_NAME]
                                  disable [--project|-p PROJECT_NAME]
                                  status
              --app --action|-a deploy [--project|-p PROJECT_NAME] --version|-v VERSION
                                new --project|-p PROJECT_NAME --run-type <mods|webapps|webapps8030> [--version|-v VERSION]
                                list
                                status                              
              --cmdb --action|a start|stop|restart|refresh|status
              --force|-f 
              --journal|-j
EOF
exit
}


ZABBIX_ACTION=0; NGINX_ACTION=0; DUBBO_ACTION=0; APP_ACTION=0; CMDB_ACTION=0; OPTION_FORCE=0; OPTION_JOURNAL=0 
if [ $# -lt 1 ];then
    usage
fi

logs logfile info "[bash $0 $*]"

#while [ -n "$1" -a "$1" != "${1##[-+]}" ]; do
while [ -n "$1" ];do
    case "$1" in
        -h|--help)
            usage
            shift
            ;;
        --zabbix)
            ZABBIX_ACTION=1
            shift
            ;;
        --nginx)
            NGINX_ACTION=1
            shift
            ;;
        --dubbo) 
            DUBBO_ACTION=1
            shift 
            ;;
        --app)
            APP_ACTION=1
            shift 
            ;;
        --cmdb)
            CMDB_ACTION=1
            shift
            ;;
        -a|--action)
            OPTION_ACTION=$2
            [ -z "${OPTION_ACTION}" ]&& usage
            shift 2
            ;;
        --action=?*)    
            OPTION_ACTION=${1#--action=}
            [ -z "${OPTION_ACTION}" ]&& usage
            shift
            ;;
        --run-type)
            RUN_TYPE=$2
            [ -z "${RUN_TYPE}" ]&& usage
            shift 2
            ;; 
        --run-type=?*)
            RUN_TYPE=${1#--run-type=}
            [ -z "${RUN_TYPE}" ]&& usage
            shift
            ;; 
        -p|--project)
            PROJECT_NAME=$2
            [ -z "${PROJECT_NAME}" ]&& usage
            shift 2
            ;;
        --project=?*)   
            PROJECT_NAME=${1#--project=}
            [ -z "${PROJECT_NAME}" ]&& usage
            shift
            ;;
        -v|--version)
            VERSION=$2
            [ -z "${VERSION}" ]&& usage
            shift 2
            ;;
        --version=?*)
            VERSION=${1#--version=}
            [ -z "${VERSION}" ]&& usage
            shift
            ;;
        -f|--force)
            OPTION_FORCE=1
            shift
            ;;
        -j|--journal)
            OPTION_JOURNAL=1
            shift
            ;;
        *)
            usage
            ;;
    esac
done


if [ $UID -eq 0 ];then
    logs all warn "不能用特权用户(root)执行,请切换普通用户执行该脚本!"
    exit 1
fi

if [ -n "${SHELL_LOCK_FILE}" ];then
    if [ -f ${SHELL_LOCK_FILE} ];then
        if [ "${OPTION_FORCE}" -ne 1 ];then 
            logs all warn "脚本正在运行，请检查是否需强制执行！如需强制执行请指定-f|--force参数"
            exit 1
        else
            if [ -f "$SHELL_PID_FILE" ];then
                [ ! -r "$SHELL_PID_FILE" ] && exit 4 # "user had insufficient privilege"
                PID=`cat $SHELL_PID_FILE`
                if [ $PID -ne $$ -a -z "${PID//[0-9]/}" -a -d "/proc/$PID" ] ; then
                    kill -9 $PID
                fi
            fi
            shell_lock
        fi
    else
        shell_lock
    fi
else
    logs all warn "请指定SHELL_LOCK_FILE路径!"
    exit 1 
fi

if [ $OPTION_JOURNAL -eq 1 ];then
    logs all info '日志信息如下:'
    tail -n 10 $SHELL_LOG
    exit 0
#else
#    echo > $SHELL_LOG
fi

#if [ "${DUBBO_ACTION}" -eq 1 -a "${APP_ACTION}" -eq 1 ];then
if [ $[${ZABBIX_ACTION}+${NGINX_ACTION}+${DUBBO_ACTION}+${APP_ACTION}+${CMDB_ACTION}] -ne 1 ];then
    echo "Usage: `basename ${0}` --zabbix --nginx --dubbo --app --cmdb 不能指定多个,同时只能指定一个"
    usage
fi

if [ "${ZABBIX_ACTION}" -eq 1 ];then
    if [ "${OPTION_ACTION}"x == "stop"x ];then
        zabbix ${OPTION_ACTION}
    elif [ "${OPTION_ACTION}"x == "start"x ];then
        zabbix ${OPTION_ACTION}
    elif [ "${OPTION_ACTION}"x == "restart"x ];then
        zabbix ${OPTION_ACTION}
    elif [ "${OPTION_ACTION}"x == "status"x ];then
        zabbix ${OPTION_ACTION}
    else 
        echo "Usage: `basename ${0}` --type zabbix --action must be [stop|start|restart|status]"
        usage
    fi
fi

app_dubbo_enable(){
    if `find $BASE_LOCAL/{webapps,webapps8030} -type l 2>/dev/null | xargs -i ls -l {} | awk -F'/' '{print $NF}' | egrep 'marketing|canyin|waimai' >/dev/null` ;then
       dubbo enable
    fi
}

app_dubbo_disable(){
    if `find $BASE_LOCAL/{webapps,webapps8030} -type l 2>/dev/null | xargs -i ls -l {} | awk -F'/' '{print $NF}' | egrep 'marketing|canyin|waimai' >/dev/null` ;then
       dubbo disable
    fi
}

app_dubbo(){
    case $1 in 
        disable)
            app_dubbo_disable
        ;;
        enable)
            app_dubbo_enable
        ;;
        status)
            dubbo_status
        ;;
        *)
            echo "Usage: `basename ${0}` --type dubbo [disable|enable|status]"
            usage
        ;;
    esac
}

if [ "${NGINX_ACTION}" -eq 1 ];then
    if [ "${OPTION_ACTION}"x == "stop"x ];then
        nginx ${OPTION_ACTION} 
        app_dubbo disable
    elif [ "${OPTION_ACTION}"x == "start"x ];then
        nginx ${OPTION_ACTION}
        app_dubbo enable
    elif [ "${OPTION_ACTION}"x == "restart"x ];then
        nginx ${OPTION_ACTION}
    elif [ "${OPTION_ACTION}"x == "reload"x ];then
        nginx ${OPTION_ACTION}
    elif [ "${OPTION_ACTION}"x == "configtest"x ];then
        nginx ${OPTION_ACTION}
    elif [ "${OPTION_ACTION}"x == "status"x ];then
        nginx ${OPTION_ACTION}
    else    
        echo "Usage: `basename ${0}` --type nginx --action must be [stop|start|restart|reload|status|configtest]"
        usage
    fi
fi

mod_nginx_start(){
    if [ -e ${NGINX_SCRIPT} ];then
        nginx start
    fi
}

mod_nginx_stop(){
    if [ -e ${NGINX_SCRIPT} ];then
        nginx stop
    fi
}

mod_nginx(){
    case $1 in
        start)
            mod_nginx_start
            ;;
        stop)
            mod_nginx_stop
            ;;
    esac
}

if [  "${DUBBO_ACTION}" -eq 1 ];then
    if [ "${OPTION_ACTION}"x == "enable"x ];then
        dubbo enable 
        mod_nginx start
    elif [ "${OPTION_ACTION}"x == "disable"x ];then
        dubbo disable
        mod_nginx stop
    elif [ "${OPTION_ACTION}"x == "status"x ];then
        dubbo status
        if [ -e ${NGINX_SCRIPT} ];then
           nginx status
        fi
    else    
        echo "Usage: `basename ${0}` --type dubbo --action must be [enable|disable|status]"
        usage
    fi
fi

if [  "${APP_ACTION}" -eq 1 ];then
    if [ "${OPTION_ACTION}"x == "deploy"x ];then
        app deploy 
    elif [ "${OPTION_ACTION}"x == "list"x ];then
        app list
    elif [ "${OPTION_ACTION}"x == "status"x ];then
        app status
    elif [ "${OPTION_ACTION}"x == "new"x ];then
        app new
    else    
        echo "Usage: `basename ${0}` --type app --action must be [deploy|list|status|new]"
        usage
    fi
fi
#update cmdb info
#/data/sh/cmdb-agent.sh refresh
if [ "${CMDB_ACTION}" -eq 1 ];then
    cmdb ${OPTION_ACTION}
fi
echo >> $SHELL_LOG
