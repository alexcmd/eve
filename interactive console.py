# Credits to wibiti

import sys
import code
import threading
import stackless
import uthread

class wConsole(code.InteractiveConsole):
    def __init__(self, *args, **kwds):
        self.__input = stackless.channel()
        code.InteractiveConsole.__init__(self, *args, **kwds)
        
    def interact(self, banner=None):
        threading.Thread(target=self.__input_loop).start()
        code.InteractiveConsole.interact(self, banner)
        
    def __input_loop(self):
        while 1:
            self.__input.send(raw_input())
        
    def raw_input(self, prompt=None):
        if prompt:
            sys.stdout.write(prompt)
        return self.__input.receive()
        
uthread.new(code.interact, readfunc=lambda p: uthread.CallOnThread(raw_input, args=(p,)))