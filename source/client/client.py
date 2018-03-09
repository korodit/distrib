import sys
import os
from string import printable
from threading import Thread, Lock,Timer
import time
import queue
import http.client
import json
import socket
from pqdict import pqdict
import copy

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
    screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()
class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            # ch = sys.stdin.read(1)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

# enter: ord 13
#backspace: ord 127

# getch = _Getch()
# getch = lamba : time.sleep(1)
getch = None

def server_request(parameters):
    """Returns a proper object out of a request to the tracker"""
    try:
        ip = StateHolder.server_ip
        conn = http.client.HTTPConnection(ip)
        conn.request("GET", parameters)
        r1 = conn.getresponse()
        data1 = r1.read()
        return json.loads(data1.decode("utf-8"))
    # except http.client.HTTPException:
    except:
        return {"Error":"Server unavailable"}

class UIHandler:
    """
    Contains all functions to handle the given output in a tidely manner.
    Everything other than post() is called exclusively by InputHandler,
    to keep the terminal right while printing the real time input.
    """

    # Must be held when an action is about to meddle with the UI,
    # or with the InputHandler information, in any way
    ui_mutex = Lock()

    @classmethod
    def append_input(cls,app):#adds a new string at the end of the current
        print(app,end="")
        sys.stdout.flush()

    @classmethod
    def bspace(cls): #prints a proper backspace
        print("\b \b",end="")
        sys.stdout.flush()

    @classmethod
    def clear_input(cls): #clears input. Is not to be called alone
        linelen = (len(InputHandler.current_input)+len(InputHandler.prompt_msg))
        print("\r"+" "*linelen+"\r",end="")
        sys.stdout.flush()
    
    @classmethod
    def reset_input(cls,newin): #for InputHandler Only to Call
        # with(yield from ui_mutex):
        cls.clear_input()
        print(InputHandler.prompt_msg+newin,end="")
        sys.stdout.flush()

    @classmethod
    def restore_input(cls):
        cls.clear_input()
        print(InputHandler.prompt_msg+InputHandler.current_input,end="")
        sys.stdout.flush()

    @classmethod
    def post(cls,out): #must NOT be called by Input Handler
        # with(yield from ui_mutex):
        cls.clear_input()
        print(InputHandler.output_pudding+out)
        cls.restore_input()
        sys.stdout.flush()

class InputHandler:
    """
    Handles the terminal interface according to input given, and
    pushes the commands to the command queue when enter key
    is pressed
    """

    current_input=""
    default_prompt_msg = "[(Warning:Not connected!)]:> "
    prompt_msg = default_prompt_msg
    output_pudding = "|| "

    @classmethod
    def handle_input(cls,ch):
        with UIHandler.ui_mutex:
        
            if ord(ch)==3:# ctrl+c
                #try to make a cleanup before exiting
                print("")
                StateHolder.flag_exit()
                CommandHandler.quit("")
                exit()

            elif ord(ch)==13:# enter
                command=cls.current_input.replace(chr(13),"")
                CommandHandler.pushCommand(command)
                UIHandler.reset_input("")
                cls.current_input = ""

            elif ord(ch)==127 and len(cls.current_input)>0:# backspace
                newin=cls.current_input[:-1].replace(chr(13),"")
                # UIHandler.reset_input(newin)
                UIHandler.bspace()
                cls.current_input = newin

            elif ch in printable or ord(ch)>127: # printable
                cls.current_input+=ch
                UIHandler.append_input(ch)

class OutputHandler:
    """
    Essentially a wrapper, holds a queue at which
    strings to be printed are thrown.
    """

    outputQueue = queue.Queue(0)

    @classmethod
    def processOutput(cls):
        while(True):
            output_str = cls.outputQueue.get()
            with UIHandler.ui_mutex:
                UIHandler.post(output_str)
    
    @classmethod
    def print(cls,out):
        OutputHandler.outputQueue.put(out)

    @classmethod
    def print_msg(cls,out,timee):
        cls.print(out)
        curr_timestamp = time.time()
        lat = curr_timestamp - timee
        Benchmark.add_msg(lat,curr_timestamp)

    @classmethod
    def initialize(cls):
        Thread(target=OutputHandler.processOutput, name=None, args=(),daemon=True).start()

