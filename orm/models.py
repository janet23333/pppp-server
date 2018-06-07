from sqlalchemy import Column, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import String, Text, Integer, DateTime, SmallInteger

BaseModel = declarative_base()


class TableMixin(object):
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __mapper_args__ = {'always_refresh': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    create_time = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    update_time = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)


class UserDepartment(TableMixin, BaseModel):
    __tablename__ = 'user_department'

    user_id = Column(Integer, server_default=text('0'), nullable=False)
    department_id = Column(Integer, server_default=text('0'), nullable=False)

    user = relationship(
        'User', foreign_keys='User.id', primaryjoin='UserDepartment.user_id == User.id', uselist=False, backref='user')

    department = relationship(
        'Department',
        foreign_keys='Department.id',
        primaryjoin='UserDepartment.user_id == Department.id',
        uselist=False,
        backref='department')


class Department(TableMixin, BaseModel):
    __tablename__ = 'department'

    name = Column(String(128), server_default='', nullable=False)

    users = relationship(
        'User',
        primaryjoin='UserDepartment.department_id==Department.id',
        secondary=UserDepartment.__table__,
        secondaryjoin='UserDepartment.user_id == foreign(User.id)')

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


class User(TableMixin, BaseModel):
    __tablename__ = 'user'

    fullname = Column(String(128), server_default='', nullable=False)
    email = Column(String(128), server_default='', nullable=False)
    username = Column(String(128), server_default='', nullable=False)
    departments = relationship(
        'Department',
        primaryjoin='UserDepartment.user_id==User.id',
        secondary=UserDepartment.__table__,
        secondaryjoin='UserDepartment.department_id==foreign(Department.id)')

    def to_dict(self):
        return {
            'id': self.id,
            'fullname': self.fullname,
            'username': self.username,
            'email': self.email,
            'create_time': str(self.create_time),
            'update_time': str(self.update_time),
            'department_name': ' '.join([department.name for department in self.departments])
        }


class PublishPlan(TableMixin, BaseModel):
    # 一次发版计划：只需提供需要发版的应用名称。
    # 大发版：多个应用
    # bugfix： 单个应用
    __tablename__ = 'publish_plan'

    title = Column(String(128), server_default='', nullable=False)
    description = Column(String(1024), server_default='', nullable=False)
    application_list = relationship(
        'PublishApplication',
        foreign_keys='PublishApplication.publish_plan_id',
        cascade="all, delete-orphan",
        backref="publish_plan",
        primaryjoin='PublishApplication.publish_plan_id==PublishPlan.id')

    create_user_id = Column(Integer, server_default=text('0'), nullable=False)
    create_user = relationship(
        'User',
        foreign_keys='PublishPlan.create_user_id',
        primaryjoin='PublishPlan.create_user_id == User.id',
        uselist=False,
        doc='创建发版任务的人')
    inventory_version = Column(String(128), server_default='', nullable=False, comment='inventory文件版本')

    status = Column(SmallInteger, server_default=text('0'), nullable=False,
                    comment='1: 创建中 2：创建完成  3：创建失败  4:发版成功 5：发版失败 6：已回滚 7：已删除 8：发版中')
    type = Column(SmallInteger, server_default=text('0'), nullable=False, comment='发版计划类型. 0:小版本 1:大版本')
    finish_time = Column(DateTime, server_default=text('"0000-00-00 00:00:00"'), nullable=False, comment='完成时间')

    def to_dict(self):
        return {
            'id':
                self.id,
            'title':
                self.title,
            'description':
                self.description,
            'inventory_version':
                self.inventory_version,
            'application_list': [
                publish_application.to_dict() for publish_application in self.application_list
                if publish_application.current_flag == 1
            ],
            'create_time':
                str(self.create_time),
            'update_time':
                str(self.update_time),
            'finish_time':
                str(self.finish_time),
            'create_user':
                self.create_user.to_dict() if self.create_user is not None else None,
            'status':
                self.status,
            'type':
                self.type
        }


