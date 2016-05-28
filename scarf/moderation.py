from scarf import app
from core import redirect_back, SiteImage, NoImage, user_by_uid, doquery, read, Tree

from main import page_not_found, PageData
from access import check_mod

from flask import redirect, url_for, render_template, session, request, flash
 
#TODO: finish sql cleanup

@app.route('/mod')
@check_mod
def moderate():
    pd = PageData()

    sql = read('imgmods')
    result = doquery(sql)

    pd.mods = []

    pd.tags = Tree('tags')

    for mod in result:
        try:
            imgid = mod[0]
            flag = mod[2]
            user = mod[3]

            if user is None:
                user = 'Anonymous'
            else:
                user = user_by_uid(user)

            if mod[1] == 0 or flag == 1:
                sql = 'select tag from images where uid = %(uid)s;'
                img = doquery(sql, {"uid": imgid})
                
                class Mod:
                    pass
                mod = Mod()

                if img:
                    mod.uid = imgid
                    mod.tag = img[0][0]
                    mod.user = user
                    mod.flag = flag
                    pd.mods.append(mod)
                else:
                    flash('Error loading data for image ' + str(imgid))
        except IndexError as e:
            pd.title = "SQL error"
            pd.errortext = "SQL error"
            return render_template('error.html', pd=pd)

    pd.title = "Unmoderated images" 

    return render_template('moderation.html', pd=pd)

@app.route('/mod/ban/<user>')
@check_mod
def mod_ban_user(user):
    pd = PageData()

    pd.title="Banning user " + user

    pd.accessreq = 10 
    pd.conftext = "Banning user " + user
    pd.conftarget = "/admin/users/" + user + "/accesslevel/0"
    pd.conflinktext = "Yup, I'm sure."

    return render_template('confirm.html', pd=pd)

@app.route('/mod/image/<image>/<scale>')
@app.route('/mod/image/<image>')
@check_mod
def mod_img(image, scale=2):
    pd = PageData()
    pd.scale = float(scale)

    try:
        modimg = SiteImage.create(image)
    except NoImage:
        return page_not_found()

    pd.image = modimg

    try:
        sql = 'select uid name from items where uid = %(uid)s;'
        pd.parent = doquery(sql, {"uid": modimg.parent})[0][0]

        sql = 'select * from imgmods where imgid = %(uid)s;'
        result = doquery(sql, {"uid": modimg.uid})

        if result[0][3] is None:
            user = 'Anonymous'
        else:
            user = user_by_uid(result[0][3])
        
        pd.moduser = user
    except IndexError:
        return page_not_found()

    pd.ascii = SiteImage.create(modimg.uid).ascii(scale=pd.scale)

    return render_template('mod_img.html', pd=pd)

@app.route('/mod/image/<imageid>/approve')
@check_mod
def mod_img_approve(imageid):
    pd = PageData()

    try:
        modimg = SiteImage.create(imageid)
    except NoImage:
        flash('Error during moderation')
        return redirect(url_for('moderate'))

    modimg.approve()

    return redirect(url_for('moderate'))
