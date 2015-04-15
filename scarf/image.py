import os
import imghdr
import uuid
import re
import datetime
from StringIO import StringIO
from PIL import Image
from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash, send_file
from werkzeug import secure_filename
from scarflib import check_login
from sql import upsert, doupsert, read, doselect, delete
from profile import get_userinfo
from scarflib import redirect_back, check_scarf, scarf_imgs, pagedata, get_imgupload, upload_dir
from main import page_not_found

@app.route('/image/<img_id>/reallydelete')
def reallydelete_image(img_id):
    pd = pagedata()

    if not pd.accesslevel >= 10:
        return redirect(url_for('accessdenied'))

    sql = read('images', **{"filename": escape(img_id)})
    result = doselect(sql)

    try:
        uuid = result[0][1]
        filename = result[0][2]
    except IndexError: 
        return page_not_found(404)

    sql = delete('scarfimg', **{"imgid": uuid})
    result = doselect(sql)

    sql = delete('images', **{"uuid": uuid})
    result = doselect(sql)

    sql = delete('imgmods', **{"imgid": uuid})
    result = doselect(sql)

    try:
        os.remove(upload_dir + filename)
    except:
        app.logger.error("Error removing image: " + escape(img_id))

        pd.title = "Error deleting image"
        pd.errortext = "Error deleting image " + escape(img_id)
        return render_template("error.html", pd=pd)

    pd.title=escape(img_id) + " has been deleted"
    pd.accessreq = 10
    pd.conftext = escape(img_id) + " has been deleted. I hope you meant to do that."
    pd.conftarget = ""
    pd.conflinktext = ""
    return render_template('confirm.html', pd=pd)

@app.route('/image/<img_id>/delete')
def delete_image(img_id):
    pd = pagedata()

    if not pd.accesslevel >= 10:
        return redirect(url_for('accessdenied'))

    pd.title=escape(img_id)

    pd.accessreq = 10
    pd.conftext = "Deleting image " + escape(img_id)
    pd.conftarget = "/image/" + escape(img_id) + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/image/upload', methods=['POST'])
def imageupload():
    if not check_login():
        flash('You must be logged in to upload a picture.')
        return redirect_back('/index')

    scarf = check_scarf(escape(request.form['scarfname']))
    if scarf == False:
        return redirect_back('/index')

    if request.method == 'POST':
        if request.form['tag'] == '':
            flash('Please add a tag for this picture.')
            return redirect_back('/index')

        if request.files['image'].filename == '':
            flash('Please upload something.')
            return redirect_back('/index')

        get_imgupload(request.files['image'], scarf[1], escape(request.form['tag']))

        flash('Image added to ' + escape(request.form['scarfname']))

    return redirect_back('/index')

def serve_pil_image(pil_img):
    img_io = StringIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

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

@app.route('/image/<image>/thumbnail')
def serve_thumb(image):
    img=Image.open(upload_dir + escape(image))
    img = resize(img, 800.0, 200.0)
    return serve_pil_image(img)

@app.route('/image/<image>/preview')
def serve_preview(image):
    img=Image.open(upload_dir + escape(image))
    img = resize(img, 800.0, 800.0)
    return serve_pil_image(img)
