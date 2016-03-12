import datetime
import logging

from sql import upsert, doupsert, doquery, Tree
from mail import send_mail
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
from utility import ip_uid

import images
import users

logger = logging.getLogger(__name__)

class Tags(Tree):
    def __init__(self):
        self.root = 'tags'
        super(self.__class__, self).__init__(self.root)

    def insert_children(self, names, parentname):
        if parentname == 'Unsorted':
            try:
                self.retrieve('Unsorted')
            except IndexError:
                self.insert_children(['Unsorted'], self.root)

        super(self.__class__, self).insert_children(names, parentname)

    def delete(self, nodename):
        if nodename == 'Unsorted':
            return False

        if nodename == self.root:
            return False

        sql = "delete from itemtags where tag=%(tag)s;"
        doquery(sql, { 'tag': nodename })

        return super(self.__class__, self).delete(nodename)

    def items(self, tag):
        sql = "select itemid from itemtags where tag = %(tag)s;"
        tags = doquery(sql, { 'tag': tag })

        ret = list()
        for tag in tags:
            ret.append(SiteItem(tag[0]))
        return ret

    def items_from_children(self, tag):
        ret = list()

        items = dict()
        for child in self.all_children_of(tag):
            for item in self.items(child):
                ret = list(set(ret) ^ set([item]))

        return ret

item_cache = dict()
@memoize_with_expiry(item_cache, long_cache_persist)
def item_by_uid(uid):
    sql = 'select name from items where uid = %(uid)s;'
    result = doquery(sql, { 'uid': uid })

    try:
        return result[0][0]
    except IndexError:
        return

@memoize_with_expiry(item_cache, long_cache_persist)
def uid_by_item(item):
    sql = 'select uid from items where name = %(name)s;'
    result = doquery(sql, { 'name': item })

    try:
        return result[0][0]
    except IndexError:
        return

def item_search(query):
    sql = 'select uid from items where name like %(query)s;'
    result = doquery(sql, {'query': '%{}%'.format(query)})

    ret = list()
    for item in result:
        ret.append(SiteItem(item[0]))
    return ret

class ItemHist(object):
    def __init__(self, uid):
        self.uid = uid

class NoItem(Exception):
    def __init__(self, item):
        Exception.__init__(self, item)

