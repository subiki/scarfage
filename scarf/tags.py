from scarf import app
from core import redirect_back, SiteImage, NoImage, user_by_uid, Tags
from main import page_not_found, PageData
from access import check_mod

from flask import redirect, url_for, render_template, session, request, flash
 
@app.route('/tag/')
def bare_tag():
    return redirect(url_for('index'))

@app.route('/tag/<tag>')
def mod_tag(tag):
    pd = PageData()

    pd.tree = Tags()
    try:
        pd.tag = pd.decode(tag)

        # remove children, current parent, and ourself from the reparent list
        all_tags = pd.tree.all_children_of(pd.tree.root)
        subtract = pd.tree.all_children_of(pd.tag)
        parent = pd.tree.parent_of(pd.tag)

        if parent != pd.tree.root:
            subtract.append(parent)

        subtract.append(pd.tag)

        pd.reparent_list = list(set(all_tags) ^ set(subtract))

        pd.root_tree = pd.tree.draw_tree(pd.tree.root)

        return render_template('tag.html', pd=pd)
    except TypeError:
        return page_not_found(404)

@app.route('/tag/<tag>/delete')
@check_mod
def mod_tag_delete(tag):
    pd = PageData()

    tree = Tags()
    decode_tag = pd.decode(tag)
    parent = tree.parent_of(decode_tag)

    if tree.delete(decode_tag):
        return redirect('/tag/' + pd.encode(parent))
    else:
        flash('Unable to delete tag: ' + decode_tag)
        return redirect_back('/tag/' + tag)

@app.route('/tag/new', methods=['POST'])
def newtag():
    pd = PageData()

    if request.method == 'POST':
        if 'username' in session:
            userid = pd.authuser.uid
        else:
            userid = 0 

        if 'tag' in request.form:

            if request.form['tag'] == '':
                return redirect_back('index')

            try:
                Tags().retrieve(request.form['tag'].strip())
                flash('Tag already exists!')
            except IndexError:
                Tags().insert_children([request.form['tag']], pd.decode(request.form['parent']))

    return redirect_back('index')

@app.route('/tag/reparent', methods=['POST'])
@check_mod
def tagreparent():
    pd = PageData()

    if request.method == 'POST':
        if 'username' in session:
            userid = pd.authuser.uid
        else:
            userid = 0 

        if 'reparent' in request.form:
            try:
                Tags().reparent(pd.decode(request.form['name']), pd.decode(request.form['reparent']))
            except IndexError:
                flash('Error reparenting tag!')

    return redirect_back('index')
