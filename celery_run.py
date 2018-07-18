#!/data/env/python36publish_server/bin/python -O

# -*- coding: utf-8 -*-
import re
import sys

from celery.__main__ import main
from conf import settings

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


if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
