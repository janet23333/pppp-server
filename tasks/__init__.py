from tasks import deploy, dubbo, nginx, get_package, service, rollback

task_name_to_task_obj = {
    "执行发版": deploy.run,
    "查询dubbo状态": dubbo.status,
    "启动dubbo": dubbo.enable,
    '停止dubbo': dubbo.disable,
    "查询nginx状态": nginx.status,
    "启动nginx": nginx.start,
    '停止nginx': nginx.stop,
    "重启nginx": nginx.restart,
    '检测conf 文件是否有效': nginx.configtest,
    'nginx reload': nginx.reload,
    "下载包到目标服务器": get_package.get_package,
    "执行回滚": rollback.run,
    "查询service状态": service.status,
    "启动service": service.start,
    '停止service': service.stop,
    "重启service": service.restart,
    "列举该主机部署的应用": service.list,
}