class CommandHandler:
    """
    Holds a queue at which keyboard commands are thrown
    and handles them by order. Contains the functions that
    process each command
    """
    commandQueue = queue.Queue(0)
    commandDict = {}

    # To be run as a daemon Thread
    @classmethod
    def processQueue(cls):
        while(True):
            command_str = cls.commandQueue.get()
            if command_str == "":
                continue
            if command_str[0]=='!':
                command_str = command_str[1:].split(' ')
                command = command_str[0]
                param = ' '.join(command_str[1:])
                if command in cls.commandDict:
                    cls.commandDict[command](param)
                else:
                    OutputHandler.print("( Warning: Wrong command name! )")
            else:
                cls.chat(command_str)
    
    # For calling from external classes,
    # a wrapper method
    @classmethod
    def pushCommand(cls,comm):
        cls.commandQueue.put(comm)

    # Bind commands to respective functions
    @classmethod
    def initialize(cls):
        cls.commandDict = {
            "echo":cls.echo,
            "newname":cls.newname,
            "h":cls.help,
            "register":cls.register,
            "q":cls.quit,
            # "sup":cls.setUDPPorts,
            "lg":cls.listgroups,
            "lm":cls.listmembers,
            "j":cls.joingroup,
            "e":cls.exitgroup,
            "w":cls.writetogroup
        }

        Thread(target=cls.processQueue, name=None, args=(),daemon=True).start()

    @classmethod
    def joingroup(cls,param):
        """(group_name) Join a chat group"""
        if StateHolder.id == -1:
            OutputHandler.print("( Warning: You are not logged in! )")
            return
        param = param.split(' ')
        if len(param)!=1 or param[0]=="":
            OutputHandler.print("( Warning: Wrong Arguments! )")
            return

        room_name = param[0]
        response = server_request("/join_group/{}/{}".format(room_name,StateHolder.name))
        if "Error" not in response:
            room_name = param[0]
            StateHolder.join_room(room_name)
            OutputHandler.print("( Joined room '{}'! )".format(room_name))
        else:
            OutputHandler.print("Error:"+response["Error"])
    
    @classmethod
    def exitgroup(cls,param):
        """(group_name) Exit a chat group"""
        if StateHolder.id == -1:
            OutputHandler.print("( Warning: You are not logged in! )")
            return
        param = param.split(' ')
        if len(param)!=1 or param[0]=="":
            OutputHandler.print("( Warning: Wrong Arguments! )")
            return

        room_name = param[0]
        response = server_request("/exit_group/{}/{}".format(room_name,StateHolder.name))
        if "Error" not in response:
            StateHolder.exit_room(room_name)
            OutputHandler.print("( Exited room '{}'! )".format(room_name))
        else:
            OutputHandler.print("Error:"+response["Error"])
    
    @classmethod
    def writetogroup(cls,param):
        """(group_name) Specify group on which to chat"""
        if StateHolder.id == -1:
            OutputHandler.print("( Warning: You are not logged in! )")
            return
        param = param.split(' ')
        if len(param)!=1 or param[0]=="":
            OutputHandler.print("( Warning: Wrong Arguments! )")
            return

        room_name = param[0]
        with StateHolder.rooms_lock:
            if room_name in StateHolder.rooms:
                StateHolder.current_room = room_name
                OutputHandler.print("( Now writing to group '{}' )".format(room_name))
            else:
                OutputHandler.print("( Warning: You are not participating in the group '{}'! )".format(room_name))

    @classmethod
    def listmembers(cls,param):
        """(group_name) List the members of a group available at the server"""
        param = param.split(' ')
        if len(param)!=1 or param[0]=="":
            OutputHandler.print("( Warning: Wrong Arguments! )")
            return
        
        room_name = param[0]
        response = server_request("/list_members/{}".format(room_name))
        if "Error" not in response:
            # We strip down to only show usernames
            OutputHandler.print("Members of '{}':".format(room_name)+str(list(map(lambda x:x["username"],response))))
        else:
            OutputHandler.print("Error:"+response["Error"])

    @classmethod
    def listgroups(cls,param):
        """() List the groups available at the server"""
        response = server_request("/list_groups/")
        OutputHandler.print(str(response))

    @classmethod
    def setUDPPorts(cls,param): # DEPRECATED
        """(in_port,out_port) Set the UDP input and output ports"""
        # name = "horestarod2"
        param = param.split(' ')
        if len(param)!=2:
            OutputHandler.print("( Warning: Wrong Arguments! )")
            return
        in_port,out_port = map(int,param)
        # StateHolder.udp_listen_port,StateHolder.udp_send_port = in_port,out_port
        # OutputHandler.print("( New UDP ports: in = {}, out = {} )".format(str(StateHolder.udp_listen_port),str(StateHolder.udp_send_port)))

    @classmethod
    def register(cls,param):
        """(username) Register to tracker with the appropriate input"""
        # name = "horestarod2"
        param = param.split(' ')
        if len(param)!=1 or param[0]=="":
            OutputHandler.print("( Warning: Wrong Arguments! )")
            return
        name = param[0]
        response = server_request("/register/{}/{}".format(str(StateHolder.udp_listen_port),name))
        if "Error" not in response:
            StateHolder.id = int(response["id"])
            StateHolder.name = response["username"]
            StateHolder.my_ip = response["ip"]
            StateHolder.start_heartbeat()
            with UIHandler.ui_mutex:
                InputHandler.prompt_msg = "[{}]:> ".format(StateHolder.name)
            OutputHandler.print("Logged in: id = {}, name = {}, ip = {}, port = {}".format(str(StateHolder.id),StateHolder.name,response["ip"],response["port"]))
        else:
            OutputHandler.print("Error:"+response["Error"])
    
    @classmethod
    def quit(cls,param):
        """() Quit from tracker and exit program"""
        if StateHolder.id == -1:
            OutputHandler.print("( Warning: You are not logged in! )")
            return
        response = server_request("/quit/{}".format(str(StateHolder.id)))
        StateHolder.stop_heartbeat()
        if "Error" not in response:
            if not StateHolder.exitt:
                #If we are about to quit, InputHandler blocks while waiting for
                # quit() to finish. In such case, avoid the actions below,
                # as they lead to deadlock
                with UIHandler.ui_mutex:
                    StateHolder.exit_all_rooms()
                    StateHolder.id = -1
                    StateHolder.name = None
                    InputHandler.prompt_msg = InputHandler.default_prompt_msg
                    # StateHolder.current_room = None
            OutputHandler.print("( Warning: You have been logged out! )")
        else:
            OutputHandler.print("Error:"+response["Error"])

    # What happens when the user simply inputs text
    # - should default to sending to active room?
    @classmethod
    def chat(cls,param):
        """I just chat lulz"""
        if StateHolder.id == -1 or StateHolder.current_room is None:
            OutputHandler.print("( Warning: You are not in any chat group! )")
            return
        
        StateHolder.chat_message(param)

    # Echoes a message, for testing purposes
    @classmethod
    def echo(cls,param):
        """(message) Echoes a message to the console"""
        OutputHandler.print(param)
    
    @classmethod
    def help(cls,param):
        """() Prints available commands"""
        comms = StateHolder.get_info()
        comms += "\r\n>> Commands available:"
        for key in cls.commandDict:
            comms+="\r\n\t!"+key+" --> "+cls.commandDict[key].__doc__
        OutputHandler.print(comms)
    
    # Test method, adds user name to start of prompt
    @classmethod
    def newname(cls,param):
        """(newname) Changes the name of the user appearing on the prompt"""
        if param!="":
            with UIHandler.ui_mutex:
                InputHandler.prompt_msg = "["+param+"]"+InputHandler.default_prompt_msg
            OutputHandler.outputQueue.put("( Notification: Name changed! )")
        else:
            OutputHandler.print("( Warning: Wrong Arguments! )")

