
# Hack for model import
import os
import sys
sys.path.insert(0, os.path.realpath("."))
from orm.db import Engine
from orm.models import BaseModel

if __name__ == "__main__":
    BaseModel.metadata.create_all(Engine)
