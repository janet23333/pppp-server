import re
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy import orm
from tornado.log import app_log

from conf import settings

DB_URL = settings['database_url']

db_kwargs = settings['database_config']
# db_kwargs.update({'echo': True})
Engine = create_engine(DB_URL, **db_kwargs)

SESSION_MAKER = orm.sessionmaker(bind=Engine, autoflush=False)


class DBError(Exception):
    pass


def init():
    app_log.info('init mysql')


Filed = re.compile(r'(has no property) (.*)')


@contextmanager
def session_scope():
    session = SESSION_MAKER()
    try:
        yield session
        session.commit()
    except exc.IntegrityError as e:
        session.rollback()
        raise DBError(str(e))
    except orm.exc.NoResultFound as e:
        session.rollback()
        raise DBError(str(e))
    except exc.InvalidRequestError as e:

        error_info = e.args[0]
        value = Filed.search(error_info)
        if value:
            value = value.group(2)
            reason = "InvalidRequestError, arguments %s is not allowed" % value
        else:
            app_log.error(str(e))
            reason = "InvalidRequestError, please check your request arguments"
        session.rollback()
        raise DBError(reason)
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