# message: "[room] [purpose] [rest]"
class roomFIFO:

    class member_struct:
        def __init__(self,room_name,member_dict):
            self.msg_pool = queue.PriorityQueue(0)
            self.msg_queue = queue.Queue(0)
            self.room_name = room_name
            self.name = member_dict["username"]
            self.ip = member_dict["ip"]
            self.id = member_dict["id"]
            self.port = member_dict["port"]
            self.last_received = None
            self.process_mode = "prq" # prq:priority queue, inq:inputqueue
            self.exit = False
            Thread(target=self.process_queues, name=None, args=(),daemon=True).start()
        
        def process_queues(self):
            message = {"purpose":"send_curr_last","username":StateHolder.name,"room_name":self.room_name}
            message = (self.ip,self.port,json.dumps(message))
            shared_sign = [True]
            Thread(target=self.swell_balls, name=None, args=(message,shared_sign),daemon=True).start()
            while True:
                msg = self.msg_queue.get()
                if msg["purpose"]!="reply_curr_last":
                    self.msg_pool.put((msg["msg_id"],msg["text"]))
                else:
                    shared_sign[0] = False
                    shared_sign = [False]
                    self.last_received = msg["msg_id"]
                    break
            
            while True:
                if self.process_mode == "prq":
                    try:
                        id,txt,ts = self.msg_pool.get_nowait()
                        if id == self.last_received + 1:
                            self.last_received += 1
                            OutputHandler.print_msg("'{}' in room '{}' says:: {}".format(self.name,self.room_name,txt),ts)
                        elif id > self.last_received + 1:
                            self.msg_pool.put((id,txt,ts))
                            message = {"purpose":"send_old_msg","username":StateHolder.name,"room_name":self.room_name,"msg_id":(self.last_received + 1)}
                            message = (self.ip,self.port,json.dumps(message))
                            shared_sign = [True]
                            Thread(target=self.swell_balls, name=None, args=(message,shared_sign),daemon=True).start()
                            self.process_mode = "inq"
                    except queue.Empty:
                        self.process_mode = "inq"
                        continue
                else: # self.process_mode == "prq"
                    msg = self.msg_queue.get()
                    if self.exit:
                        shared_sign[0] = False
                        return
                    if msg["purpose"]=="incoming_msg":
                        msg_id = msg["msg_id"]
                        msg_txt = msg["text"]
                        msg_ts = msg["timestamp"]
                        self.msg_pool.put((msg_id,msg_txt,msg_ts))
                        if msg_id == self.last_received+1:
                            if shared_sign[0] == True:
                                shared_sign[0] = False
                                shared_sign = [False]
                            self.process_mode = "prq"

        def swell_balls(self,message,shared_sign): # send a message repeatedely until the parent thread signals off
            while shared_sign[0]:
                UDPbroker.sendUDP(message)
                time.sleep(0.001)
        
        def exit_member(self):
            self.exit = True
            self.msg_queue.put({"Dummy":True})



    def __init__(self,room_name):
        self.room_name = room_name
        self.my_last_msg_id = -1
        self.my_messages=[]
        self.my_messages_timestamps = []
        self.my_messages_lock = Lock()
        self.exit = False
        self.members = {}
        self.members_lock = Lock()
        Thread(target=self.member_updater, name=None, args=(),daemon=True).start()

    def member_updater(self): #daemon thread
        while not self.exit:
            response = server_request("/list_members/{}".format(self.room_name))
            with self.members_lock:
                to_be_deleted = []
                for member in self.members:
                    if member not in map(lambda x:x["username"],response):
                        to_be_deleted.append(member)
                for member in to_be_deleted:
                    self.members[member].exit_member()
                    del self.members[member]
                for member in response:
                    if member["username"] not in self.members:
                        self.members[member["username"]] = self.member_struct(self.room_name,member)
            time.sleep(0.3)
        with self.members_lock:
            for member in self.members:
                self.members[member].exit_member()
        
    
    def chat_msg(self,msg_txt):
        with self.my_messages_lock:
            self.my_messages.append(msg_txt)
            self.my_messages_timestamps.append(time.time())
            self.my_last_msg_id+=1
            out_msg = {}
            out_msg["purpose"] = "incoming_msg"
            out_msg["text"] = self.my_messages[-1]
            out_msg["username"] = StateHolder.name
            out_msg["room_name"] = self.room_name
            out_msg["msg_id"] = self.my_last_msg_id
            out_msg["timestamp"] = self.my_messages_timestamps[-1]
            out_msg = json.dumps(out_msg)
            with self.members_lock:
                for member in self.members:
                    UDPbroker.sendUDP((self.members[member].ip,self.members[member].port,out_msg))

    def handle_msg(self,msg):
        purp = msg["purpose"]
        if purp in ["incoming_msg","reply_curr_last"]:
            with self.members_lock:
                if msg["username"] in self.members:
                    self.members[msg["username"]].msg_queue.put(msg)
        elif purp == "send_curr_last":
            with self.my_messages_lock:
                with self.members_lock:
                    if msg["username"] in self.members:
                        out_msg = {}
                        out_msg["purpose"] = "reply_curr_last"
                        # out_msg["text"] = self.my_messages[-1]
                        out_msg["username"] = StateHolder.name
                        out_msg["room_name"] = self.room_name
                        out_msg["msg_id"] = self.my_last_msg_id
                        out_msg = json.dumps(out_msg)
                        UDPbroker.sendUDP((self.members[msg["username"]].ip,self.members[msg["username"]].port,out_msg))
        elif purp == "send_old_msg":
            with self.my_messages_lock:
                with self.members_lock:
                    if msg["username"] in self.members:
                        out_msg = {}
                        out_msg["purpose"] = "incoming_msg"
                        out_msg["text"] = self.my_messages[msg["msg_id"]]
                        out_msg["username"] = StateHolder.name
                        out_msg["room_name"] = self.room_name
                        out_msg["msg_id"] = msg["msg_id"]
                        out_msg["timestamp"] = self.my_messages_timestamps[msg["msg_id"]]
                        out_msg = json.dumps(out_msg)
                        UDPbroker.sendUDP((self.members[msg["username"]].ip,self.members[msg["username"]].port,out_msg))

    # member updater thread will take care of the rest
    def kill_room(self):
        self.exit = True

