from flask import Flask

app = Flask(__name__)

import scarf.main
import scarf.sql
import scarf.image
import scarf.scarves
import scarf.ownwant
import scarf.user
import scarf.profile
import scarf.admin
import scarf.moderation
