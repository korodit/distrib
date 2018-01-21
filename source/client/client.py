import sys
from string import printable


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

current_input = ""
prompt_msg = ":>  "

# print(10*"\n",end="")

getch = _Getch()
prompt_printed = False
def clear_input(outp):
    linelen = (len(current_input)+len(prompt_msg))
    global prompt_printed
    prompt_printed = False
    print("\b"*linelen+" "*linelen+"\b"*linelen+outp)
    sys.stdout.flush()

while(True):
    if not prompt_printed:   
        sys.stdout.write(prompt_msg+"\b")
        sys.stdout.flush()
        prompt_printed = True
    ch=getch()
    if ord(ch)==3:# ctrl+c
        exit()
    elif ord(ch)==13:# enter
        out="|| "
        out+=current_input.replace(chr(13),"")
        clear_input(out)
        current_input = ""

    elif ord(ch)==127 and len(current_input)>0:# backspace
        sys.stdout.write("\r")
        sys.stdout.write(":> "+len(current_input)*" ")
        sys.stdout.write("\r")
        current_input=current_input[:-1].replace(chr(13),"")
        sys.stdout.write(":> "+current_input)
        sys.stdout.flush()
    elif ch in printable or ord(ch)>127: # printable
        current_input+=ch
        sys.stdout.write(ch)
        sys.stdout.flush()