class roomTotal:

    class member_struct:
        def __init__(self,member_dict):
            self.name = member_dict["username"]
            self.ip = member_dict["ip"]
            self.id = member_dict["id"]
            self.port = member_dict["port"]
            self.vote = None
            self.confirmed = False
            # self.pending = {}

    def __init__(self,room_name):
        self.room_name = room_name
        self.counter = 0
        self.s = 0
        self.my_messages_q = queue.Queue(0)
        self.incoming_msg_q = queue.Queue(0)
        self.pending_msg_pool = pqdict({})
        self.pending_per_member = {}
        self.pending_lock = Lock()
        self.exit = False
        self.members = {}
        self.members_lock = Lock()
        self.working_set = {}
        self.working_set_lock = Lock()
        Thread(target=self.member_updater, name=None, args=(),daemon=True).start()
        Thread(target=self.chat_pusher, name=None, args=(),daemon=True).start()
        Thread(target=self.process_incoming, name=None, args=(),daemon=True).start()

    def handle_msg(self,msg):
        self.incoming_msg_q.put(msg)

    def process_incoming(self):
        while not self.exit:

            while True:
                with self.pending_lock:
                    try:
                        top_itm = self.pending_msg_pool.top()
                        if not self.pending_msg_pool[top_itm][1]:
                            break
                        self.pending_msg_pool.pop()
                        txt,ts = self.pending_per_member[top_itm[0]][top_itm[1]]
                        del self.pending_per_member[top_itm[0]][top_itm[1]]
                        OutputHandler.print_msg("'{}' in room '{}' says:: {}".format(top_itm[0],self.room_name,txt),ts)
                    except KeyError:
                        break

            msg = self.incoming_msg_q.get()
            if self.exit:break
            purp = msg["purpose"]
            # self.pending_per_member = {"orestarod":{1:("Some text 1",timestamp),2:("Some text 2",timestamp)} , "airmper":{1:("airmper text 1",timestamp),2:("airmper text 2",timestamp)}}
            # Pool elements:
            # (sender username, msg id):(priority_num,deliverable,prop_id)

            if purp == "ask_vote":
                with self.members_lock:
                    if msg["username"] not in self.members:
                        continue
                    with self.pending_lock:
                        if ( msg["username"] , msg["msg_id"] ) not in self.pending_msg_pool:
                            self.s += 1
                            self.pending_msg_pool[( msg["username"] , msg["msg_id"] )] = (self.s,False,StateHolder.id)
                            self.pending_per_member[msg["username"]][msg["msg_id"]] = (msg["text"],msg["timestamp"])
                        out_msg = {}
                        out_msg["purpose"] = "vote"
                        out_msg["username"] = StateHolder.name
                        out_msg["room_name"] = self.room_name
                        out_msg["msg_id"] = msg["msg_id"]
                        out_msg["priority"]  = self.pending_msg_pool[(msg["username"] , msg["msg_id"])][0]
                        out_msg["proposer_id"] = StateHolder.id        
                        # out_msg = json.dumps(out_msg)
                        UDPbroker.sendUDP((self.members[msg["username"]].ip,self.members[msg["username"]].port,json.dumps(out_msg)))          

            elif purp == "vote":
                with self.working_set_lock:
                    if msg["username"] in self.working_set and msg["msg_id"] == self.counter:
                        voter_username = msg["username"]
                        # voter_msg_id = msg["msg_id"]
                        voter_priority = msg["priority"]
                        voter_id = msg["proposer_id"]
                        self.working_set[voter_username].vote = (voter_priority,voter_id)

            elif purp == "final_sending":
                with self.members_lock:
                    if msg["username"] not in self.members:
                        continue
                    with self.pending_lock:
                        if (msg["username"],msg["msg_id"]) in self.pending_msg_pool:
                            self.s = max(self.s,msg["priority"])
                            self.pending_msg_pool[(msg["username"],msg["msg_id"])] = (msg["priority"],True,msg["proposer_id"])
                        out_msg = {}
                        out_msg["purpose"] = "final_received_confirm"
                        out_msg["username"] = StateHolder.name
                        out_msg["room_name"] = self.room_name
                        out_msg["msg_id"] = msg["msg_id"]      
                        # out_msg = json.dumps(out_msg)
                        UDPbroker.sendUDP((self.members[msg["username"]].ip,self.members[msg["username"]].port,json.dumps(out_msg)))  
                            
            elif purp == "final_received_confirm":
                with self.working_set_lock:
                    if msg["username"] in self.working_set and msg["msg_id"] == self.counter:
                        voter_username = msg["username"]
                        self.working_set[voter_username].confirmed = True

    def chat_pusher(self):
        while not self.exit:
            my_msg = self.my_messages_q.get()
            self.counter+=1
            with self.members_lock:
                with self.working_set_lock:
                    self.working_set = copy.deepcopy(self.members)
            # The operation for a new chat message starts!
            # phase 1
            found = 1
            timestamp = time.time()
            while (not self.exit) and found > 0:
                with self.working_set_lock:
                    found = 0
                    out_msg = {}
                    out_msg["purpose"] = "ask_vote"
                    out_msg["text"] = my_msg
                    out_msg["username"] = StateHolder.name
                    out_msg["room_name"] = self.room_name
                    out_msg["msg_id"] = self.counter
                    out_msg["timestamp"] = timestamp
                    for member in self.working_set:
                        if not self.working_set[member].vote:
                            found+=1
                            UDPbroker.sendUDP((self.working_set[member].ip,self.working_set[member].port,json.dumps(out_msg)))
                time.sleep(0.001)
            max_priority = -1
            min_id = -1

            if not self.exit:
                with self.working_set_lock:
                    for member in self.working_set:
                        if (self.working_set[member].vote[0]>max_priority) or ((self.working_set[member].vote[0]==max_priority) and (self.working_set[member].vote[1]<min_id)):
                            max_priority,min_id = self.working_set[member].vote
            found = 1
            while (not self.exit) and found > 0:
                with self.working_set_lock:
                    found = 0
                    for member in self.working_set:
                        if not self.working_set[member].confirmed:
                            found+=1
                            out_msg = {}
                            out_msg["purpose"] = "final_sending"
                            out_msg["username"] = StateHolder.name
                            out_msg["room_name"] = self.room_name
                            out_msg["msg_id"] = self.counter
                            out_msg["priority"] = max_priority
                            out_msg["proposer_id"] = min_id
                            UDPbroker.sendUDP((self.working_set[member].ip,self.working_set[member].port,json.dumps(out_msg)))
                time.sleep(0.001)
            


                    
    
    def chat_msg(self,msg_txt):
        self.my_messages_q.put(msg_txt)

    def member_updater(self): #daemon thread
        while not self.exit:
            response = server_request("/list_members/{}".format(self.room_name))
            with self.members_lock:
                to_be_deleted = []
                for member in self.members:
                    if member not in map(lambda x:x["username"],response):
                        to_be_deleted.append(member)
                with self.working_set_lock:
                    for member in to_be_deleted:
                        # self.members[member].exit_member()
                        if member in self.working_set:
                            del self.working_set[member]
                        del self.members[member]
                with self.pending_lock:
                    for member in to_be_deleted:
                        if member in self.pending_per_member:
                            for msg_id in self.pending_per_member[member]:
                                del self.pending_msg_pool[(member,msg_id)]
                            del self.pending_per_member[member]
                    for member in response:
                        if member["username"] not in self.members:
                            self.members[member["username"]] = self.member_struct(member)
                            self.pending_per_member[member["username"]]={}
            time.sleep(0.3)



    def kill_room(self):
        self.exit = True
        self.my_messages_q.put("dummy")
        self.incoming_msg_q.put({})

