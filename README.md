# denonTray
This is a simple tool to control your Denon or compatible (e.g. Marantz) receiver remotely
from Windows by placing an icon in the system tray. The options are accessible from the
icon's context menu. Double-clicking the tray icon turns on the receiver.

<a target="_blank" rel="noopener noreferrer" href="https://github.com/robertschulze/denonTray/blob/master/screenshot.png?raw=True"><img src="https://github.com/robertschulze/denonTray/raw/master/screenshot.png?raw=True" alt="Screenshot" width="220"></a>

The tool is based on the [denonavr](https://github.com/scarface-4711/denonavr)
and [infi.systray](https://github.com/Infinidat/infi.systray) packages.

#### Configuration
The configuration is maintained in ```config.yml``` file. 
There is one only one configuration option that needs to be set specifically for your
home network, namely the hostname or IP address of you receiver:

```receiver_address: 192.168.3.46```

#### Installation
1. Install Python
2. Install dependencies, e.g. via
``` pip install denonavr infi.systray ```
3. Download or clone this repository
4. Place your receiver in ```config.yml```, then start ```denonTray.py```