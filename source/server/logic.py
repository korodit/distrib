# coding: utf-8
import json
import time
from threading import Thread, Lock
id = 0
id_lock = Lock()
users = {}
users_lock = Lock()
groups = {}
groups_lock = Lock()
id_heartbeat_dict = {}
heartbeat_lock = Lock()

def register(ip,port,username):
    global id_lock
    global users_lock
    global heartbeat_lock
    global groups_lock
    global id_heartbeat_dict
    with id_lock:
        with users_lock:
            with heartbeat_lock:
                if username not in users:
                    global id
                    users[username] = {"id":id,"ip":ip,"port":port,"username":username}
                    id_heartbeat_dict[id] = True
                    id += 1
                    print "What I got is:",ip,str(port),username
                    print "This is my heartbeat now:",id_heartbeat_dict
                    return json.dumps(users[username])
                else:
                    return json.dumps({"Error":"username already exists"})

def listmembers(group):
    global id_lock
    global users_lock
    global heartbeat_lock
    global groups_lock
    with users_lock:
        with groups_lock:
            if group not in groups:
                return json.dumps({"Error":"group does not exist"})
            result = []
            for username in groups[group]:
                result.append(users[username])
            return json.dumps(result)

def listgroups():
    global id_lock
    global users_lock
    global heartbeat_lock
    global groups_lock
    with groups_lock:
        result = []
        for group,mlist in groups.iteritems():
            result.append(group)
        return json.dumps(result)

def quitchat(id):
    global id_lock
    global users_lock
    global heartbeat_lock
    global groups_lock
    global users
    global id_heartbeat_dict
    todel = []
    with users_lock:
        with groups_lock:
            with heartbeat_lock:
                found = False
                username = ""
                for uname,details in users.iteritems():
                    if details["id"] == id:
                        found = True
                        username = uname
                        break
                if not found:
                    return json.dumps({"Error":"id does not exist"})
                # todel = []
                for group in groups:
                    if username in groups[group]:
                        todel.append(group)
    for group in todel:
        exitgroup(group,username)
    with users_lock:
        with heartbeat_lock:
                del id_heartbeat_dict[id]
                del users[username]
    return json.dumps("Success")

def exitgroup(group,username):
    global id_lock
    global users_lock
    global heartbeat_lock
    global groups_lock
    with users_lock:
        with groups_lock:
            if username not in users:
                return json.dumps({"Error":"username does not exist"})
            if group not in groups:
                return json.dumps({"Error":"group does not exist"})
            groups[group].remove(username)
            if len(groups[group]) == 0:
                del groups[group]
            return json.dumps("Success")

def joingroup(group,username):
    global id_lock
    global users_lock
    global heartbeat_lock
    global groups_lock
    with users_lock:
        with groups_lock:
            if username not in users:
                return json.dumps({"Error":"username does not exist"})
            if group not in groups:
                groups[group] = []
            if username not in groups[group]:
                groups[group].append(username)
    return listmembers(group)

def heartbeat(id):
    global id_lock
    global users_lock
    global heartbeat_lock
    global groups_lock
    global id_heartbeat_dict
    with heartbeat_lock:
        id_heartbeat_dict[id] = True
    return "Success"

def haros():
    global id_heartbeat_dict
    global heartbeat_lock
    while True:
        to_be_del = []
        to_be_checked = []
        with heartbeat_lock:
            for idd in id_heartbeat_dict:
                if not id_heartbeat_dict[idd]:
                    to_be_del.append(idd)
                else:
                    to_be_checked.append(idd)
            for idd in to_be_checked:
                id_heartbeat_dict[idd] = False
        for idd in to_be_del:
            quitchat(idd)
        time.sleep(1)

haros_thread = Thread(target=haros, name=None, args=())
haros_thread.daemon = True
haros_thread.start()