class StateHolder:
    """
    The main element holding the state of the program.
    Will also hold the room structures, which are to be defined,
    and on which the chat exchange actions will operate
    """
    name=None
    id=-1
    rooms = {}
    current_room = None
    server_ip = None
    my_ip = None
    udp_listen_port = None
    exitt = False
    rooms_lock = Lock()
    heartbeat_flag = []
    # room_type = roomFIFO
    room_type = roomTotal

    @classmethod
    def get_info(cls):
        """ Get a string with info about program state"""
        res = ""
        res += "Name = {}, ID = {}, My IP = {}, UDP Listen = {}, Current room = {},Server IP = {}".format(
                                                                cls.name,
                                                                "[Not Set]" if cls.id == -1 else cls.id,
                                                                cls.my_ip,
                                                                cls.udp_listen_port,
                                                                cls.current_room,
                                                                cls.server_ip)
        res += "\n\r   Chat groups participating in: {}".format(str(list(cls.rooms)))
        return res

    @classmethod
    def join_room(cls,room_name):
        with cls.rooms_lock:
            if room_name not in cls.rooms:
                cls.rooms[room_name] = cls.room_type(room_name)
    
    @classmethod
    def exit_room(cls,room_name):
        with cls.rooms_lock:
            if room_name in cls.rooms:
                cls.rooms[room_name].kill_room()
                del cls.rooms[room_name]
                if cls.current_room == room_name:
                    cls.current_room = None

    @classmethod
    def msg_to_room(cls,msg):
        with cls.rooms_lock:
            try:
                room_name = msg["room_name"]
                del msg["room_name"]
                if room_name in cls.rooms:
                    cls.rooms[room_name].handle_msg(msg)
            except:
                pass
    
    @classmethod
    def chat_message(cls,txt):
        with cls.rooms_lock:
            if cls.current_room is not None:
                cls.rooms[cls.current_room].chat_msg(txt)

    @classmethod
    def exit_all_rooms(cls):
        rooms = None
        with cls.rooms_lock:
            rooms = list(cls.rooms)
        for room_name in rooms:
            cls.exit_room(room_name)

    @classmethod
    def start_heartbeat(cls):
        cls.heartbeat_flag = [True]
        Thread(target=cls.heartbeat, name=None, args=(cls.heartbeat_flag,),daemon=True).start()

    @classmethod
    def heartbeat(cls,flag):
        # flag = flag_list[0]
        # OutputHandler.print("This is my flag list"+str(flag_list))
        while (flag[0]):
            server_request("/heartbeat/{}".format(cls.id))
            time.sleep(0.3)

    @classmethod
    def stop_heartbeat(cls):
        cls.heartbeat_flag[0] = False
        cls.heartbeat_flag = [False]

    @classmethod
    def flag_exit(cls):
        """ Flag that an exit is decided. The next quit will result in a
            state clearance
        """
        cls.exitt = True