class PublishApplication(TableMixin, BaseModel):
    # 对应发版计划中的发版应用
    # 如一次发版计划，涉及10个应用，则生成10个发版应用。
    __tablename__ = 'publish_application'

    application_name = Column(String(128), server_default='', nullable=False, comment='应用名称')
    application_type = Column(SmallInteger, server_default='1', nullable=False, comment='应用类型：1 web 2 mod')
    target_version = Column(String(128), server_default='', nullable=False, comment='需要发版的版本')
    current_flag = Column(
        SmallInteger, server_default=text('1'), nullable=False, comment='修改下载地址之后,创建新的publish application,并且将字段置为1')
    jenkins_url = Column(String(128), server_default='', nullable=False, comment='jenkins下载地址')

    publish_plan_id = Column(Integer, server_default=text('0'), nullable=False, comment='发版计划ID')

    host_list = relationship(
        'PublishHost',
        foreign_keys='PublishHost.publish_application_id',
        cascade="all, delete-orphan",
        backref="publish_application",
        primaryjoin='PublishHost.publish_application_id==PublishApplication.id')

    def to_dict(self):
        return {
            'id': self.id,
            'application_name': self.application_name,
            'application_type': self.application_type,
            'target_version': self.target_version,
            'jenkins_url': self.jenkins_url,
            'host_list': [host.to_dict() for host in self.host_list],
            'create_time': str(self.create_time),
            'update_time': str(self.update_time),
        }


class PublishHost(TableMixin, BaseModel):
    # application和主机的对应关系
    __tablename__ = 'publish_host'

    publish_application_id = Column(Integer, server_default=text('0'), nullable=False, comment='发版应用ID')
    progress = Column(Integer, server_default=text('0'), nullable=False, comment='主机发版进度')
    host_name = Column(String(128), server_default='', nullable=False, comment='host name')
    host_ip = Column(String(128), server_default='', nullable=False, comment='host ip')
    host_flag = Column(SmallInteger, server_default=text('0'), nullable=False, comment='主机标识 1:master 2:slave 3:gray')
    rollback_version = Column(String(128), server_default='', nullable=False, comment='回滚版本')

    def to_dict(self):
        return {
            'id': self.id,
            'publish_application_id': self.publish_application_id,
            'host_name': self.host_name,
            'host_ip': self.host_ip,
            'host_flag': self.host_flag,
            'rollback_version': self.rollback_version,
            'create_time': str(self.create_time),
            'update_time': str(self.update_time),
            'progress': self.progress,
        }


class PublishTask(TableMixin, BaseModel):
    # 具体对应到每一个celery任务。
    # 可以认为，是最小的可执行单元。
    # 是对celery内置对象的一个补充。
    __tablename__ = 'publish_task'

    celery_task_id = Column(String(155), server_default='', nullable=False, comment='celery task ID')
    task_name = Column(String(128), server_default='', nullable=False, comment='任务名称')
    publish_pattern_task_id = Column(
        Integer, server_default=text('0'), nullable=False, comment='publish pattern task ID')
    publish_host_id = Column(
        Integer, server_default=text('0'), nullable=False, comment='publish host ID')
    start_time = Column(DateTime, server_default=text('\'0000-00-00 00:00:00\''), nullable=False, comment='任务开始时间')
    end_time = Column(DateTime, server_default=text('\'0000-00-00 00:00:00\''), nullable=False, comment='任务结束时间')
    status = Column(String(50), server_default='', nullable=False, comment='任务状态；PENDING STARTED SUCCESS FAILURE')

    result = Column(Text, comment='任务执行的结果；可由celery写入，也可以由回调函数写入')
    # 可以使用临时文件
    script = Column(Text, comment='任务调用的具体的ansible脚本')
    ansible_task = relationship(
        'AnsibleTaskResult',
        foreign_keys='PublishTask.celery_task_id',
        primaryjoin='PublishTask.celery_task_id == AnsibleTaskResult.celery_task_id',
        uselist=False,
        doc='ansible task')

    def to_dict(self):
        return {
            'id': self.id,
            'celery_task_id': self.celery_task_id,
            'task_name': self.task_name,
            'publish_pattern_task_id': self.publish_pattern_task_id,
            # 'start_time': str(self.start_time),
            # 'end_time': str(self.end_time),
            'status': self.status,
            # 'result': self.result,
            'script': self.script,
            'ansible_task': self.ansible_task.to_dict() if self.ansible_task is not None else None,
            'create_time': str(self.create_time),
            'update_time': str(self.update_time),
        }


