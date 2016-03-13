from scarf import app
from core import redirect_back, SiteImage, SiteItem, NoItem, NoImage, new_img, latest_items, memoize_with_expiry, cache_persist, long_cache_persist
from main import page_not_found, PageData
from access import check_mod
import core

from StringIO import StringIO
from PIL import Image
from flask import make_response, redirect, url_for, request, render_template, session, flash, send_file
import logging
import base64
import cStringIO

logger = logging.getLogger(__name__)

@app.route('/newimg', methods=['POST'])
def newimg():
    pd = PageData()
    if request.method == 'POST':
        if 'img' in request.files:
            if request.form['title'] == '':
                title = request.files['img'].filename
            else:
                title = request.form['title']

            if 'username' in session:
                userid = pd.authuser.uid
            else:
                userid = None

            img = new_img(request.files['img'], title, request.form['parent'], userid, request.remote_addr)

            if img:
                flash('Uploaded {}'.format(request.files['img'].filename))
                return redirect_back('/image/' + str(img))
            else:
                flash('An error occurred while processing {}'.format(request.files['img'].filename))

        return redirect_back(url_for('index'))

@app.route('/image/<img_id>/reallydelete')
@check_mod
def reallydelete_image(img_id):
    pd = PageData()

    delimg = SiteImage.create(img_id)
    delimg.delete()

    pd.title = delimg.tag + " has been deleted"
    pd.accessreq = 10
    pd.conftext = delimg.tag + " has been deleted. I hope you meant to do that."
    pd.conftarget = ""
    pd.conflinktext = ""
    return render_template('confirm.html', pd=pd)

@app.route('/image/<img_id>/delete')
@check_mod
def delete_image(img_id):
    pd = PageData()

    delimg = SiteImage.create(img_id)

    pd.title=delimg.tag

    pd.accessreq = 10
    pd.conftext = "Deleting image " + delimg.tag
    pd.conftarget = "/image/" + img_id + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/image/<img_id>/flag')
def flag_image(img_id):
    pd = PageData()

    flagimg = SiteImage.create(img_id)
    if 'username' in session:
        userid = core.uid_by_user(session['username'])
    else:
        userid = None

    flagimg.flag(userid)

    flash("The image has been flagged and will be reviewed by a moderator.")

    return redirect_back('index') 

def serve_pil_image(pil_img):
    img_io = StringIO()

    pil_img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

def resize(image_string, maxwidth, maxheight):
    img = Image.open(image_string)
    hsize = img.size[0]
    vsize = img.size[1]
    factor = 1

    if hsize > maxwidth or vsize > maxheight:
        hfactor = 1
        if hsize > maxwidth:
            if vsize < hsize:
                hfactor = maxheight / vsize
            else:
                hfactor = maxwidth / hsize

        vfactor = 1
        if vsize > maxheight:
            if vsize > hsize:
                vfactor = maxheight / vsize
            else:
                vfactor = maxwidth / hsize

        if vfactor < hfactor:
            factor = vfactor
        else:
            factor = hfactor

    return img.resize((int(hsize * factor), int(vsize * factor)), Image.ANTIALIAS)

@app.route('/image/<img_id>/full')
def serve_full(img_id):
    try:
        simg = SiteImage.create(img_id)

        resp = make_response(base64.b64decode(simg.image))
        resp.content_type = "image/png"
        return resp
    except (IOError, NoImage):
        return page_not_found(404)

@app.route('/resize/<size>/<img_id>')
def resize_image(size, img_id):
    try:
        logger.info('resize fallback URL called for imgid {} - {}'.format(img_id, size))
        simg = SiteImage.create(img_id)
        image_string = cStringIO.StringIO(base64.b64decode(simg.image))
        (x, y) = size.split('x')
        img = resize(image_string, float(x), float(y))
        return serve_pil_image(img)
    except (IOError, NoImage, ValueError):
        return page_not_found(404)

@app.route('/image/<img_id>')
def show_image(img_id):
    pd = PageData()

    try:
        pd.img = SiteImage.create(img_id)
        pd.title=pd.img.tag
    except NoImage:
        return page_not_found(404)

    return render_template('image.html', pd=pd)