class UDPbroker:
    in_queue = queue.Queue(0) # Each element is just a string
    out_queue = queue.Queue(0) # Each element is of type (ip,port,msg)

    @classmethod
    def getIncoming(cls):
        insock = socket.socket(socket.AF_INET, # Internet
                    socket.SOCK_DGRAM) # UDP
        insock.bind(("0.0.0.0",StateHolder.udp_listen_port))
        while True:
            data, addr = insock.recvfrom(1024)
            cls.in_queue.put(data.decode("utf-8"))
    
    @classmethod
    def process_in_queue(cls):
        while True:
            try:
                msg = json.loads(cls.in_queue.get())
                StateHolder.msg_to_room(msg)
            except:
                pass
            # OutputHandler.print(msg)

    
    @classmethod
    def process_out_queue(cls):
        out_sock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_DGRAM) # UDP
        while True:
            ip,port,msg = cls.out_queue.get() # (ip,port,msg)
            msg = bytes(msg,"utf-8")
            out_sock.sendto(msg, (ip, port))

    @classmethod
    def sendUDP(cls,element):
        """Push element of shape (ip,port,message) to UDP output queue"""
        cls.out_queue.put(element)
        Benchmark.add_udp()
            
    @classmethod
    def initialize(cls):

        Thread(target=cls.getIncoming, name=None, args=(),daemon=True).start()
        Thread(target=cls.process_in_queue, name=None, args=(),daemon=True).start()
        # cls.out_queue.put(("0.0.0.0",5001,"Lulz I mssaged myself"))
        Thread(target=cls.process_out_queue, name=None, args=(),daemon=True).start()

