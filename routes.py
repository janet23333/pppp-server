from handler.audit_log import AuditLogHandler
from handler.check_package_url import CheckPackageURLHandler
from handler.cmdb_agent import CMDBAgentOperationHandler
from handler.deploy import DeployOperationHandler
from handler.dubbo import DubboOperationHandler
from handler.get_cmdb_host import CMDBHostHandler
from handler.host_log import HostLogWebSocket
from handler.nginx import NginxOperationHandler
from handler.notfound import NotFoundHandler
from handler.package import PackageOperationHandler
from handler.pattern_host import PatternHostTaskWebSocket
from handler.pattern_task import PatternTaskWebSocket
from handler.publish_pattern import PublishPatternHandler, PatternAction
from handler.publish_plan import PlanDetailHandler
from handler.publish_plan import PublishPlanHandler
from handler.publish_plan import PublishPlanWebSocket
from  handler.publish_plan import  PlanRetryHandler
from handler.rollback import RollbackOperationHandler
from handler.service import ServiceOperationHandler
from handler.task_status import TaskStatusHandler
from handler.task_status import TaskStatusWebSocket
from handler.test_ansible import OperationHandler
from handler.test_websocket import TestWebSocket
from handler.token import TokenHandler
from handler.user import UserHandler
from handler.zabbix_agent import ZabbixOperationHandler

ROUTES = [
    (r'/api/test/?$', OperationHandler),
    (r'/api/test/websocket/?$', TestWebSocket),
    (r'/api/user/?', UserHandler),
    (r'/api/ws/publish_plan/?', PublishPlanWebSocket),
    (r'/api/publish_plan/?', PublishPlanHandler),
    (r'/api/plan_detail/?', PlanDetailHandler),
    (r'/api/publish_plan_retry/?', PlanRetryHandler),
    (r'/api/token/?', TokenHandler),
    (r'/api/nginx/?', NginxOperationHandler),
    (r'/api/dubbo/?', DubboOperationHandler),
    (r'/api/cmdb/?', CMDBAgentOperationHandler),
    (r'/api/zabbix/?', ZabbixOperationHandler),
    (r'/api/package/?', PackageOperationHandler),
    (r'/api/taskstatus/?', TaskStatusHandler),
    (r'/api/ws/taskstatus/?', TaskStatusWebSocket),
    (r'/api/deploy/?', DeployOperationHandler),
    (r'/api/service/?', ServiceOperationHandler),
    (r'/api/rollback/?', RollbackOperationHandler),
    (r'/api/audit_log/?', AuditLogHandler),
    (r'/api/publish_pattern/?', PublishPatternHandler),
    (r'/api/cmdb_host/?', CMDBHostHandler),
    (r'/api/ws/pattern_task/?', PatternTaskWebSocket),
    (r'/api/ws/pattern_host_task/?', PatternHostTaskWebSocket),
    (r'/api/ws/host_log/?', HostLogWebSocket),
    (r'/api/check_package_url/?', CheckPackageURLHandler),
    (r'/api/pattern_action/?', PatternAction),
    (r'.*', NotFoundHandler)
]
