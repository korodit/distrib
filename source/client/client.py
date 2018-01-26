import sys
import os
from string import printable
from threading import Thread, Lock
import time
import queue
import http.client
import json

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

getch = _Getch()

def makerequest(full_address,parameters):
    """Returns a proper object out of a request to the tracker"""
    conn = http.client.HTTPConnection(full_address)
    conn.request("GET", parameters)
    r1 = conn.getresponse()
    data1 = r1.read()
    return json.loads(data1.decode("utf-8"))

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
    def append_input(cls,app): #adds a new string at the end of the current
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
    input_mutex = Lock()
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
    def initializeDict(cls):
        cls.commandDict = {
            "echo":cls.echo,
            "newname":cls.newname,
            "h":cls.help,
            "register":cls.register,
            "q":cls.quit
        }
    
    @classmethod
    def register(cls,param):
        """(username) Register to tracker with the appropriate input"""
        # name = "horestarod2"
        param = param.split(' ')
        if len(param)!=1:
            OutputHandler.print("( Warning: Wrong Arguments! )")
            return
        name = param[0]
        response = makerequest(StateHolder.server_ip,"/register/{}/{}".format(str(StateHolder.udp_listen_port),name))
        if "Error" not in response:
            StateHolder.id = response["id"]
            StateHolder.name = response["username"]
            with UIHandler.ui_mutex:
                InputHandler.prompt_msg = "[{}]:> ".format(StateHolder.name)
            OutputHandler.print("Logged in: id = {}, name = {}".format(str(StateHolder.id),StateHolder.name))
        else:
            OutputHandler.print("Error:"+response["Error"])
    
    @classmethod
    def quit(cls,param):
        """() Quit from tracker and exit program"""
        if StateHolder.id == -1:
            OutputHandler.print("( Warning: You are not logged in! )")
            return
        response = makerequest(StateHolder.server_ip,"/quit/{}".format(str(StateHolder.id)))
        if "Error" not in response:
            with UIHandler.ui_mutex:
                InputHandler.prompt_msg = InputHandler.default_prompt_msg
                StateHolder.id = -1
                StateHolder.name = None
                StateHolder.rooms = {}
                StateHolder.current_room = None
            OutputHandler.print("( Warning: You have been logged out! )")
        else:
            OutputHandler.print("Error:"+response["Error"])

    # What happens when the user simply inputs text
    # - should default to sending to active room?
    @classmethod
    def chat(cls,param):
        """I just chat lulz"""
        OutputHandler.print("( Warning: No Chat supported yet :( )")

    # Echoes a message, for testing purposes
    @classmethod
    def echo(cls,param):
        """(message) Echoes a message to the console"""
        OutputHandler.print(param)
    
    @classmethod
    def help(cls,param):
        """() Prints available commands"""
        comms = "Commands available:"
        for key in cls.commandDict:
            comms+="\r\n\t!"+key+" --> "+cls.commandDict[key].__doc__
        OutputHandler.print(comms)
    
    # Test method, adds user name to start of prompt
    @classmethod
    def newname(cls,param):
        """(newname) Changes the name of the user appearing on the prompt"""
        with UIHandler.ui_mutex:
            InputHandler.prompt_msg = "["+param+"]"+InputHandler.default_prompt_msg
        OutputHandler.outputQueue.put("( Notification: Name changed! )")

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
    udp_listen_port = None

def initialize():
    """Do all necessary actions before input loop starts"""

    StateHolder.server_ip = '0.0.0.0:5000'
    StateHolder.udp_listen_port = 500
    out_thr = Thread(target=OutputHandler.processOutput, name=None, args=(),daemon=True)
    out_thr.start()
    CommandHandler.initializeDict()
    comm_thr = Thread(target=CommandHandler.processQueue, name=None, args=(),daemon=True)
    comm_thr.start()
    print(InputHandler.prompt_msg,end="")
    sys.stdout.flush()



if __name__ == "__main__":
    initialize()
    while(True):
        # pass
        ch=getch()
        InputHandler.handle_input(ch)
