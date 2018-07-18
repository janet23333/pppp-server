import yaml
import os
import sys

conf_dir = '/data/conf/publish-server'
settings_file_name = 'settings.yml'

if os.path.isdir(conf_dir):
    BASE_DIR = conf_dir
    sys.path.insert(0, conf_dir)
    import celery_config
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, settings_file_name), 'rb') as ymlfile:
    settings = yaml.load(ymlfile)
