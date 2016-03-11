#!/usr/bin/env python

from scarf import app
import logging

logging.basicConfig(level=logging.DEBUG)

app.run(host='0.0.0.0', debug=True)
