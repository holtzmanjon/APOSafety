from socket import *
import pdb
from datetime import datetime
import time
from logging import Logger
import re

messout = b"all"

class Safety :

    def __init__(self, logger=None, use35m=True, use25m=False) :
        """  Initialize safety properties and capabilities
        """
        self.connected = True
        self.use35m = use35m
        self.use25m = use25m

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
        if ( encl25m == "-1" ) :
            stat25m="unknown"
        elif ( encl25m == "16" ) :
            stat25m="open"
        else:
            stat25m="closed"

        return stat35m, stat25m

    def encl25Open(self,verbose=False):
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

    def issafe(self,verbose=False) :
        """ Return whether is safe to be open based on 3.5m/2.5m as set up
        """
        stat35m, stat25m = self.stat(verbose=verbose)
        stat25m = self.encl25Open(verbose=verbose)

        safe25m = False
        safe35m = False
        if stat35m == "open" : safe35m = True
        if stat25m == "open" : safe25m = True

        now=datetime.now()
        print("Enclosure: 3.5m",stat35m,", 2.5m",stat25m, "at",now.strftime("%d/%m/%Y %H:%M:%S"))

        if self.use35m and self.use25m :
            return safe35m or safe25m
        elif self.use35m :
            return safe35m
        elif self.use25m :
            return safe25m
        else :
            return False



 
