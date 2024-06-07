repository for communicating with Bronkhorst MFCs remotely. Intended to be used with Pylatus or similar scripting environment. To install, clone the repository, then run 'pip install -e .' inside. This will create the bronkhorstServer program. Can also get from PyPi, 'pip install bronkhorstControlbm31'

Usage: On the PC connected to the MFCs run bronkhorstServer in a terminal. Options are -c/--com input the com number as an integer (default 1, but check com ports in Device Manager), this will save next time you run so you shouldn't need to input it again. -p/--port port number, (default is value in the script, probably unnecessary to change). A positional argument which can be 'local' ('localhost'), 'remote' (hostname), or remoteip (ip address) (default local). If remote the hostname will be displayed to connect from another computer, otherwise it will be 'localhost'. The port number will also be displayed.

The best way to run is to use the multi client server e.g.

bronkhorstMultiServer remote -c 7

Use remoteip or the IP address itself instead of remote to use the IP address as the hostname, sometimes it works better in cases where the PC has multiple connections.

To send commands import the MFCclient class and connect function, then run it's methods. Initial arguments are MFC address (will be an integer), the IP address (default localhost) and the port (default is that in the script). 

E.g.

from bronkhorstControlbm31 import MFCclient

MFCclient(3,'\<hostname or ip address\>').pollAll() 

(this gives information about all MFCs that are connected in a dataframe, the MFC address isn't used and can be anything in this case). 

To change setpoint on MFC address 3:

MFCclient(3,'\<hostname or ip address\>').writeSetpoint(value)

There are also 2 other programs called barPlot and timePlot which can be run in conjunction with the bronkhorstMultiServer. Takes host as a positional argument (default 'localhost'). Run e.g. 'timePlot \<hostname\>'

I should mention this article https://realpython.com/python-sockets/ and the associated repository which helped me to make this.

Can also be controlled more directly, without the server, using the MFC class in the bronkhorst.py module, but the plotting programs won't work in that case, and it must be on the same PC as the MFCs. e.g.

from bronkhorstControlbm31.bronkhorst import MFC, startMfc

mfcmain = startMfc()

mfc1 = MFC(1,mfcmain)

mfc1.readName()
