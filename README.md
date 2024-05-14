repository for communicating with Bronkhorst MFCs remotely. Intended to be used with Pylatus or similar scripting environment. To install, clone the repository, then run 'pip install -e .' inside. This will create the bronkhorstServer program.

Usage: On the PC connected to the MFCs run bronkhorstServer in a terminal. Options are -c/--com input the com number as an integer (default 1, but check com ports in Device Manager), this will save next time you run so you shouldn't need to input it again. -p/--port port number, (default is value in the script, probably unnecessary to change). A positional argument which can be 'local' or 'remote' (default local). If remote the IP address will be displayed to connect from another computer, otherwise it will be 'localhost'. The port number will also be displayed.

To send commands import the MFCclient class (from bronkhorstControlbm31.bronkhorstClient import MFCclient), then run it's methods. Initial arguments are MFC address (will be an integer), the IP address (default localhost) and the port (default is that in the script). 

E.g.

MFCclient(3,\<ip address\>).pollAll() 

(this gives information about all MFCs that are connected in a dataframe, the MFC address isn't used and can be anything in this case). 

To change setpoint :

MFCclient(3,\<ip address\>).writeSetpoint(value).
