#!/bin/bash
time=${2-`date +%m%d%H%M`}
project_dir=/home/data/project
release_dir=${project_dir}/release
index_dir=${project_dir}/index
tmp_dir=${project_dir}/tmp
project_list=${project_dir}/project_list.txt

file_path=$1

if [ $# -ne 2 ]; then
    echo $"Usage: sh $0 package_path datetime"
    exit 1
fi

if [ -z "$project_list" -o ! -f "$project_list" ];then
    echo "error: $project_list 文件不存在!"
    exit 1
fi

if [[ -n "$tmp_dir" && "$tmp_dir" =~ "tmp" ]];then
   [ -d $tmp_dir ]&&rm -rf $tmp_dir/*||mkdir -p $tmp_dir
else
   echo "error: $tmp_dir未指定或路径未包含tmp字符!"
   exit 1
fi

[ ! -d $index_dir ];mkdir -p $index_dir
touch ${index_dir}/${time}.index

if [ -n "$file_path" -a -d "$file_path" ];then
    cd $file_path
    for pkg in *.zip;do
        pkg_name=${pkg%.zip}
        [ ! -d $tmp_dir/$pkg_name ] && mkdir -p $tmp_dir/$pkg_name
        unzip -q $pkg -d $tmp_dir/$pkg_name
        if [ $? -eq 0 ];then
             for p in `ls $tmp_dir/$pkg_name|grep 'bin.zip$\|.war$'`;do
                 if [[ "$p" =~ "bin.zip"$ ]];then
                      pkg_ver=${p%-bin.zip}
                      version=${pkg_ver##*-}
                      mkdir -p $tmp_dir/$pkg_name/${version}-$time
                      mv $tmp_dir/$pkg_name/*zip* $tmp_dir/$pkg_name/${version}-$time
                      #echo "mkdir -p $tmp_dir/$pkg_name/${version}-$time"
                      #echo "mv $tmp_dir/$pkg_name/*zip* $tmp_dir/$pkg_name/${version}-$time"
                 elif [[ "$p" =~ ".war"$ ]];then
         	          pkg_ver=${p%.war}
                      version=${pkg_ver##*-}
                 	  mkdir -p $tmp_dir/$pkg_name/${version}-$time
                      mv $tmp_dir/$pkg_name/*war* $tmp_dir/$pkg_name/${version}-$time
                      #echo "mkdir -p $tmp_dir/$pkg_name/${version}-$time"
                      #echo "mv $tmp_dir/$pkg_name/*war* $tmp_dir/$pkg_name/${version}-$time"
                 else
                     echo "error: ${pkg_name}编译包名称不规范,请检查!"
                     exit 1
                 fi
            done
         	#pkg_group=`grep -p "\b${pkg_name}\b" ${project_list}|grep -v "\-${pkg_name}"|grep -v "${pkg_name}\-"|awk -f ':' '{print $1}'`
         	pkg_group=`grep -P "\b${pkg_name}\b" ${project_list}|expand|tr -s ' '|awk -v project_name=${pkg_name} -F '[ :]' '{for(i=3;i<=NF;i++){if($i == project_name)print $1}}'`
         	if [ -n "$pkg_group" ];then
                [ ! -d $project_dir/$pkg_group/$pkg_name ]&& mkdir -p $project_dir/$pkg_group/$pkg_name
         	    mv $tmp_dir/$pkg_name/${version}-$time $project_dir/$pkg_group/$pkg_name
         	    #echo "mv $tmp_dir/$pkg_name/${version}-$time $project_dir/$pkg_group/$pkg_name"
                if ! `grep "^$pkg_name " ${index_dir}/${time}.index &> /dev/null`;then
                    echo "$pkg_name ${version}-$time $project_dir/$pkg_group/$pkg_name/${version}-$time" >> ${index_dir}/${time}.index
                fi
         	else
         	    echo "error: 请先在project_list中定义${pkg_nam}对应组!"
         	    exit 1
         	fi
        else
            echo "error: $pkg_name 解压失败!"
            exit 1
        fi
    done
    echo "info: 索引文件见 ${index_dir}/${time}.index"
    echo "该次部署版本如下:"
    awk '{print $2}' ${index_dir}/${time}.index|sort -u
else
    echo "error: $file_path 不存在,请检查!"
    exit 1
fi
