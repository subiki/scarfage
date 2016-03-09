from scarf import app
from flask import render_template
from scarflib import PageData, get_whores_table, get_contribs_table, get_needy_table, get_willtrade_table

@app.route('/stats')
def stats():
    pd = PageData()

    pd.title = "Scarf Stats" 

    pd.topcollectors = get_whores_table()
    pd.topcontributors = get_contribs_table()
    pd.topneedy = get_needy_table()
    pd.topwilltrade = get_willtrade_table()

    return render_template('stats.html', pd=pd)
