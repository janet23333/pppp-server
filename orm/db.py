import re
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy import orm
from tornado.log import app_log

from conf import settings
from tornado.web import HTTPError

DB_URL = settings['database_url']

db_kwargs = settings['database_config']
# db_kwargs.update({'echo': True})
Engine = create_engine(DB_URL, **db_kwargs)

SESSION_MAKER = orm.sessionmaker(bind=Engine, autoflush=False)


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
        raise HTTPError(status_code=400, reason=str(e))
    except orm.exc.NoResultFound as e:
        session.rollback()
        raise HTTPError(status_code=404, reason=str(e))
    except exc.InvalidRequestError as e:

        error_info = e.args[0]
        value = Filed.search(error_info)
        if value:
            value = value.group(2)
            reason = "InvalidRequestError, arguments %s is not allowed" % value
        else:
            reason = "InvalidRequestError, please check your request arguments"
        session.rollback()
        raise HTTPError(status_code=400, reason=reason)
    except Exception as e:
        session.rollback()
        raise HTTPError(status_code=400, reason=str(e))
    finally:
        session.close()
