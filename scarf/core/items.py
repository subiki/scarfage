import datetime
import logging

from sql import upsert, doupsert, doquery, Tree, MySQLdb
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
            ret.append(SiteItem.create(tag[0]))
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

def item_search(query, limit=10, offset=0, sort='name'):
    ret = dict()
    ret['items'] = list()

    sql = 'select count(*) from items where name like %(query)s;'
    ret['maxresults'] = doquery(sql, {'query': '%{}%'.format(query)})[0][0]

    if ret['maxresults'] == 0:
        return ret

    sorts = {'name': 'name asc', 'added': 'added desc', 'modified': 'modified desc'}

    if sort not in sorts.keys():
        sort = 'name'

    sql = 'select uid from items where name like %(query)s order by {} limit %(limit)s offset %(offset)s;'.format(sorts[sort])
    result = doquery(sql, {'query': '%{}%'.format(query), 'limit': limit, 'offset': offset})

    for item in result:
        ret['items'].append(SiteItem.create(item[0]))

    return ret

class ItemHist(object):
    def __init__(self, uid):
        self.uid = uid

class NoItem(Exception):
    def __init__(self, item):
        Exception.__init__(self, item)

siteitem_cache = dict()
class SiteItem(object):
    """
    Site Item - object for an item

    :Attributes:
        * uid       - UID for the item
        * name      - The item's name
        * added     - When the item was added
        * modified  - Last modified
        * tree      - an instance of the Tags() object

    :raises NoItem: If no item can be found or if an error occurs this will be raised during initialization.
    """

    @classmethod
    @memoize_with_expiry(siteitem_cache, long_cache_persist)
    def create(cls, username):
        return cls(username)

    def __init__(self, uid):
        sql = 'select uid, name, added, modified from items where uid = %(uid)s;'

        try:
            result = doquery(sql, { 'uid': uid })

            self.uid = result[0][0]
            self.name = result[0][1]
            self.added = result[0][2]
            self.modified = result[0][3]
        except (Warning, IndexError):
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

    def description(self):
        """
        Get the item's current description. Items can have several descriptions with only one set as active.

        :return: ID of the item's description
        """

        sql = 'select description from items where uid = %(uid)s;'

        try:
            result = doquery(sql, { 'uid': self.uid })
            return result[0][0]
        except (Warning, IndexError):
            raise NoItem(uid)

    def delete(self):
        """
        Delete an item. Might be dangerous.
        """

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
        """
        Update the database with the object's current name as well as the modified timestamp.
        """

        logger.info('item updated {}: {} '.format(self.uid, self.name))
        self.name = self.name.strip()[:64]
        sql = "update items set name = %(name)s, modified = %(modified)s where uid = %(uid)s;"
        return doquery(sql, {"uid": self.uid, "name": self.name, "modified": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") })

    def history(self):
        """
        Get the edit history for an item. 

        :return: A list of objects with the following attributes:
            * uid       - The edit's uid, zero filled
            * itemid    - The item id
            * date      - Date of the edit
            * userid    - Editing user
            * ip        - IP address of the editor
        """

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

    def values(self, edit=None):
        """
        Return the attributes of the object as a dict. body will be set to the text of the specified or current edit.

        :param edit: Optional parameter to specify a historical edit id. If omitted the current edit ID for the item is used. 
        """

        if not edit:
            edit = self.description()
        else:
            edit = int(edit)

        images = list()
        for image in self.images():
            images.append(image.uid)

        return dict(body=self.body(edit),
                    uid=self.uid,
                    name=self.name,
                    description=edit,
                    tags=self.tags_with_parents(),
                    images=images,
                    added=str(self.added),
                    modified=str(self.modified))

    imglist_cache = dict()
    @memoize_with_expiry(imglist_cache, cache_persist)
    def images(self):
        """
        Get the images for an item.

        :return: list of SiteImage objects
        """

        ret = list()
        sql = """select uid
                 from images
                 where parent = %(uid)s"""
        for row in doquery(sql, { 'uid': self.uid }):
            ret.append(images.SiteImage.create(row[0]))

        return ret

    body_cache = dict()
    @memoize_with_expiry(body_cache, cache_persist)
    def body(self, edit=None):
        """
        Get the text of the item's description.

        :param edit: Optional parameter to specify a historical edit id. If omitted the current edit ID for the item is used. 
        :return: The item's description
        """
        if not edit:
            edit = self.description()
        sql = "select body from itemedits where uid = '%(uid)s';"
        return doquery(sql, {'uid': int(edit) })[0][0]

    have_cache = dict()
    @memoize_with_expiry(have_cache, cache_persist)
    def haveusers(self):
        """
        Get a list of users that have this item in their collections.

        :return: list of SiteUser objects
        """

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
        """
        Get a list of users that have this item in their collection and available for trade.

        :return: list of SiteUser objects
        """

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
        """
        Get a list of users that want this item.

        :return: list of SiteUser objects
        """

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
        """
        Get a list of tags for this item.

        :return: list of tags as strings
        """

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

    username = users.user_by_uid(userid)
    try:
        date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        sql = "insert into itemedits (date, itemid, userid, ip, body) values (%(date)s, %(itemid)s, %(userid)s, %(ip)s, %(body)s);"
        doquery(sql, { 'date': date, 'itemid': itemid, 'userid': userid, 'ip': ip_uid(ip), 'body': description })

        sql = "select uid from itemedits where date=%(date)s and itemid=%(itemid)s and ip=%(ip)s;"
        edit = doquery(sql, { 'date': date, 'itemid': itemid, 'ip': ip_uid(ip) })[0][0]

        sql = "update items set description = %(edit)s, modified = %(modified)s where uid = %(uid)s;"
        doquery(sql, {"uid": itemid, "edit": edit, "modified": date })

        logger.info('item {} edited by {} / {} '.format(itemid, username, ip))

        return edit 
    except MySQLdb.OperationalError, Warning:
        logger.info('Error editing item {} by {} ({})'.format(itemid, username, ip))
        #FIXME: raise something else
        raise NoItem(itemid)

def new_item(name, description, userid, ip):
    name = name.strip()[:64]

    try:
        sql = "insert into items (name, description, added, modified) values (%(name)s, 0, %(now)s, %(now)s);"
        doquery(sql, { 'now': datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), 'name': name })

        sql = "select uid from items where name=%(name)s and description=0;"
        itemid = doquery(sql, { 'name': name })[0][0]
    except MySQLdb.OperationalError, Warning:
        logger.info('Error adding item {} by {} ({})'.format(name, userid, ip))
        raise NoItem(0)

    new_edit(itemid, description, userid, ip)

    username = users.user_by_uid(userid)
    logger.info('new item {} added by {} / {} '.format(name, username, ip))

    return itemid 

# TODO: remove this once reimplemented with JS. #81
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
            items.append(SiteItem.create(item[0]))
    except TypeError:
        pass

    return items