class AnsibleTaskResult(TableMixin, BaseModel):
    # 对 ansible 执行结果进行拆分
    __tablename__ = 'ansible_task_result'

    host = Column(String(128), server_default='', nullable=False, comment='hostname or ip ')
    cmd = Column(String(1024), server_default='', nullable=False, comment="执行的命令")
    status = Column(String(50), server_default='', nullable=False, comment='执行状态， SUCCESS FAILED UNREACHABLE')
    rc = Column(SmallInteger, server_default=text('-1'), nullable=False, comment='rc 返回值')
    changed = Column(SmallInteger, server_default=text('0'), nullable=False, comment="1: True 2: False")
    stderr_lines = Column(Text, comment="stderr_lines")
    stdout_lines = Column(Text, comment="stdout_lines")
    delta_time = Column(String(128), server_default='', nullable=False, comment="执行所消耗时间")
    start_time = Column(DateTime, server_default=text('\'0000-00-00 00:00:00\''), nullable=False, comment="开始执行时间")
    end_time = Column(DateTime, server_default=text('\'0000-00-00 00:00:00\''), nullable=False, comment="执行结束时间")
    celery_task_id = Column('celery_task_id', String(128), comment='celery task ID，创建celery task的时候，可以获得')

    def to_dict(self):
        return {
            'id': self.id,
            'host': self.host,
            'cmd': self.cmd,
            'status': self.status,
            'rc': self.rc,
            'delta_time': self.delta_time,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'stdout_lines': self.stdout_lines,
            'create_time': str(self.create_time),
            'update_time': str(self.update_time),
        }


class AuditLog(TableMixin, BaseModel):
    __tablename__ = 'audit_log'

    user_id = Column(Integer, server_default='0', nullable=False, comment='关联user表id')
    user = relationship(
        'User', foreign_keys='AuditLog.user_id', primaryjoin='AuditLog.user_id == User.id', uselist=False, doc='user')
    resource_type = Column(
        SmallInteger,
        server_default='0',
        nullable=False,
        comment='操作资源类型 1:publish_plan 2:publish_application 3:publish_host 4:pattern')
    resource_id = Column(Integer, server_default='0', nullable=False, comment='操作资源id')
    publish_plan = relationship(
        'PublishPlan',
        foreign_keys='AuditLog.resource_id',
        primaryjoin='AuditLog.resource_id == PublishPlan.id',
        uselist=False,
        doc='publish_plan')
    publish_application = relationship(
        'PublishApplication',
        foreign_keys='AuditLog.resource_id',
        primaryjoin='AuditLog.resource_id == PublishApplication.id',
        uselist=False,
        doc='publish_application')
    publish_host = relationship(
        'PublishHost',
        foreign_keys='AuditLog.resource_id',
        primaryjoin='AuditLog.resource_id == PublishHost.id',
        uselist=False,
        doc='publish_host')
    publish_pattern = relationship(
        'PublishPattern',
        foreign_keys='AuditLog.resource_id',
        primaryjoin='AuditLog.resource_id == PublishPattern.id',
        uselist=False,
        doc='publish_pattern')
    description = Column(String(128), server_default='', nullable=False, comment='操作描述')
    visible = Column(SmallInteger, server_default='1', nullable=False, comment='前端是否可见 1: True 0: False')
    method = Column(String(64), server_default='', nullable=False, comment='请求方法')
    path = Column(String(1024), server_default='', nullable=False, comment='请求URL')
    fullpath = Column(String(4096), server_default='', nullable=False, comment='完整的请求URL')
    body = Column(String(4096), server_default='', nullable=False, comment='请求的body')

    def to_dict(self, return_resource=False):
        result = {
            'id': self.id,
            'create_time': str(self.create_time),
            'update_time': str(self.update_time),
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user_id != 0 else None,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'visible': self.visible,
            'method': self.method,
            'path': self.path,
            'fullpath': self.fullpath,
            'body': self.body
        }
        if return_resource:
            result['resource'] = self.get_resource()

        return result

    def get_resource(self):
        type_map = {
            1: self.publish_plan,
            2: self.publish_application,
            3: self.publish_host,
            4: self.publish_pattern,
        }

        resource = type_map.get(self.resource_type)
        if resource:
            return resource.to_dict()

        return None


