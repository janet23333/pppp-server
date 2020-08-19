# xxxx

### 简介

* python3
* celery 4
* tornado
* SQLAlchemy

### 初始化

```bash
# 安装依赖
pip3 install -r requirements.txt

# 创建配置文件

/conf/settings.yml

# 初始化数据库
python3 bin/init_db.py

# 启动程序
python3 publish-server.py
```

### 数据库变更


如果没有之前的revision file，需要先清空表：alembic_version 。

```bash
alembic revision --autogenerate -m "modify info"

alembic upgrade head
```

### 启动celery

```bash
export PYTHONOPTIMIZE=1 && celery worker -A celery_worker -l info -P eventlet
```

### 测试

### ansibe +celery 结果为空
有两种方法解决这个问题，就是关闭assert：
* 1.在celery 的worker启动窗口设置export PYTHONOPTIMIZE=1或打开celery这个参数-O OPTIMIZATION
* 2.注释掉python包multiprocessing下面process.py中102行，关闭assert

#### 登录

* POST： http://localhost:8888/api/token

#### celery

* GET：http://localhost:8888/api/test?h=ello
