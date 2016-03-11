from scarf import app
from core import redirect_back, SiteImage, SiteItem, NoItem, NoImage, new_img, latest_items, memoize_with_expiry, cache_persist, long_cache_persist
from main import page_not_found, PageData
import core

from StringIO import StringIO
from PIL import Image
from flask import make_response, redirect, url_for, request, render_template, session, flash, send_file

import base64
import cStringIO

from access import check_mod

@app.route('/newimg', methods=['POST'])
def newimg():
    pd = PageData()
    if request.method == 'POST':
        if request.form['title'] == '':
            title = "(untitled)"
        else:
            title = request.form['title']

        if 'username' in session:
            userid = pd.authuser.uid
        else:
            userid = None

        if 'img' in request.files:
            img = new_img(request.files['img'], title, request.form['parent'], userid, request.remote_addr)

            if img:
                flash('Uploaded ' + request.files['img'].filename)
                return redirect_back('/image/' + str(img))
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

#    pil_img.save(img_io, 'JPEG', quality=70)
#    img_io.seek(0)
#    return send_file(img_io, mimetype='image/jpeg')

#TODO this is broken, I hate it
def resize(img, maxwidth, maxheight):
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

@app.route('/image/<img_id>/thumbnail')
def serve_thumb(img_id):
    try:
        simg = SiteImage.create(img_id)
        image_string = cStringIO.StringIO(base64.b64decode(simg.image))
        img = Image.open(image_string)
        img = resize(img, 800.0, 200.0)
        return serve_pil_image(img)
    except (IOError, NoImage):
        return page_not_found(404)

@app.route('/image/<img_id>/preview')
def serve_preview(img_id):
    try:
        simg = SiteImage.create(img_id)
        image_string = cStringIO.StringIO(base64.b64decode(simg.image))
        img = Image.open(image_string)
        img = resize(img, 800.0, 800.0)
        return serve_pil_image(img)
    except (IOError, NoImage):
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