class HostLog(TableMixin, BaseModel):
    __tablename__ = 'host_log'
    host_name = Column(String(128), server_default='', nullable=False, comment='host name')
    host_ip = Column(String(128), server_default='', nullable=False, comment='host ip')
    publish_host_id = Column(Integer, server_default='0', nullable=False, comment='关联publish_host表id')
    task_name = Column(String(128), server_default='', nullable=False, comment='任务名称')
    task_status = Column(String(128), server_default='', nullable=False, comment='任务状态：开始，成功，失败')

    def to_dict(self):
        result = {
            'id': self.id,
            'create_time': str(self.create_time),
            'update_time': str(self.update_time),
            'host_name': self.host_name,
            'host_ip': self.host_ip,
            'task_name': self.task_name,
            'task_status': self.task_status,
            'publish_host_id': self.publish_host_id
        }

        return result


class PublishPattern(TableMixin, BaseModel):
    __tablename__ = 'publish_pattern'

    publish_plan_id = Column(Integer, server_default='0', nullable=False, comment='关联publish_plan_id')
    step = Column(Integer, server_default='0', nullable=False, comment='记录执行顺序')
    title = Column(String(64), server_default='0', nullable=False, comment='标题')
    note = Column(String(4096), server_default='0', nullable=False, comment='备注')
    action = Column(Integer, server_default='0', nullable=False, comment='动作 1: 发布 2: 停服务 3: 提示')
    publish_pattern_host_list = relationship(
        'PublishPatternHost',
        uselist=True,
        foreign_keys='PublishPatternHost.publish_pattern_id',
        primaryjoin='PublishPattern.id == PublishPatternHost.publish_pattern_id')
    status = Column(SmallInteger, server_default='0', nullable=False, comment='任务状态 0: 待执行 1:执行中 2：完成 3：失败')

    def to_dict(self):
        return {
            'id': self.id,
            'create_time': str(self.create_time),
            'update_time': str(self.update_time),
            'publish_plan_id': self.publish_plan_id,
            'step': self.step,
            'title': self.title,
            'note': self.note,
            'action': self.action,
            'status': self.status,
        }


class PublishPatternHost(TableMixin, BaseModel):
    __tablename__ = 'publish_pattern_host'

    publish_pattern_id = Column(Integer, server_default='0', nullable=False, comment='关联publish_pattern表id')
    publish_pattern = relationship(
        'PublishPattern',
        uselist=False,
        foreign_keys='PublishPattern.id',
        primaryjoin='PublishPatternHost.publish_pattern_id == PublishPattern.id')
    publish_host_id = Column(Integer, server_default='0', nullable=False, comment='关联publish_host表id')
    publish_host = relationship(
        'PublishHost',
        uselist=False,
        foreign_keys='PublishHost.id',
        primaryjoin='PublishPatternHost.publish_host_id == PublishHost.id')
    publish_pattern_tasks = relationship(
        'PublishPatternTask',
        uselist=True,
        foreign_keys='PublishPatternTask.publish_pattern_host_id',
        primaryjoin='PublishPatternTask.publish_pattern_host_id == PublishPatternHost.id')
    status = Column(SmallInteger, server_default='0', nullable=False, comment='任务状态 0: 待执行 1:执行中 2：完成 3：失败')

    def to_dict(self):
        return {
            'id': self.id,
            'create_time': str(self.create_time),
            'update_time': str(self.update_time),
            'publish_pattern_id': self.publish_pattern_id,
            'publish_pattern': self.publish_pattern.to_dict(),
            'publish_host_id': self.publish_host_id,
            'publish_host': self.publish_host.to_dict(),
            'publish_pattern_tasks': [t.to_dict() for t in self.publish_pattern_tasks],
            'status': self.status,
        }


class PublishPatternTask(TableMixin, BaseModel):
    __tablename__ = 'publish_pattern_task'

    publish_pattern_host_id = Column(Integer, server_default='0', nullable=False, comment='关联publish_pattern_host表id')
    publish_pattern_host = relationship(
        'PublishPatternHost',
        uselist=False,
        foreign_keys='PublishPatternHost.id',
        primaryjoin='PublishPatternTask.publish_pattern_host_id == PublishPatternHost.id')
    task_name = Column(String(128), server_default='', nullable=False, comment='任务名称')
    status = Column(SmallInteger, server_default='0', nullable=False, comment='任务状态 0: 待执行 1:执行中 2：完成 3：失败')

    def to_dict(self):
        return {
            'id': self.id,
            'create_time': str(self.create_time),
            'update_time': str(self.update_time),
            'publish_pattern_host_id': self.publish_pattern_host_id,
            'task_name': self.task_name,
            'status': self.status
        }
