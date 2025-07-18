Repository for a client/server program for communicating with Bronkhorst MFCs remotely. Intended to be used with Pylatus or similar scripting environment. To install, clone the repository, then run 'pip install -e .' inside. This will create the bronkhorstServer program. Can also get from PyPi, 'pip install bronkhorstControlbm31'. Uses the Bronkhorst propar library. Also requires pandas, matplotlib and PyQt6.

Usage: On the PC connected to the MFCs run bronkhorstServer in a terminal. Options are -c/--com input the com number as an integer (default 1, but check com ports in Device Manager), this will save next time you run so you shouldn't need to input it again. -p/--port port number, (default is value in the script, probably unnecessary to change). A positional argument which can be 'local' ('localhost'), 'remote' (hostname), or remoteip (ip address) (default local). If remote the hostname will be displayed to connect from another computer, otherwise it will be 'localhost'. The port number will also be displayed.

The best way to run is to use the multi client server e.g.
```
bronkhorstServer remote -c 7
```
remoteip, the hostname/ hostname.domain (e.g. format: pcname.company.countrycode) or the IP address itself can be used instead of remote to help specify the hostname, sometimes it works better in cases where the PC has multiple connections.

Use ctrl+c to close the server. May take 5 s to take effect.

To send commands import the MFCclient class and connect function, then run it's methods. Initial arguments are MFC address (will be an integer), the IP address (default localhost) and the port (default is that in the script). 

E.g.
```python
from bronkhorstControlbm31 import MFCclient

MFCclient(3,'<hostname or ip address>').pollAll() 
```
(this gives information about all MFCs that are connected in a dataframe, the MFC address isn't used and can be anything in this case). 

To change setpoint on MFC address 3:
```python
MFCclient(3,'<hostname or ip address>').writeSetpoint(value)
```

There is a gui called mfcgui (still must be used in conjuction with bronkhorstServer). Run in the terminal. There is one option: -m/--maxMFCs - the maximum number of MFCs that may be needed (sets the number of columns of widgets, doesn't matter if it's more than you have), by default this is 10, if you have more, or want to reduce it to make it cleaner, run with the specific number you want. e.g. for 15 MFCs:
```
mfcgui -m 15
```

<img width="799" height="578" alt="image" src="https://github.com/user-attachments/assets/6fe75069-f66e-450c-8915-dda187c5501f" />

When plot data is checked, the following data will be plotted:

![plotter](https://github.com/user-attachments/assets/9f26bbf2-cbeb-4d9d-994d-d15f480fcfa3)

There is a 'reset axes' box on the plotter. If this is checked, the axes for the time plotters will always reset to show all the data. If unchecked, it allows you to zoom into a region, and it will stay there until the box is checked again. If the graph is not zoomed in, the axes will reset as more data comes in.

The GUI also logs the measure values and setpoints every 5 seconds. This is saved in the \<home>/bronkhorstClientLog/ folder.

There are also 3 plotting programs which can be run independently of the GUI, called barPlot, timePlot, and mfcPlotAll which can be run in conjunction with the bronkhorstServer. Takes host as a positional argument (default 'localhost'). Run e.g. 'timePlot \<hostname\>'. Use --help to display options. mfcPlotAll plots the same data as the GUI. timePlot and mfcPlotAll also log the data.

Can also be controlled more directly, without the server, using the MFC class in the bronkhorst.py module, but the GUI and plotting programs won't work in that case, and it must be on the same PC as the MFCs. e.g.
```python
from bronkhorstControlbm31 import MFC, startMfc

mfcmain = startMfc('COM3')
mfc1 = MFC(1,mfcmain)
mfc1.readName()
```

I should mention this article https://realpython.com/python-sockets/ and the associated repository which helped me to make this.
