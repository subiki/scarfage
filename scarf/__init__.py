from flask import Flask

app = Flask(__name__)

import scarf.main
import scarf.user
import scarf.scarves
import scarf.sql
import scarf.profile
import scarf.ownwant
