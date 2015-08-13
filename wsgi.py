#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"//srv/data/web/vhosts/default/scarf")

from scarf import app as application
