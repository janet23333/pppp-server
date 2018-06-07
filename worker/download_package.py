import requests
from common.util import run_shell
from conf import settings
import os
from tornado.log import app_log
urls = """
canyin.zip http://git.ops.yunnex.com/deployment/packages/raw/2c096873d551d9ce82544be5921018fe747959a9/canyin.zip
linesvr-mod-service.zip http://git.ops.yunnex.com/deployment/packages/raw/9ba23a84118e12d428834a69dc48d0d450b8f11e/linesvr-mod-service.zip
linesvr-web-mobile.zip http://git.ops.yunnex.com/deployment/packages/raw/e47ce80205f71759b1dd854d83d7cef8faa0b538/linesvr-web-mobile.zip
saofu-mobile.zip http://git.ops.yunnex.com/deployment/packages/raw/5a15dea6949fc308481523c6cee56100198176b5/saofu-mobile.zip
saofu-mod-broker.zip http://git.ops.yunnex.com/deployment/packages/raw/62e94eb83a644dae209c0cbbd8f427f0775373a3/saofu-mod-broker.zip
wxapp-mod-auth.zip http://git.ops.yunnex.com/deployment/packages/raw/235abaf261a24f814396760bb36bbaf13094ac07/wxapp-mod-auth.zip
"""

download_package_path = settings['download_package_path']


def package(jenkins_url, inventory):
    package_path = '{}/{}'.format(download_package_path, inventory)
    app_log.info('package_path is {}'.format(package_path))
    if not os.path.exists(package_path):
        app_log.info('not exit {} :'.format(package_path))
        os.makedirs(package_path)
    result = run_shell('rm -rf {}/*.zip'.format(package_path))
    if result.startswith('error'):
        return 'error: {}'.format(result)
    for url in jenkins_url:
        r = requests.get(url)
        file_name = url.split('/')[-1]
        app_log.info('file_name is {}'.format(file_name))

        save_file_path = '{}/{}'.format(package_path, file_name)
        app_log.info('save_file_path is {}'.format(save_file_path))
        if r.status_code == 200:
            with open(save_file_path, 'wb') as _file:
                _file.write(r.content)
        else:
            return 'error {} {} download failed'.format(file_name, url)
    return 'ok'
