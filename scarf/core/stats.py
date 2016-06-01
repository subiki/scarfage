from sql import doquery
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
import items

stats_cache = dict()
@memoize_with_expiry(stats_cache, long_cache_persist)
def get_whores_table():
    """
    Top ten users with the most items in their collection

    :return: list of (count, username)
    """

    sql = """select count(*), users.username
             from users 
             join ownwant on ownwant.userid=users.uid 
             where ownwant.own = 1 
             group by users.uid, ownwant.own 
             order by count(*) desc limit 10;"""
    result = doquery(sql)

    return result;

willtrade_cache = dict()
@memoize_with_expiry(willtrade_cache, long_cache_persist)
def get_willtrade_table():
    """
    Top ten users with items available for trade

    :return: list of (count, username)
    """

    sql = """select count(*), users.username
             from users 
             join ownwant on ownwant.userid=users.uid 
             where ownwant.willtrade = 1 
             group by users.uid, ownwant.willtrade
             order by count(*) desc limit 10;"""
    result = doquery(sql)

    return result;

needy_cache = dict()
@memoize_with_expiry(needy_cache, long_cache_persist)
def get_needy_table():
    """
    Top ten users looking for items

    :return: list of (count, username)
    """

    sql = """select count(*), users.username
             from users 
             join ownwant on ownwant.userid=users.uid 
             where ownwant.want = 1 
             group by users.uid, ownwant.want
             order by count(*) desc limit 10;"""
    result = doquery(sql)

    return result;

contribs_cache = dict()
@memoize_with_expiry(contribs_cache, long_cache_persist)
def get_contribs_table():
    """
    Top ten users with the most item edits

    :return: list of (count, username)
    """

    sql = """select count(*), users.username
             from users 
             join itemedits on itemedits.userid=users.uid 
             group by users.uid, itemedits.userid
             order by count(*) desc limit 10;"""
    result = doquery(sql)

    return result;
