repository for communicating with Bronkhorst MFCs remotely. Intended to be used with Pylatus or similar scripting environment. To install, clone the repository, then run 'pip install -e .' inside. This will create the bronkhorstServer program. Can also get from PyPi, 'pip install bronkhorstControlbm31'

Usage: On the PC connected to the MFCs run bronkhorstServer in a terminal. Options are -c/--com input the com number as an integer (default 1, but check com ports in Device Manager), this will save next time you run so you shouldn't need to input it again. -p/--port port number, (default is value in the script, probably unnecessary to change). A positional argument which can be 'local' ('localhost'), 'remote' (hostname), or remoteip (ip address) (default local). If remote the hostname will be displayed to connect from another computer, otherwise it will be 'localhost'. The port number will also be displayed.

e.g.

bronkhorstServer remote -c 7

Use remoteip instead of remote to use the IP address as the hostname, sometimes it works better.

To send commands import the MFCclient class and connect function, then run it's methods. Initial arguments are MFC address (will be an integer), the IP address (default localhost) and the port (default is that in the script). 

E.g.

from bronkhorstControlbm31.bronkhorstClient import MFCclient


MFCclient(3,'\<hostname or ip address\>').pollAll() 

(this gives information about all MFCs that are connected in a dataframe, the MFC address isn't used and can be anything in this case). 

To change setpoint on MFC address 3:

MFCclient(3,'\<hostname or ip address\>').writeSetpoint(value)

A second server is available for accepting multiple clients:

bronkhorstMultiServer remote

then for the client use multi=True:

MFCclient(3,'\<hostname or ip address\>', multi=True).pollAll()

There are also 2 other functions in bronkhorstClient called barPlot() and timePlot() which can be run in conjunction with the bronkhorstMultiServer. Takes host as a required argument. These are also packaged as executables, so run e.g. 'timePlot \<hostname\>'

I should mention this article https://realpython.com/python-sockets/ and the associated repository which helped me to make this.
