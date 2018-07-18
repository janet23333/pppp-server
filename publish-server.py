import os
import tornado.ioloop
import tornado.web
from tornado.log import app_log
from tornado.options import define
from tornado.options import options

from conf import settings

server_config = settings['server']

# IDE 远程调试
try:
    if settings['remote_debug']:
        print('debug')
        import ptvsd

        # Allow other computers to attach to ptvsd at this IP address and port, using the secret
        ptvsd.enable_attach("my_secret", address=('10.10.50.30', 10088))

        # Pause the program until a remote debugger is attached
        ptvsd.wait_for_attach()
except Exception as e:
    print(str(e))
    pass


def conf_log():
    define(
        'port',
        default=server_config['port'],
        help='running on the given port',
        type=int)

    options.parse_command_line(final=False)

    # log rotate by time (day), max save 30 files
    options.log_rotate_mode = 'time'
    options.log_file_num_backups = 30
    options.logging = 'debug' if settings['debug'] else 'info'
    options.log_to_stderr = settings['debug']
    options.log_file_prefix = '{}/{}.log'.format(server_config['log_path'],
                                                 options.port)

    options.run_parse_callbacks()

    app_log.info('publish Server Listening:{} Started'.format(options.port))

    # # 设置数据库log
    # if settings['debug']:
    #     logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)


def init_db():
    from orm import db
    db.init()


def main():
    conf_log()

    init_db()

    from routes import ROUTES
    app = tornado.web.Application(ROUTES, debug=settings['debug'])
    app.listen(
        options.port,
        address='0.0.0.0',
        xheaders=True,
        decompress_request=True)

    portal_pid = os.path.join(server_config['run_path'], 'p_{}.pid'.format(
        options.port))
    app_log.info("publish is starting on %s" % os.getpid())

    with open(portal_pid, 'w') as f:
        f.write('{}'.format(os.getpid()))

    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
