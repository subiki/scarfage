from scarf import app
from flask import redirect, url_for, render_template, session, request, flash
from scarflib import redirect_back, pagedata, siteimage, NoImage, user_by_uid, Tags
from sql import doquery, read
from main import page_not_found
 
@app.route('/tag/')
def bare_tag():
    return redirect(url_for('index'))

@app.route('/tag/<tag>')
def mod_tag(tag):
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 10:
        return redirect(url_for('accessdenied'))

    pd.tree = Tags()
    try:
        pd.tag = pd.decode(tag)

        # remove children, current parent, and ourself from the reparent list
        all_tags = pd.tree.all_children_of(pd.tree.root)
        subtract = pd.tree.all_children_of(pd.tag)
        parent = pd.tree.parent_of(pd.tag)

        subtract.append(pd.tag)
        subtract.append(parent)

        pd.reparent_list = list(set(all_tags) ^ set(subtract))

        return render_template('tag.html', pd=pd)
    except TypeError:
        return page_not_found(404)

@app.route('/tag/<tag>/delete')
def mod_tag_delete(tag):
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 10:
        return redirect(url_for('accessdenied'))

    tree = Tags()
    decode_tag = pd.decode(tag)
    parent = tree.parent_of(decode_tag)

    app.logger.info('Deleting tag: ' + decode_tag)
    tree.delete(decode_tag)

    return redirect('/tag/' + pd.encode(parent))

@app.route('/tag/new', methods=['POST'])
def newtag():
    pd = pagedata()

    if request.method == 'POST':
        if 'username' in session:
            userid = pd.authuser.uid
        else:
            userid = 0 

        if 'tag' in request.form:
            try:
                Tags().retrieve(request.form['tag'])
                flash('Tag already exists!')
            except IndexError:
                Tags().insert_children([request.form['tag']], pd.decode(request.form['parent']))

    return redirect_back('index')

@app.route('/tag/metatag', methods=['POST'])
def new_metatag():
    pd = pagedata()

    if request.method == 'POST':
        if 'username' in session:
            userid = pd.authuser.uid
        else:
            userid = 0 

        if 'metatag' in request.form:
            Tags().add_metatag(pd.decode(request.form['tag']), request.form['metatag'])

    return redirect_back('index')

@app.route('/tag/reparent', methods=['POST'])
def tagreparent():
    pd = pagedata()

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
