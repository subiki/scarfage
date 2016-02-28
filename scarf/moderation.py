from scarf import app
from flask import redirect, url_for, render_template, session, request, flash
from scarflib import redirect_back, pagedata, siteimage, NoImage, user_by_uid
from sql import doquery, read, Tree
from main import page_not_found
from debug import dbg

from access import check_mod
 
from PIL import Image
import cStringIO
import random
import base64
from bisect import bisect


zonebounds=[36,72,108,144,180,216,252]
greyscale = [
            " ",
            " ",
            ".,-",
            "_ivc=!/|\\~",
            "gjez2]/(YL)t[+T7Vf",
            "mdKbNDXY5P*Q",
            "W8KMA",
            "#%$"
            ]

@app.route('/mod')
@check_mod
def moderate():
    pd = pagedata()

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
                sql = 'select * from images where uid = %(uid)s;'
                img = doquery(sql, {"uid": imgid})
                
                class mod:
                    pass

                if img:
                    mod.uid = imgid
                    mod.tag = img[0][1]
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
    pd = pagedata()

    pd.title="Banning user " + user

    pd.accessreq = 10 
    pd.conftext = "Banning user " + user
    pd.conftarget = "/admin/users/" + user + "/accesslevel/0"
    pd.conflinktext = "Yup, I'm sure."

    return render_template('confirm.html', pd=pd)

@app.route('/mod/image/<image>')
@check_mod
def mod_img(image):
    pd = pagedata()

    modimg = siteimage.create(image)
    try:
        modimg = siteimage.create(image)
    except NoImage:
        return page_not_found(404)

    pd.image = modimg

    sql = 'select uid name from items where uid = %(uid)s;'
    pd.parent = doquery(sql, {"uid": modimg.parent})[0][0]

    try:
        sql = 'select * from imgmods where imgid = %(uid)s;'
        result = doquery(sql, {"uid": modimg.uid})

        if result[0][3] is None:
            user = 'Anonymous'
        else:
            user = user_by_uid(result[0][3])
        
        pd.moduser = user
    except IndexError:
        pd.title = "SQL error"
        pd.errortext = "SQL error"
        return render_template('error.html', pd=pd)

    simg = siteimage.create(modimg.uid)
    image_string = cStringIO.StringIO(base64.b64decode(simg.image))
    im = Image.open(image_string)
    basewidth = 100
    wpercent = (basewidth/float(im.size[0]))
    hsize = int((float(im.size[1])*float(wpercent))) / 2
    im=im.resize((basewidth,hsize), Image.ANTIALIAS)
    im=im.convert("L") # convert to mono

    ascii=""
    for y in range(0,im.size[1]):
        for x in range(0,im.size[0]):
            lum=255-im.getpixel((x,y))
            row=bisect(zonebounds,lum)
            possibles=greyscale[row]
            ascii=ascii+possibles[random.randint(0,len(possibles)-1)]
        ascii=ascii+"\n"

    pd.ascii = ascii

    return render_template('mod_img.html', pd=pd)

@app.route('/mod/image/<imageid>/approve')
@check_mod
def mod_img_approve(imageid):
    pd = pagedata()

    try:
        modimg = siteimage.create(imageid)
    except:
        flash('Error during moderation')
        return redirect(url_for('moderate'))

    modimg.approve()

    return redirect(url_for('moderate'))
