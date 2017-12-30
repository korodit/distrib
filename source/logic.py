# coding: utf-8
import json
id = 0
users = {}
groups = {}

def register(ip,port,username):
    if username not in users:
        global id
        users[username] = {"id":id,"ip":ip,"port":port,"username":username}
        id += 1
        print "What I got is:",ip,str(port),username
        return json.dumps(users[username])
    else:
        return json.dumps("Error:username already exists")

def listmembers(group):
    if group not in groups:
        return json.dumps("Error:group does not exist")
    result = []
    for username in groups[group]:
        result.append(users[username])
    return json.dumps(result)

def listgroups():
    result = []
    for group,mlist in groups.iteritems():
        result.append(group)
    return json.dumps(result)

def quitchat(id):
    global users
    found = False
    username = ""
    for uname,details in users.iteritems():
        if details["id"] == id:
            found = True
            username = uname
            break
    if not found:
        return json.dumps("Error:id does not exist")
    todel = []
    for group in groups:
        if username in groups[group]:
            todel.append(group)
    for group in todel:
        exitgroup(group,username)
    del users[username]
    return json.dumps("Success")

def exitgroup(group,username):
    if username not in users:
        return json.dumps("Error: username does not exist")
    if group not in groups:
        return json.dumps("Error: group does not exist")
    groups[group].remove(username)
    if len(groups[group]) == 0:
        del groups[group]
    return json.dumps("Success")

def joingroup(group,username):
    if username not in users:
        return json.dumps("Error:username does not exist")
    if group not in groups:
        groups[group] = []
    if username not in groups[group]:
        groups[group].append(username)
    return listmembers(group)