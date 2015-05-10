from StringIO import StringIO
from PIL import Image
from scarf import app
from flask import redirect, url_for, request, render_template, session, escape, flash, send_file
from scarflib import redirect_back, pagedata, siteimage, siteitem, NoItem, NoImage
from main import page_not_found

from config import upload_dir

@app.route('/image/<img_id>/reallydelete')
def reallydelete_image(img_id):
    pd = pagedata()

    if not pd.authuser.accesslevel >= 10:
        return redirect(url_for('accessdenied'))

    delimg = siteimage(escape(img_id))
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

    delimg = siteimage(escape(img_id))

    pd.title=escape(delimg.filename)

    pd.accessreq = 10
    pd.conftext = "Deleting image " + delimg.filename
    pd.conftarget = "/image/" + escape(img_id) + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/image/<img_id>/flag')
def flag_image(img_id):
    pd = pagedata()

    flagimg = siteimage(escape(img_id))
    flagimg.flag()

    flash("The image has been flagged and will be reviewed by a moderator.")

    return redirect_back('index') 

@app.route('/image/upload', methods=['POST'])
def imageupload():
    try:
        item = siteitem(escape(request.form['itemname']))
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

        # TODO support upload from URL

        if item.newimg(request.files['image'], escape(request.form['tag'])):
            flash('Image added to ' + escape(request.form['itemname']))

    return redirect_back('/index')

def serve_pil_image(pil_img):
    img_io = StringIO()

    pil_img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

# for whatever reason the above works with both PNGs and JPEGs

#    pil_img.save(img_io, 'JPEG', quality=70)
#    img_io.seek(0)
#    return send_file(img_io, mimetype='image/jpeg')

def resize(img, box, fit):
    #preresize image with factor 2, 4, 8 and fast algorithm
    factor = 1
    while img.size[0]/factor > 2*box[0] and img.size[1]*2/factor > 2*box[1]:
        factor *=2
    if factor > 1:
        img.thumbnail((img.size[0]/factor, img.size[1]/factor), Image.NEAREST)

    #calculate the cropping box and get the cropped part
    if fit:
        x1 = y1 = 0
        x2, y2 = img.size
        wRatio = 1.0 * x2/box[0]
        hRatio = 1.0 * y2/box[1]
        if hRatio > wRatio:
            y1 = int(y2/2-box[1]*wRatio/2)
            y2 = int(y2/2+box[1]*wRatio/2)
        else:
            x1 = int(x2/2-box[0]*hRatio/2)
            x2 = int(x2/2+box[0]*hRatio/2)
        img = img.crop((x1,y1,x2,y2))

    #Resize the image with best quality algorithm ANTI-ALIAS
    img.resize(box, Image.ANTIALIAS)

    return img

@app.route('/image/<image>/thumbnail')
def serve_thumb(image):
    try:
        img=Image.open(upload_dir + escape(image))
        img = resize(img, (600, 150), True)
        return serve_pil_image(img)
    except:
        return page_not_found(404)

@app.route('/image/<image>/preview')
def serve_preview(image):
    try:
        img=Image.open(upload_dir + escape(image))
        img = resize(img, (800, 800), True)
        return serve_pil_image(img)
    except:
        return page_not_found(404)

@app.route('/image/<img_id>')
def show_image(img_id):
    pd = pagedata()

    try:
        pd.img = siteimage(escape(img_id))
        pd.title=escape(pd.img.tag)
    except NoImage:
        return page_not_found(404)

    return render_template('image.html', pd=pd)
