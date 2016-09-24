from flask import Flask

app = Flask(__name__)

import scarf.main
import scarf.image
import scarf.resize
import scarf.items
import scarf.ownwant
import scarf.profile
import scarf.admin
import scarf.moderation
import scarf.user
import scarf.trade
import scarf.pm
import scarf.tags
import scarf.stats
import scarf.fbimage
