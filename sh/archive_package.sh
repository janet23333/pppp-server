#!/bin/bash

TIME=${2-`date +%m%d%H%M`}
PROJECT_DIR=/home/data/project
RELEASE_DIR=$1
INDEX_DIR=${PROJECT_DIR}/index
TMP_DIR=${PROJECT_DIR}/tmp
LOGPATH=$PROJECT_DIR/release/predeploy.log



if [[ -n "$TMP_DIR" && "$TMP_DIR" =~ "tmp" ]];then
   [ -d $TMP_DIR ]&&rm -rf $TMP_DIR/*||mkdir -p $TMP_DIR
else
   echo "ERROR: $TMP_DIR未指定或路径未包含tmp字符!"
   exit 1
fi

log() {
    local LOGTIME=$(date +"%F %R")
    [ ! -f ${LOGPATH} ]&&touch $LOGPATH||(exit 1)
    if [ $1 == "all" ];then
       shift 1
       msg=$@
       echo -e "$LOGTIME" "$msg"|tee -a ${LOGPATH}
    elif [ $1 == "stdio" ];then
       shift 1
       msg=$@
       echo -e "$LOGTIME" "$msg"
    elif [ $1 == "log" ];then
       shift 1
       msg=$@
       echo -e "$LOGTIME" "$msg" >> ${LOGPATH}
    else
       msg=$@
       echo -e "$LOGTIME" "$msg"|tee -a ${LOGPATH}
    fi

}

[ ! -d $INDEX_DIR ];mkdir -p $INDEX_DIR
touch ${INDEX_DIR}/${TIME}.index

if [ -n "$RELEASE_DIR" -a -d "$RELEASE_DIR" ];then
    cd $RELEASE_DIR
    for pkg in *.zip;do
        pkg_name=${pkg%.zip}
        [ ! -d $TMP_DIR/$pkg_name ] && mkdir -p $TMP_DIR/$pkg_name
        unzip -q $pkg -d $TMP_DIR/$pkg_name
        if [ $? -eq 0 ];then
             for p in `ls $TMP_DIR/$pkg_name|grep 'bin.zip.info$\|.war.info$'`;do
                 if [[ "$p" =~ "bin.zip.info"$ ]];then
                      pkg_ver_tmp=`cat $TMP_DIR/$pkg_name/$p |grep "APP-Package"`
                      pkg_ver_tmp2=${pkg_ver_tmp#APP-Package: }
                      pkg_ver=${pkg_ver_tmp2%-bin.zip}
                      version=${pkg_ver##*-}

                      commit_id_tmp=`cat $TMP_DIR/$pkg_name/$p |grep "LAST-COMMIT-ID"`
                      commit_id=${commit_id_tmp#LAST-COMMIT-ID: }


                      mkdir -p $TMP_DIR/$pkg_name/${version}-$TIME
                      mv $TMP_DIR/$pkg_name/*zip* $TMP_DIR/$pkg_name/${version}-$TIME


                      #echo "mkdir -p $TMP_DIR/$pkg_name/${version}-$TIME"
                      #echo "mv $TMP_DIR/$pkg_name/*zip* $TMP_DIR/$pkg_name/${version}-$TIME"
                 elif [[ "$p" =~ ".war.info"$ ]];then
                      pkg_ver_tmp=`cat $TMP_DIR/$pkg_name/$p |grep "APP-Package"`
                      pkg_ver_tmp2=${pkg_ver_tmp#APP-Package: }
                      pkg_ver=${pkg_ver_tmp2%.war}
                      version=${pkg_ver##*-}

                      commit_id_tmp=`cat $TMP_DIR/$pkg_name/$p |grep "LAST-COMMIT-ID"`
                      commit_id=${commit_id_tmp#LAST-COMMIT-ID: }


                 	  mkdir -p $TMP_DIR/$pkg_name/${version}-$TIME
                      mv $TMP_DIR/$pkg_name/*war* $TMP_DIR/$pkg_name/${version}-$TIME
                      #echo "mkdir -p $TMP_DIR/$pkg_name/${version}-$TIME"
                      #echo "mv $TMP_DIR/$pkg_name/*war* $TMP_DIR/$pkg_name/${version}-$TIME"
                 else
                     echo "ERROR: ${pkg_name}编译包名称不规范,请检查!"
                     #continue
                     exit 1
                 fi
            done
            [ ! -d $PROJECT_DIR/$pkg_name ]&& mkdir -p $PROJECT_DIR/$pkg_name
            mv $TMP_DIR/$pkg_name/${version}-$TIME $PROJECT_DIR/$pkg_name
            if ! `grep "^$pkg_name " ${INDEX_DIR}/${TIME}.index &> /dev/null`;then
                echo "$pkg_name ${version}-$TIME $commit_id $PROJECT_DIR/$pkg_name/${version}-$TIME" >> ${INDEX_DIR}/${TIME}.index
            fi
        else
            echo "ERROR: $pkg_name 解压失败!"
            exit 1
        fi
    done
    if [ $(wc -l ${INDEX_DIR}/${TIME}.index|awk '{print $1}') -eq 0 ];then
        log all "INFO: 未发现需发布包,请确认是否存在zip包."
        exit 1
    else
        log log "=====Version $TIME ====="
        log all "INFO: 索引文件见 ${INDEX_DIR}/${TIME}.index"
        log all "INFO: 该次部署版本如下:"
        log all `awk '{print $1":"$2}' ${INDEX_DIR}/${TIME}.index`

        PROJECTS=`cat ${INDEX_DIR}/${TIME}.index|awk '{printf $1","}'`
        rollback_version_tmp=/tmp/rollback_version_tmp_${TIME}.txt
        #/usr/local/bin/cmdb -v -a ${PROJECTS} |awk 'NR>2{if($0 != ""){sub(/,/,"\n",$NF);print $NF}}'|sort -u|sed -e 's/(/ /g' -e 's/)//g' > $rollback_version_tmp
        #/usr/local/bin/cmdb -v -a ${PROJECTS} | grep -v ^$ | awk '(NR>2 && $(NF-1)=="master") || (NR>2 && $(NF-1)=="grey") {print $NF}' | sed 's/\,/\n/g' | sort -u | awk -F'[()]' 'NF>1 {print $1,$2}' > $rollback_version_tmp
        /usr/local/bin/cmdb -v --raw -a ${PROJECTS} -o hostname -o deploy_env -o status -o application |grep -v ^$|awk '($(NF-1)=="online") {print $NF}' |sed 's/\,/\n/g' | sort -u | awk -F'[()]' 'NF>1 {print $1,$2}' > $rollback_version_tmp

        > ${INDEX_DIR}/${TIME}_rollback.index
        for app in `echo $PROJECTS|sed 's/,/ /g'`;do
            if [ `awk -v app=$app '{if($1 == app){print $0}}' $rollback_version_tmp |wc -l` -lt 1 ];then
                log all "WARN: $app CMDB中无版本号,请确认$app 是否为新增模块,是新增模块忽略此提示,如果不是新增模块请检查."
            elif [ `awk -v app=$app '{if($1 == app){print $0}}' $rollback_version_tmp |wc -l` -eq 1 ];then
                awk -v app=$app '{if($1 == app){print $0}}' $rollback_version_tmp >> ${INDEX_DIR}/${TIME}_rollback.index
            else
                massage="在CMDB中存在多个版本,请确认回滚版本,手动编辑${INDEX_DIR}/${TIME}_rollback.index打开需要回滚的版本注释."
                awk -v app="#$app" '{if($1 == app){print $0}}' ${INDEX_DIR}/${TIME}_rollback.index | grep "^#$app\ " >/dev/null 2>&1 || ( echo -e "\033[31m[WARN]\033[0m: \033[31m$app\033[0m $massage" ; log log "WARN: $app $massage")
                awk -v app=$app '{if($1 == app){print "#"$0}}' $rollback_version_tmp >> ${INDEX_DIR}/${TIME}_rollback.index
            fi
        done
        rm -rf $rollback_version_tmp
        log all "INFO: 该次部署回滚索引文件见 ${INDEX_DIR}/${TIME}_rollback.index"
        echo -e "\nINFO: 历史信息见 $LOGPATH\n"
        /home/data/project/release/.rsync_packge.sh ${INDEX_DIR}/${TIME}_rollback.index
    fi

else
    echo "ERROR: $RELEASE_DIR 不存在,请检查!"
    exit 1
fi
