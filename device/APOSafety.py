from socket import *
import pdb
from datetime import datetime
import time
from logging import Logger
import re
import timer

messout = b"all"

class Safety :

    def __init__(self, logger=None, use35m=True, use25m=True, warnonly=False) :
        """  Initialize safety properties and capabilities
        """
        self.connected = True
        self.use35m = use35m
        self.use25m = use25m
        self.warnonly = warnonly
        self.override_timer = None
        self.override_time = 0

    def setoverride(self,time) :
        self.override_timer = timer.Timer()
        self.override_timer.start()
        self.override_time = time

    def override(self) :
        if (self.override_timer is not None and 
            self.override_timer.elapsed()<self.override_time ) :
            # if we have a timer set and overrid time hasn't expired 
            return True
        elif self.override_timer is not None :
            # if we've passed override time, dispose of timer 
            self.override_timer = None
        return False


    def old_override(self,verbose=False) :
        """ Get override from 10.75.0.19
        """

        sock = socket(AF_INET, SOCK_DGRAM)
        sock.settimeout(2)
        sock.sendto(messout, ('10.75.0.19', 6251))
        messin='close'
        try: 
            messin, server = sock.recvfrom(1024)
            messin=messin.decode()
        except timeout: 
            pass
        sock.close()
        if messin == 'open' : return True
        else : return False

    def stat(self,verbose=False) :
        """ Get 3.5m and 2.5m status from 10.75.0.152
        """
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.sendto(messout, ('10.75.0.152', 6251))
        messin, server = sock.recvfrom(1024)
        sock.close()
        messin=messin.decode()

        # strip off beginning.
        # replace = with =', and replace space with space'
        # for example dewPoint=14.0 becomes dewPoint='14.0'
        start = messin.find('timeStamp')
        stop = messin.find('end')
        stuff = messin[start:stop].replace ("=","='").replace (" ","'; ")

        # exec - causes the pieces to become global variables
        ldict={}
        exec(stuff,globals(),ldict)
        encl35m=ldict['encl35m']
        encl25m=ldict['encl25m']
        if verbose:
            print('encl35m: {:s}  encl25m: {:s}'.format(encl35m,encl25m))

        try:
            encl35m
        except NameError:
            encl35m = "-1"

        safe35m = False
        if ( encl35m == "-1" ) :
            stat35m="unknown"
        elif ( encl35m == "open" ) :
            stat35m="open"
        else:
            stat35m="closed"

        try:
            encl25m
        except NameError:
            encl25m = "-1"

        safe25m = False
        #print('encl25m: ', encl25m)
        if ( encl25m == "-1" ) :
            stat25m="unknown"
            if self.use25m : safe=False
        elif ( encl25m == "1" ) :
            stat25m="open"
        else:
            stat25m="closed"

        return stat35m, stat25m

    def oldencl25Open(self,verbose=False):
        """ Get 2.5m status from 10.25.1.139
        """
        try :
            s = socket()
            s.connect(('10.25.1.139', 9990))
            s.send(b'status\n')
            time.sleep(1)
            reply=s.recv(4096)
            if (verbose) : print(reply)
            stat25m = bool(int(re.search('encl25m=([0|1])', reply.decode()).group(1)))
            if stat25m : return "open"
            else : return "closed"
        except :
            return "unknown"

    def encl25Open(self,verbose=False) :

        conn = create_connection(("10.25.1.139", 19991))
        buffer = b""

        while True:
            data = conn.recv(1024)
            buffer += data

            if b"\n" in data:
                response = eval(buffer[0 : buffer.index(b"\n")].decode())
                buffer = buffer[buffer.index(b"\n") + 1 :]
                break
        
        bldg_clear_az = (response["plc_words_158"] & 0x10) != 0
        bldg_clear_alt = (response["plc_words_157"] & 0x02) != 0

        if bldg_clear_az & bldg_clear_alt:
            return "open"  # 1 means open

        return "closed"  # 0 means closed


    def issafe(self,verbose=False) :
        """ Return whether is safe to be open based on 3.5m/2.5m as set up
        """
        try: stat35m, stat25m = self.stat(verbose=verbose)
        except : stat35m = 'unknown'
        try :stat25m = self.encl25Open(verbose=verbose)
        except : stat25m = 'unknown'

        safe25m = False
        safe35m = False
        if stat35m == "open" : safe35m = True
        if stat25m == "open" : safe25m = True

        now=datetime.now()
        print("Enclosure: 3.5m",stat35m,", 2.5m",stat25m,", override",self.override(), " at",now.strftime("%d/%m/%Y %H:%M:%S"))

        if self.override() or self.warnonly: return True

        if self.use35m and self.use25m :
            return safe35m or safe25m
        elif self.use35m :
            return safe35m
        elif self.use25m :
            return safe25m
        else :
            return False