class SiteItem(object):
    def __init__(self, uid):
        sql = 'select * from items where uid = %(uid)s;'
        result = doquery(sql, { 'uid': uid })

        try:
            self.uid = result[0][0]
            self.name = result[0][1]
            self.description = result[0][2]
            self.added = result[0][3]
            self.modified = result[0][4]
        except IndexError:
            raise NoItem(uid)

        self.tree = Tags()

        """
        sql = 'select tag from itemtags where uid = %(uid)s;'
        result = doquery(sql, { 'uid': uid })

        try:
            self.tags = result[0]
        except IndexError:
            self.tags = None
        """

    def delete(self):
        logger.info('deleted item id {}: {}'.format(self.uid, self.name))
        item_cache = dict()

        for image in self.images():
            image.delete()

        sql = 'delete from itemedits where itemid = %(uid)s;'
        result = doquery(sql, {"uid": self.uid}) 
     
        sql = 'delete from ownwant where itemid = %(itemid)s;'
        result = doquery(sql, {"itemid": self.uid}) 

        sql = 'delete from tradelist where itemid = %(itemid)s;'
        result = doquery(sql, {"itemid": self.uid}) 

        sql = 'delete from itemtags where itemid = %(uid)s;'
        result = doquery(sql, {"uid": self.uid}) 

        sql = 'delete from items where uid = %(uid)s;'
        result = doquery(sql, {"uid": self.uid}) 

    def update(self):
        logger.info('item updated {}: {} '.format(self.uid, self.name))
        self.name = self.name.strip()[:64]
        sql = "update items set name = %(name)s, description = %(desc)s, modified = %(modified)s where uid = %(uid)s;"
        return doquery(sql, {"uid": self.uid, "desc": self.description, "name": self.name, "modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") })

    def history(self):
        sql = """select itemedits.uid, itemedits.itemid, itemedits.date, itemedits.userid, ip.ip
                 from itemedits
                 join ip on itemedits.ip=ip.uid
                 where itemid = %(uid)s
                 order by uid desc;"""
        edits = doquery(sql, { 'uid': self.uid })

        ret = list()
        for edit in edits:
            editobject = ItemHist(edit[0])
            editobject.uid = str(editobject.uid).zfill(8)
            editobject.itemid = edit[1]
            editobject.date = edit[2]
            editobject.userid = edit[3]
            editobject.ip = edit[4]

            editobject.user = users.user_by_uid(editobject.userid)

            ret.append(editobject)

        return ret

    imglist_cache = dict()
    @memoize_with_expiry(imglist_cache, cache_persist)
    def images(self):
        ret = list()
        sql = """select uid
                 from images
                 where parent = %(uid)s"""
        for row in doquery(sql, { 'uid': self.uid }):
            ret.append(images.SiteImage(row[0]))

        return ret

    body_cache = dict()
    @memoize_with_expiry(body_cache, cache_persist)
    def body(self, edit=None):
        if not edit:
            edit = self.description
        sql = "select body from itemedits where uid = '%(uid)s';"
        return doquery(sql, {'uid': int(edit) })[0][0]

    have_cache = dict()
    @memoize_with_expiry(have_cache, cache_persist)
    def haveusers(self):
        haveusers = list()
        have = 0

        sql = "select userid,hidden from ownwant where itemid = %(uid)s and own = 1"
        res = doquery(sql, {"uid": self.uid})
        
        for user in res:
            have = have + 1
            if not user[1]:
                userinfo = users.SiteUser.create(users.user_by_uid(user[0]))
                haveusers.append(userinfo)

        return (have, haveusers)

    willtrade_cache = dict()
    @memoize_with_expiry(willtrade_cache, cache_persist)
    def willtradeusers(self):
        willtradeusers = list()
        willtrade = 0

        sql = "select userid from ownwant where itemid = %(uid)s and willtrade = 1"
        res = doquery(sql, {"uid": self.uid})
        
        for user in res:
            willtrade = willtrade + 1
            userinfo = users.SiteUser.create(users.user_by_uid(user[0]))
            willtradeusers.append(userinfo)

        return (willtrade, willtradeusers)

    want_cache = dict()
    @memoize_with_expiry(want_cache, cache_persist)
    def wantusers(self):
        wantusers = list()
        want = 0

        sql = "select userid from ownwant where itemid = %(uid)s and want = 1 and hidden = 0"
        res = doquery(sql, {"uid": self.uid})
        
        for user in res:
            want = want + 1
            userinfo = users.SiteUser.create(users.user_by_uid(user[0]))
            wantusers.append(userinfo)

        return (want, wantusers)

    def tags(self):
        sql = "select tag from itemtags where itemid = %(itemid)s;"
        tags = doquery(sql, { 'itemid': self.uid })

        ret = list()
        for tag in tags:
            ret.append(self.tree.retrieve(tag[0]))
        return ret

    def tags_with_parents(self):
        sql = "select tag from itemtags where itemid = %(itemid)s;"
        direct_tags = doquery(sql, { 'itemid': self.uid })

        ret = dict()
        for tag in direct_tags:
            path = self.tree.path_to(tag[0])
            for path_item in path:
                excludes = list()
                excludes.append('Hidden')
                excludes.append('Unsorted')
                excludes.append(self.tree.root)
                if path_item not in excludes: 
                    # is inherited
                    ret[path_item] = True

        # ensure all tags directly applied to the item are included and marked as direct
        for tag in direct_tags:
            ret[tag[0]] = False

        return ret
        
    def add_tag(self, tag, parent=None):
        logger.info('tag {} added to {}: {} '.format(tag, self.uid, self.name))
        try:
            self.tree.retrieve(tag)
        except IndexError:
            if parent:
                self.tree.insert_children([tag], parent)
            else:
                self.tree.insert_children([tag], 'Unsorted')

        try:
            sql = "insert into itemtags (itemid, tag) values (%(itemid)s, %(tag)s);"
            doquery(sql, { 'itemid': self.uid, 'tag': tag })
        except Exception as e:
            if e[0] == 1062: # ignore duplicates
                pass
            else:
                raise

    def remove_tag(self, tag):
        logger.info('tag {} removed from {}: {} '.format(tag, self.uid, self.name))
        try:
            self.tree.retrieve(tag)
        except IndexError:
            return

        sql = "delete from itemtags where itemid=%(itemid)s and tag=%(tag)s;"
        doquery(sql, { 'itemid': self.uid, 'tag': tag })

def new_edit(itemid, description, userid, ip):
    if userid == 0:
        userid = None

    logger.info('item {} edited by {} / {} '.format(itemid, userid, ip))

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "insert into itemedits (date, itemid, userid, ip, body) values (%(date)s, %(itemid)s, %(userid)s, %(ip)s, %(body)s);"
    doquery(sql, { 'date': date, 'itemid': itemid, 'userid': userid, 'ip': ip_uid(ip), 'body': description })

    sql = "select uid from itemedits where date=%(date)s and itemid=%(itemid)s and ip=%(ip)s;"
    edit = doquery(sql, { 'date': date, 'itemid': itemid, 'ip': ip_uid(ip) })[0][0]

    sql = "update items set description = %(edit)s, modified = %(modified)s where uid = %(uid)s;"
    doquery(sql, {"uid": itemid, "edit": edit, "modified": date })

    return edit 

def new_item(name, description, userid, ip):
    name = name.strip()[:64]
    logger.info('new item {} added by {} / {} '.format(itemid, userid, ip))

    sql = "insert into items (name, description, added, modified) values (%(name)s, 0, %(now)s, %(now)s);"
    doquery(sql, { 'now': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'name': name })

    sql = "select uid from items where name=%(name)s and description=0;"
    itemid = doquery(sql, { 'name': name })[0][0]

    new_edit(itemid, description, userid, ip)

    return itemid 

@memoize_with_expiry(item_cache, long_cache_persist)
def latest_items(limit=0):
    items = list()

    try:
        if limit > 0:
            sql = "SELECT uid FROM items order by added desc limit %(limit)s;"
        else:
            sql = "SELECT uid FROM items;"
        result = doquery(sql, { 'limit': limit })
        for item in result:
            items.append(SiteItem(item[0]))
    except TypeError:
        pass

    return items
