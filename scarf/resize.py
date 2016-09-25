from scarf import app
from core import SiteImage, NoImage
from main import page_not_found, PageData
import core

from StringIO import StringIO
from PIL import Image
from flask import send_file
import logging
import base64
import cStringIO

logger = logging.getLogger(__name__)

""" image resizing is implemented via nginx on hosted instances, this stuff is just for dev """

def serve_pil_image(pil_img):
    img_io = StringIO()

    pil_img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

def resize(image_string, maxwidth, maxheight):
    img = Image.open(image_string)
    hsize = float(img.size[0])
    vsize = float(img.size[1])
    factor = float(1)
    hfactor = float(1)
    vfactor = float(1)

    if hsize > maxwidth:
        if vsize < hsize:
            hfactor = maxheight / vsize
        else:
            hfactor = maxwidth / hsize

    if vsize > maxheight:
        if vsize > hsize:
            vfactor = maxheight / vsize
        else:
            vfactor = maxwidth / hsize

    if vfactor < hfactor:
        factor = vfactor
    else:
        factor = hfactor

    if factor < 1:
        newh = int(hsize * factor)
        newv = int(vsize * factor)
    else:
        newh = int(hsize / factor)
        newv = int(vsize / factor)

    return img.resize((newh, newv), Image.ANTIALIAS)

@app.route('/resize/<size>/<img_id>')
def resize_image(size, img_id):
    try:
        logger.info('resize fallback URL called for imgid {} - {}'.format(img_id, size))
        simg = SiteImage.create(img_id)
        image_string = cStringIO.StringIO(base64.b64decode(simg.image()))
        (x, y) = size.split('x')
        img = resize(image_string, float(x), float(y))
        return serve_pil_image(img)
    except (IOError, NoImage, ValueError):
        return page_not_found()
