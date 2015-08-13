from scarf import app
from flask import render_template
from scarflib import pagedata, get_whores_table, get_contribs_table

@app.route('/stats')
def stats():
    pd = pagedata()

    pd.title = "Scarf Stats" 

    pd.topcollectors = get_whores_table()
    pd.topcontributors = get_contribs_table()

    return render_template('stats.html', pd=pd)
