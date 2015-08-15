from StringIO import StringIO
from PIL import Image
from scarf import app
from flask import redirect, url_for, request, render_template, session, flash, send_file
from scarflib import redirect_back, pagedata, siteimage, siteitem, NoItem, NoImage, new_img
from main import page_not_found
from debug import dbg

from memoize import memoize_with_expiry, cache_persist, long_cache_persist
from config import upload_dir

@app.route('/newimg', methods=['GET', 'POST'], defaults={'debug': False})
@app.route('/newimg/debug', methods=['GET'], defaults={'debug': True})
def newimg(debug):
    pd = pagedata()
    if request.method == 'POST':
        if request.form['title'] == '':
            # todo: re fill form
            flash('No name?')
            return redirect(url_for('newimg'))

        if 'username' in session:
            uid = pd.authuser.uid
        else:
            uid = 0 

        if 'img' in request.files:
            img = new_img(request.files['img'], request.form['title'])

            if img:
                flash('Uploaded image!')
                return redirect('/image/' + str(img))

    pd.title="Add New Item"

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('newimg.html', pd=pd)

@app.route('/image/<img_id>/reallydelete')
def reallydelete_image(img_id):
    pd = pagedata()

    if not pd.authuser.accesslevel >= 10:
        return redirect(url_for('accessdenied'))

    delimg = siteimage.create(img_id)
    delimg.delete()

    app.logger.info(delimg.filename + " has been deleted by " + pd.authuser.username)
    pd.title = delimg.filename + " has been deleted"
    pd.accessreq = 10
    pd.conftext = delimg.filename + " has been deleted. I hope you meant to do that."
    pd.conftarget = ""
    pd.conflinktext = ""
    return render_template('confirm.html', pd=pd)

@app.route('/image/<img_id>/delete')
def delete_image(img_id):
    pd = pagedata()

    if not pd.authuser.accesslevel >= 10:
        return redirect(url_for('accessdenied'))

    delimg = siteimage.create(img_id)

    pd.title=delimg.filename

    pd.accessreq = 10
    pd.conftext = "Deleting image " + delimg.filename
    pd.conftarget = "/image/" + img_id + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/image/<img_id>/flag')
def flag_image(img_id):
    pd = pagedata()

    flagimg = siteimage.create(img_id)
    flagimg.flag()

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

# TODO: add to db, get off of local FS
# todo: caching
img_cache = dict()

@app.route('/image/<img_id>/full')
def serve_full(img_id):
    try:
        simg = siteimage.create(img_id)

        img=Image.open(upload_dir + '/' + simg.filename)
        return serve_pil_image(img)
    except IOError:
        return page_not_found(404)

@app.route('/image/<img_id>/thumbnail')
def serve_thumb(img_id):
    try:
        simg = siteimage.create(img_id)

        img=Image.open(upload_dir + '/' + simg.filename)
        img = resize(img, 800.0, 200.0)
        return serve_pil_image(img)
    except IOError:
        return page_not_found(404)

@app.route('/image/<img_id>/preview')
def serve_preview(img_id):
    try:
        simg = siteimage.create(img_id)

        img=Image.open(upload_dir + '/' + simg.filename)
        img = resize(img, 800.0, 800.0)
        return serve_pil_image(img)
    except IOError:
        return page_not_found(404)

@app.route('/image/<img_id>', defaults={'debug': False})
@app.route('/image/<img_id>/debug', defaults={'debug': True})
def show_image(img_id, debug):
    pd = pagedata()

    try:
        pd.img = siteimage.create(img_id)
        pd.title=pd.img.tag
    except NoImage:
        return page_not_found(404)

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('image.html', pd=pd)
