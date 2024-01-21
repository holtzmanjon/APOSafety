from socket import *
from datetime import datetime
import time
from logging import logger

messout = b"all"

class Safety :

    def __init__(self, logger : Logger, use35m=True, use25m=False) :
        """  Initialize safety properties and capabilities
        """
        self.connected = True
        self.use35m = use35m
        self.use25m = use25m

    def issafe(self) :

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
        exec(stuff)

        try:
            encl35m
        except NameError:
            encl35m = "-1"

        safe35m = False
        if ( encl35m == "-1" ) :
            stat35m="unknown"
        elif ( encl35m == "open" ) :
            stat35m="open"
            safe35m = True
        else:
            stat35m="closed"

        try:
            encl25m
        except NameError:
            encl25m = "-1"

        safe25m = False
        if ( encl25m == "-1" ) :
            stat25m="unknown"
            if self.use25m : safe=False
        elif ( encl25m == "16" ) :
            stat25m="open"
            safe25m = True
        else:
            stat25m="closed"

        now=datetime.now()
        print("Enclosure: 3.5m",stat35m,", 2.5m",stat25m, "at",now.strftime("%d/%m/%Y %H:%M:%S"))

        if self.use35m and self.use25m :
            return safe35m and safe25m
        elif self.use35m :
            return safe35m
        elif self.use25m :
            return safe25m
        else :
            return False
 