class Benchmark:
    bench_start = 0.0
    bench_end = 0.0
    udp_msgs = 0
    udp_lock = Lock()
    msg_lock = Lock()
    txt_msg_num = 0
    total_latency = 0.0
    msg_file = ""
    room_type = ""
    bench_name= "some_benchmark"

    @classmethod
    def add_udp(cls):
        with cls.udp_lock:
            cls.udp_msgs+=1
    
    @classmethod
    def add_msg(cls,lat,end):
        with cls.msg_lock:
            cls.txt_msg_num+=1
            cls.total_latency+=lat
            cls.bench_end = max(end,cls.bench_end)
    
    @classmethod
    def schedule_benchmark(cls):
        waittime = cls.bench_start - time.time()
        if waittime>=0:
            Timer(waittime,cls.feed_chat).start()
    
    @classmethod
    def feed_chat(cls):
        msg_list = []
        if cls.msg_file != "":
            with open(cls.msg_file) as f:
                msg_list = f.readlines()
            for msg in msg_list:
                msg = msg.replace("\n","")
                CommandHandler.pushCommand(msg)
        time.sleep(5)
        f = open("benchmarks/{}_{}_{}.txt".format(StateHolder.name,Benchmark.room_type,Benchmark.bench_name),"w")
        f.write("Throughput: {}\n".format(cls.txt_msg_num/(cls.bench_end-cls.bench_start)))
        f.write("Mean Latency: {}\n".format(cls.total_latency/cls.txt_msg_num))
        f.write("UDP messages: {}\n".format(cls.udp_msgs))
        f.close()

        # f = open("bench_outputs/{}_{}_{}.txt".format(StateHolder.name,Benchmark.room_type,Benchmark.bench_name),"w")

        os._exit(0)



