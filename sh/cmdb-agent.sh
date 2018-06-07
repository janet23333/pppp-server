#!/bin/bash
#python_path="/data/env/python36/bin/python"
#program="/data/application/cmdb-agent/cmdb-agent.py"

python_path="/data/svr/python-env/bin/python"
program="/data/svr/cmdb-agent/cmdb-agent.py"

if [[ ! -d '/home/product' ||  $(grep -c product /etc/passwd |wc -l) -eq 0 ]]; then
    echo 'user product is or /home/product is not exits'
    exit 1
fi

if [ $USER != "product" ];then
    echo "请切换普通用户product下执行该脚本!"
    exit 1
fi


cmdb_start() {
      pid=$(ps -ef |grep cmdb-agent.py|grep -v grep |awk '{print $2}')
      if [[ $pid ]]; then
          echo "cmdb-agent (pid: $pid) is running, please don't start again"
          exit 0
      fi
      if [[ $(whoami) == 'root' ]]; then
          su - product -c "nohup $python_path $program > /dev/null 2>&1 &"
      elif [[ $(whoami) == 'product' ]]; then
          nohup $python_path $program > /dev/null 2>&1 &
      else
          echo 'current user  is not product, please su - product run cmdb-agent'
          exit 1
      fi
}


cmdb_stop() {
    pid=$(ps -ef |grep cmdb-agent.py|grep -v grep |awk '{print $2}')
    if test ! -z $pid; then
        kill -9 $pid
    fi
}



cmdb_status() {
      pid=$(ps -ef |grep cmdb-agent.py|grep -v grep |awk '{print $2}')
      if test -z $pid; then
          echo "cmdb-agent is stoped"
          exit 1
      else
          echo "cmdb-agent (pid: $pid) is running"

      fi
}


cmdb_refresh() {
    kill -n 10 $(cat /tmp/cmdb-agent.pid)
}

cmdb_restart() {
      cmdb_stop && echo -e "stopping cmdb-agent:                         \033[32m [ Ok ] \033[0m"
      cmdb_start && echo -e "starting cmdb-agent:                         \033[32m [ Ok ] \033[0m"
}



case "$1" in

  start)
       cmdb_start
       ;;
  stop)
       cmdb_stop
       ;;
  status)
       cmdb_status
       ;;
  refresh)
       cmdb_refresh
       ;;
  restart)
       cmdb_restart
       ;;
  *)
       echo $"Usage: $0 {start|stop|status|refresh|restart}"
       exit 1

esac


