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

def serve_pil_image(pil_img):
    img_io = StringIO()

    pil_img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/fbimage/<img_id>')
def facebook_image(img_id):
    try:
        logger.info('fbimage URL called for imgid {}'.format(img_id))
        simg = SiteImage.create(img_id)
        image_string = cStringIO.StringIO(base64.b64decode(simg.image()))
        img = Image.open(image_string)

        hsize = img.size[0]
        vsize = img.size[1]
 
        aspect = img.size[0] / img.size[1]
        newvsize = int((aspect - 1.91) * img.size[1])
        print aspect
        print vsize
        print hsize
        print newvsize

        img_size = img.size
        fbimg_size = (img.size[0], newvsize)

        fbimg = Image.new("RGBA", fbimg_size, (255, 255, 255, 255))
        fbimg.paste(img, (0, (fbimg_size[1]-img.size[1])/2))

        return serve_pil_image(fbimg)
    except (IOError, NoImage, ValueError):
        return page_not_found()