def initialize():
    """Do all necessary actions before input loop starts"""
    isbench = False
    # udp,register,server,room
    arg_dict = get_args()
    if "udp" in arg_dict and arg_dict["udp"].isdigit():
        StateHolder.udp_listen_port = int(arg_dict["udp"])
    else:
        StateHolder.udp_listen_port = 5001

    if "server" in arg_dict:
        StateHolder.server_ip = arg_dict["server"]
    else:
        StateHolder.server_ip = '0.0.0.0:5000'

    if "mode" in arg_dict:
        if arg_dict["mode"] == "total":
            StateHolder.room_type = roomTotal
            Benchmark.room_type = "total"
        else: # arg_dict["mode"] == "fifo":
            StateHolder.room_type = roomFIFO
            Benchmark.room_type = "fifo"
    else:
        StateHolder.room_type = roomFIFO
        Benchmark.room_type = "fifo"
    
    if "msgfile" in arg_dict:
        Benchmark.msg_file = arg_dict["msgfile"]
    
    if "benchname" in arg_dict:
        Benchmark.bench_name = arg_dict["benchname"]

    if "start" in arg_dict:
        isbench = True
        isfloat = False
        try:
            float(arg_dict["start"])
            isfloat = True
        except ValueError:
            pass
        
        if isfloat:
            Benchmark.bench_start = float(arg_dict["start"])
            Benchmark.schedule_benchmark()

    # StateHolder.server_ip = '0.0.0.0:5000'
    # StateHolder.udp_listen_port = 5001 if len(sys.argv) < 2 else int(sys.argv[1])
    OutputHandler.initialize()
    CommandHandler.initialize()
    UDPbroker.initialize()
    print(">> Welcome to the chat client! Press `!h` for help.")
    print(InputHandler.prompt_msg,end="")
    sys.stdout.flush()

    if "register" in arg_dict:
        CommandHandler.pushCommand("!register {}".format(arg_dict["register"]))
    if "room" in arg_dict:
        CommandHandler.pushCommand("!j "+arg_dict["room"])
        CommandHandler.pushCommand("!w "+arg_dict["room"])
    # time.sleep(1)
    # CommandHandler.pushCommand("!register {}".format(arg_dict["register"]))

    return isbench

def get_args():
    arg_pairs = list(map(lambda x:x.split("="),[x for x in sys.argv[1:] if x.count("=") == 1]))
    arg_dict = {}
    for par in arg_pairs:
        arg_dict[par[0]] = par[1]
    return arg_dict
        
if __name__ == "__main__":
    isbench = initialize()
    if not isbench:
        getch = _Getch()
        while(True):
            # pass
            ch=getch()
            InputHandler.handle_input(ch)
    else:
        pass
