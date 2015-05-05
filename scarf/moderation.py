from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import redirect_back, pagedata, upload_dir, siteimage, NoImage
from sql import doupsert, upsert, doquery, read, delete
from main import page_not_found

from PIL import Image
import random
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
def moderate():
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 10:
        return redirect(url_for('accessdenied'))

    sql = read('imgmods')
    result = doquery(sql)

    pd.mods = []

    for mod in result:
        try:
            imgid = mod[0]
            flag = mod[2]
            user = mod[3]
            if mod[1] == 0:
                sql = read('images', **{"uid": imgid})
                img = doquery(sql)[0]
                
                class mod:
                    pass

                mod.filename = img[2]
                mod.tag = img[3]
                mod.user = user
                mod.flag = flag
                pd.mods.append(mod)
        except IndexError:
            pd.title = "SQL error"
            pd.errortext = "SQL error"
            return render_template('error.html', pd=pd)

    pd.title = "Unmoderated images" 

    return render_template('moderation.html', pd=pd)

@app.route('/mod/ban/<user>')
def mod_ban_user(user):
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 255:
        return redirect(url_for('accessdenied'))

    pd.title="Banning user " + escape(user)

    pd.accessreq = 10 
    pd.conftext = "Banning user " + escape(user)
    pd.conftarget = "/admin/users/" + escape(user) + "/accesslevel/0"
    pd.conflinktext = "Yup, I'm sure."

    return render_template('confirm.html', pd=pd)

@app.route('/mod/image/<image>')
def mod_img(image):
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 10:
        return redirect(url_for('accessdenied'))

    try:
        sql = read('images', **{"filename": escape(image)})
        result = doquery(sql)
        modimg = siteimage(result[0][0])
    except NoImage:
        return page_not_found(404)

    pd.image = modimg

    sql = read('images', **{"filename": modimg.filename})
    result = doquery(sql)

    try:
        sql = read('imgmods', **{"imgid": modimg.uid})
        result = doquery(sql)
        
        pd.moduser = result[0][3]
    except IndexError:
        pd.title = "SQL error"
        pd.errortext = "SQL error"
        return render_template('error.html', pd=pd)

    im=Image.open(upload_dir + escape(image))
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
def mod_img_approve(imageid):
    pd = pagedata()

    try:
        modimg = siteimage(escape(imageid))
    except:
        flash('Error during moderation')
        return redirect(url_for('moderate'))

    if 'username' not in session or pd.authuser.accesslevel < 10:
        return redirect(url_for('accessdenied'))

    modimg.approve()

    return redirect(url_for('moderate'))
