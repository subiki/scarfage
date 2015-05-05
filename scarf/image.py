#import os
#import imghdr
#import uuid
#import re
#import datetime

from StringIO import StringIO
from PIL import Image
from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash, send_file
from scarflib import redirect_back, pagedata, siteimage, upload_dir, siteitem, NoItem

@app.route('/image/<img_id>/reallydelete')
def reallydelete_image(img_id):
    pd = pagedata()

    if not pd.authuser.accesslevel >= 10:
        return redirect(url_for('accessdenied'))

    delimg = siteimage(escape(img_id))
    delimg.delete()

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

    delimg = siteimage(escape(img_id))

    pd.title=escape(delimg.filename)

    pd.accessreq = 10
    pd.conftext = "Deleting image " + delimg.filename
    pd.conftarget = "/image/" + escape(img_id) + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/image/upload', methods=['POST'])
def imageupload():
    try:
        item = siteitem(escape(request.form['scarfname']))
    except NoItem:
        flash('Error uploading image')
        return redirect_back('/index')

    if request.method == 'POST':
        if request.form['tag'] == '':
            flash('Please add a tag for this picture.')
            return redirect_back('/index')

        if request.files['image'].filename == '':
            flash('Please upload something.')
            return redirect_back('/index')

        item.newimg(request.files['image'], escape(request.form['tag']))

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
