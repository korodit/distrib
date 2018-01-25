import sys
from string import printable
from threading import Thread, Lock
import time
import queue

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
    prompt_msg = ":> "
    default_prompt_msg = ":> "
    output_pudding = "|| "

    @classmethod
    def handle_input(cls,ch):
        with UIHandler.ui_mutex:
        
            if ord(ch)==3:# ctrl+c
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
            "newname":cls.newname
        }
    
    # What happens when the user simply inputs text
    # - should default to sending to active room?
    @classmethod
    def chat(cls,param):
        OutputHandler.print("( Warning: No Chat supported yet :( )")

    # Echoes a message, for testing purposes
    @classmethod
    def echo(cls,param):
        OutputHandler.print(param)
    
    # Test method, adds user name to start of prompt
    @classmethod
    def newname(cls,param):
        with UIHandler.ui_mutex:
            InputHandler.prompt_msg = "["+param+"]"+InputHandler.default_prompt_msg
        OutputHandler.outputQueue.put("( Notification: Name changed! )")

# Do all necessary actions before input loop starts
def initialize():
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
