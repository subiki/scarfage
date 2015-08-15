from scarf import app
from flask import render_template
from scarflib import pagedata, get_whores_table

@app.route('/stats')
def stats():
    pd = pagedata()

    pd.title = "Scarf Stats" 

    pd.topcollectors = get_whores_table()

    return render_template('stats.html', pd=pd)
