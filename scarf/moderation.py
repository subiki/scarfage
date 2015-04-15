from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import check_login, redirect_back, pagedata, get_userinfo, upload_dir
from sql import doupsert, upsert, doselect, read, delete

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

    if 'username' not in session or pd.accesslevel < 10:
        return redirect(url_for('accessdenied'))

    sql = read('imgmods')
    result = doselect(sql)

    pd.mods = []

    for mod in result:
        try:
            uuid = mod[0]
            flag = mod[2]
            user = mod[3]
            if mod[1] == 0:
                sql = read('images', **{"uuid": uuid})
                img = doselect(sql)[0]
                app.logger.debug(img)
                
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

    if 'username' not in session or pd.accesslevel < 255:
        return redirect(url_for('accessdenied'))

    if get_userinfo(escape(user))[0][8] == 0:
        flash('User has been banned')
        return redirect(url_for('moderate'))

    pd.title="Banning user " + escape(user)

    pd.accessreq = 10 
    pd.conftext = "Banning user " + escape(user)
    pd.conftarget = "/admin/users/" + escape(user) + "/accesslevel/0"
    pd.conflinktext = "Yup, I'm sure."

    return render_template('confirm.html', pd=pd)

@app.route('/mod/image/<image>')
def mod_img(image):
    pd = pagedata()

    if 'username' not in session or pd.accesslevel < 10:
        return redirect(url_for('accessdenied'))

    pd.filename = escape(image)

    sql = read('images', **{"filename": pd.filename})
    result = doselect(sql)

    try:
        pd.uuid = result[0][1]

        sql = read('imgmods', **{"imgid": pd.uuid})
        result = doselect(sql)
        app.logger.debug(result[0])
        
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

    if 'username' not in session or pd.accesslevel < 10:
        return redirect(url_for('accessdenied'))

    sql = read('imgmods', **{"imgid": escape(imageid)})
    result = doselect(sql)

    try:
        sql = delete('imgmods', **{"imgid": result[0][0]})
        result = doselect(sql)
    except IndexError:
        pd.title = "SQL error"
        pd.errortext = "SQL error"
        return render_template('error.html', pd=pd)

    return redirect(url_for('moderate'))
