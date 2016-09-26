import datetime

from flask import render_template

from keyvalue import SiteKey, check_key_exists, new_key
from sql import upsert, doupsert, doquery, Tree
from mail import send_mail
from memoize import memoize_with_expiry, cache_persist, long_cache_persist
from utility import obfuscate, deobfuscate
import users
import items

privatemessage_cache = dict()
class PrivateMessage(object):
    @classmethod
    @memoize_with_expiry(privatemessage_cache, cache_persist)
    def create(cls, messageid):
        return cls(messageid)

    def __init__(self, messageid):
        sql = 'select * from messages where uid = %(uid)s;'
        result = doquery(sql, {'uid': messageid})

        try:
            self.uid = result[0][0]
            self.uid_obfuscated = obfuscate(result[0][0])
            self.from_uid = result[0][1]
            self.to_uid = result[0][2]
            self.subject = result[0][3]
            self.message = result[0][4]
            self.status = result[0][5] # trade status, None for PMs 
            self.parentid = result[0][6]
            self.parentid_obfuscated = obfuscate(result[0][6])
            self.sent = result[0][7]

            self.from_user = users.SiteUser.create(users.user_by_uid(self.from_uid)).username
            self.to_user = users.SiteUser.create(users.user_by_uid(self.to_uid)).username
        except IndexError:
            raise NoItem(messageid)

    def parent(self):
        if self.parentid > 0:
            return PrivateMessage.create(self.parentid)

    def setstatus(self, status):
        if self.uid > 0:
            self.status = status
            sql = "update messages set status = %(status)s where uid = %(uid)s;"
            result = doquery(sql, {"uid": self.uid, "status": status})
        else:
            return None

    def read(self, userid):
        new_key("messagereadstatus_{}_{}".format(self.uid, userid), '')    

    def unread(self, userid):
        o = SiteKey("messagereadstatus_{}_{}".format(self.uid, userid))    
        o.delete()

    def read_status(self, userid):
        return check_key_exists("messagereadstatus_{}_{}".format(self.uid, userid))

    def delete(self, userid):
        new_key("messagedeletestatus_{}_{}".format(self.uid, userid), '')    

    def undelete(self, userid):
        o = SiteKey("messagedeletestatus_{}_{}".format(self.uid, userid))    
        o.delete()

    def delete_status(self, userid):
        return check_key_exists("messagedeletestatus_{}_{}".format(self.uid, userid))

    @memoize_with_expiry(privatemessage_cache, cache_persist)
    def replies(self):
        ret = list()

        sql = 'select * from messages where parent = %(uid)s;'
        result = doquery(sql, {"uid": self.uid})

        for reply in result:
            pm = PrivateMessage.create(reply[0])
            ret.append(pm)

        return ret

def send_pm(fromuserid, touserid, subject, message, status, parent):
    # FIXME: parent id validation
    sent = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    sql = "insert into messages (fromuserid, touserid, subject, message, parent, sent, status) values (%(fromuserid)s, %(touserid)s, %(subject)s, %(message)s, %(parent)s, %(sent)s, %(status)s);"
    doquery(sql, { 'fromuserid': fromuserid, 'touserid': touserid, 'subject': subject, 'message': message, 'parent': parent, 'sent': sent, 'status': status })

    sql = "select uid from messages where fromuserid=%(fromuserid)s and touserid=%(touserid)s and sent=%(sent)s;"
    messageid = doquery(sql, { 'fromuserid': fromuserid, 'touserid': touserid, 'sent': sent })[0][0]

    email_user = users.SiteUser.create(users.user_by_uid(touserid))
    from_user = users.SiteUser.create(users.user_by_uid(fromuserid))

    message = render_template('email/pm_notify.html', to_user=email_user, email=email_user.email, from_user=from_user, message=message, status=status, parent=parent, messageid=obfuscate(messageid))

    subject = '[Scarfage] (PM) ' + subject
    send_mail(recipient=email_user.email, subject=subject, message=message)

    return messageid 

class TradeItem(object):
    def __init__(self, itemid):
        self.uid = itemid 
        self.itemid = 0
        self.messageid = 0
        self.userid = 0
        self.acceptstatus = 0

    def setstatus(self, status):
        if self.uid > 0:
            self.acceptstatus = status

            sql = "update tradelist set acceptstatus = %(status)s where uid = %(uid)s;"
            return doquery(sql, { "uid": self.uid, "status": status })

    def accept(self):
        return self.setstatus(tradeitemstatus['accepted'])

    def reject(self):
        return self.setstatus(tradeitemstatus['rejected'])

tradeitemstatus = {'unmarked': 0, 'rejected': 1, 'accepted': 2}
tradestatus = {'reserved': 0, 'active_trade': 1, 'complete_trade': 2, 'settled_trade': 3, 'rejected_trade': 4, 'cancelled_trade': 5}
trademessage_cache = dict()
class TradeMessage(PrivateMessage):
    @classmethod
    @memoize_with_expiry(trademessage_cache, cache_persist)
    def create(cls, messageid):
        return cls(messageid)

    def __init__(self, messageid):
        super(self.__class__, self).__init__(messageid)
        self.tradeitemstatus = tradeitemstatus
        self.tradestatus = tradestatus

        self.items = []

        sql = 'select * from tradelist where messageid = %(uid)s;'
        result = doquery(sql, {"uid": messageid})

        complete = True
        for item in result:
            ti = TradeItem(item[0])
            ti.itemid = item[1]
            ti.messageid = item[2]
            ti.userid = item[3]
            ti.acceptstatus = item[4]
            ti.item = items.SiteItem.create(ti.itemid)
            ti.user = users.SiteUser.create(users.user_by_uid(ti.userid))

            self.items.append(ti)

            if (ti.acceptstatus != tradeitemstatus['accepted']):
                complete = False

        if complete == True and self.status < tradestatus['settled_trade']:
            self.status = tradestatus['complete_trade']

    def settle(self):
        return self.setstatus(tradestatus['settled_trade'])

    def reject(self):
        return self.setstatus(tradestatus['rejected_trade'])

    def cancel(self):
        return self.setstatus(tradestatus['cancelled_trade'])

def add_tradeitem(itemid, messageid, userid, acceptstatus):
    sql = "insert into tradelist (itemid, messageid, userid, acceptstatus) values (%(itemid)s, %(messageid)s, %(userid)s, %(acceptstatus)s);"
    doquery(sql, { 'itemid': itemid, 'messageid': messageid, 'userid': userid, 'acceptstatus': acceptstatus })
