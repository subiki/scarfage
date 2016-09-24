from scarf import app
from core import redirect_back, SiteImage, NoImage, new_img
from main import page_not_found, PageData
from access import check_mod
import core

from flask import make_response, url_for, request, render_template, session, flash
import logging
import base64

logger = logging.getLogger(__name__)

@app.route('/newimg', methods=['POST'])
def newimg():
    """
    :URL: /newimg
    :Method: POST

    Upload a new image. 
    """
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

@app.route('/image/<img_id>/reparent', methods=['POST'])
@check_mod
def reparent(img_id):
    """
    :URL: /reparent
    :Method: POST

    Reparent an image. 
    """
    pd = PageData()
    if request.method == 'POST':
        newid = request.form['parent']

        try:
            img = core.SiteImage.create(img_id)
            item = core.SiteItem.create(newid)
        except (core.NoItem, core.NoImage):
            return page_not_found()
            

        if img:
            img.reparent(newid)
            return redirect_back('/image/' + str(img))
        else:
            flash('Unable to reparent {}'.format(img_id))

        return redirect_back(url_for('index'))

@app.route('/image/<img_id>/reallydelete')
@check_mod
def reallydelete_image(img_id):
    """
    :URL: /image/<img_id>/reallydelete

    Actually delete an image
    """

    pd = PageData()

    try:
        delimg = SiteImage.create(img_id)
        delimg.delete()
    except NoImage:
        return page_not_found()

    pd.title = delimg.tag + " has been deleted"
    pd.accessreq = 10
    pd.conftext = delimg.tag + " has been deleted. I hope you meant to do that."
    pd.conftarget = ""
    pd.conflinktext = ""
    return render_template('confirm.html', pd=pd)

@app.route('/image/<img_id>/delete')
@check_mod
def delete_image(img_id):
    """
    :URL: /image/<img_id>/delete

    Redirect to a confirmation page to make sure you want to delete an image.

    .. todo:: This should be re-done in javascript.
    """

    pd = PageData()

    try:
        delimg = SiteImage.create(img_id)
    except NoImage:
        return page_not_found()

    pd.title=delimg.tag

    pd.accessreq = 10
    pd.conftext = "Deleting image " + delimg.tag
    pd.conftarget = "/image/" + img_id + "/reallydelete"
    pd.conflinktext = "Yup, I'm sure"

    return render_template('confirm.html', pd=pd)

@app.route('/image/<img_id>/flag')
def flag_image(img_id):
    """
    :URL: /image/<img_id>/flag

    Flag an image for review by a moderator.

    .. todo:: Add support for a note and record who flagged it.
    """

    pd = PageData()

    try:
        flagimg = SiteImage.create(img_id)
        flagimg.flag()
    except NoImage:
        return page_not_found()

    flash("The image has been flagged and will be reviewed by a moderator.")

    return redirect_back('index') 

@app.route('/image/<img_id>/full')
def serve_full(img_id):
    """
    :URL: /image/<img_id>/full

    Retrieve the raw image and return it.
    """

    try:
        simg = SiteImage.create(img_id)

        resp = make_response(base64.b64decode(simg.image()))
        resp.content_type = "image/png"
        return resp
    except (IOError, NoImage):
        return page_not_found()

@app.route('/image/<img_id>')
def show_image(img_id):
    """
    :URL: /image/<img_id>

    Render a template for viewing an image.
    """

    pd = PageData()

    try:
        pd.img = SiteImage.create(img_id)
        pd.title=pd.img.tag
    except NoImage:
        return page_not_found()

    return render_template('image.html', pd=pd)
