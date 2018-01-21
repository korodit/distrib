import sys
from string import printable
from threading import Thread, Lock
import time

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
    def reset_input(cls,newin): #for Input Handler Only to Call
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
    input_mutex = Lock()
    current_input=""
    prompt_msg = ":> "
    output_pudding = "|| "

    @classmethod
    def handle_input(cls,ch):
        # with(yield from UIHandler.ui_mutex):
        with UIHandler.ui_mutex:
        
            if ord(ch)==3:# ctrl+c
                exit()

            elif ord(ch)==13:# enter
                out=cls.current_input.replace(chr(13),"")
                UIHandler.post(out)
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

# Define a function for the thread
def print_time(delay):
    count = 0
    while count < 5:
        time.sleep(delay)
        count += 1
        with UIHandler.ui_mutex:
            UIHandler.post("agleipse")

if __name__ == "__main__":
    testh = Thread(target=print_time, name=None, args=(2,),daemon=True)
    testh.start()
    print(InputHandler.prompt_msg,end="")
    sys.stdout.flush()
    while(True):
        # pass
        ch=getch()
        InputHandler.handle_input(ch)
