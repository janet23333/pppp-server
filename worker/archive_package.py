from conf import settings
from common.util import run_shell
sh_path = settings['sh_path']
download_package_path = settings['download_package_path']


def archive_package(filename):
    package_path = '{}/{}'.format(download_package_path, filename)
    sh_file = 'sh {}/archive_package.sh {} {}'.format(sh_path, package_path, filename)
    result = run_shell(sh_file)
    if result.startswith('error'):
        return result
    index_file = result.strip().split('\n')[0].split()[-1]
    application_list = []
    with open(index_file) as file:
        for line in file.readlines():
            application_name = line.split()[0]
            target_version = line.split()[1]
            app_dict = {'target_version': target_version, 'application_name': application_name}
            application_list.append(app_dict)
    result = run_shell('rm -rf {}'.format(package_path))
    if result.startswith('error'):
        return 'error: {}'.format(result)
    return application_list


