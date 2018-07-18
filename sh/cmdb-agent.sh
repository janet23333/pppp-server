#!/bin/bash
#python_path="/data/env/python36/bin/python"
#program="/data/application/cmdb-agent/cmdb-agent.py"
set -x
python_path="/data/svr/python-env/bin/python"
program="/data/svr/cmdb-agent/cmdb-agent.py"
shell_name=$(/bin/basename $0)
if [[ ! -d '/home/product' ||  $(grep -c product /etc/passwd |wc -l) -eq 0 ]]; then
    echo 'user product is or /home/product is not exits'
    exit 1
fi

pid=$(ps -ef |grep cmdb-agent.py|grep -v grep |awk '{print $2}')

log() {
    log_info=$1
    echo "[$(/bin/date "+%Y-%m-%d %H:%M:%S")] pid:$$ ${shell_name}: ${log_info}"
}

cmdb_start() {
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
    if test ! -z $pid; then
        kill -9 $pid
    fi
}



cmdb_status() {
      if test -z $pid; then
          echo "cmdb-agent is stoped"
          exit 1
      else
          echo "cmdb-agent (pid: $pid) is running"

      fi
}


cmdb_refresh() {
    kill -10 $pid 2>/dev/null
    retval=$? && [ $retval = 0 ] &&  log "[info] [func:cmdb_refresh] ${project_name} cmdb 更新成功.............."
    if [ $retval -ne 0 ];then
        log "[waring] [func:cmdb_refresh] ${project_name} cmdb 更新失败.............." ; exit 1
    fi
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


