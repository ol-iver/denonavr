# denonavr
[![Version](https://img.shields.io/badge/version-v0.10.8.dev1-orange.svg)](https://github.com/scarface-4711/denonavr)
[![Build Status](https://travis-ci.com/scarface-4711/denonavr.svg?branch=master)](https://travis-ci.com/scarface-4711/denonavr)
[![PyPi](https://img.shields.io/pypi/v/denonavr.svg)](https://pypi.org/project/denonavr)
[![License](https://img.shields.io/github/license/scarface-4711/denonavr.svg)](LICENSE)

Automation Library for Denon AVR receivers - current version 0.10.8.dev1

## Important change

This library switched to async in version 0.10.0.
All sync methods are still available for a while in order not to break too many things. However using those methods is ineffecient, because they use the corresponding async methods by starting and stopping an own asyncio event loop for each command. Please switch to `async_` methods instead.

There are a few changes.

When you create a new instance of `DenonAVR` there are no API calls anymore in order to not blocking things in this case. For an initial setup where things like type of your receiver is determined you can call `(async_)setup()` and `(async_)update()`to populate the attributes. Calling `(async_)update()` invokes a call of `async_setup()` if the instance was not setup yet.

The methods do not return True or False anymore. If they run successfull, they return `None`. Otherwise, an exception from a class you find in `denonavr/exceptions.py` is raised.

It is not longer assumed that a command was successfull even when the receiver returns a HTTP 200. The reason is that this information is not reliable and the receivers return HTTP 200 at some endpoints even when a call failed. As an example, from now on you have to call `(async_)update()` aftern you called `(async_)power_off()` to see the `power` attribute changing.

## Installation

Use pip:

```$ pip install denonavr```

or 

```$ pip install --use-wheel denonavr```
  
## Usage

For creation of a device you could use the following lines of codes
```
import denonavr
d = denonavr.DenonAVR("192.168.0.250", "Name of device (Optional)")
```
Library is not polling the Denon device. Thus you need to update device information using the update method.
```
d.update()
```
Some basic automatic discovery functions for uPnP devices using SSDP broadcast are available.
It is either possible to just discover the Denon AVR devices in the LAN zone or to create instances for each discovered device directly.
```
discovered_devices = denonavr.discover()
instanced_devices = denonavr.init_all_receivers()
```

In addition to the Main Zone which is always started, Zone2 and Zone3 of the receiver can be started assigning a dictionary to the add_zones parameter when creating the instance of the receiver.
```
import denonavr
zones = {"Zone2": "Name of Zone2", "Zone3": "Name of Zone 3"}
d = denonavr.DenonAVR("192.168.0.250", name="Name of Main Zone", add_zones=zones)
```

Each Zone is represented by an own instance which is assigned to the device instance by the zones attribute with type dictionary.
```
d.zones
{'Zone2': <denonavr.denonavr.DenonAVRZones object at 0x000001F893EB7630>, 'Main': <denonavr.denonavr.DenonAVR object at 0x000001F8964155F8>, 'Zone3': <denonavr.denonavr.DenonAVRZones object at 0x000001F896415320>}
```

Some code examples for the Main Zone:
```
>>> import denonavr
>>> d = denonavr.DenonAVR("192.168.0.250")
>>> d.update()
>>> d.power
'STANDBY'
>>> d.power_on()
>>> d.update()
>>> d.power
'ON'
>>> d.name
'Denon AVR-X4100W'
>>> d.artist
'Wynton Marsalis'
>>> d.title
"When It's Sleepytime Down South"
>>> d.image_url
'http://192.168.0.250/NetAudio/art.asp-jpg?1480031583'
>>> d.next_track()
>>> d.previous_track()
>>> d.volume
-43.5
>>> d.volume_up()
>>> d.update()
>>> d.volume
-43.0
>>> d.volume_down()
>>> d.set_volume(-40.0)
>>> d.update()
>>> d.volume
-40.0
>>> d.mute(True)
>>> d.mute(False)
>>> d.toggle_play_pause()
>>> d.toggle_play_pause()
>>> d.input_func
'Online Music'
>>> d.input_func_list
['AUX', 'AUX2', 'Blu-ray', 'Bluetooth', 'CBL/SAT', 'CD', 'DVD', 'Game', 'Internet Radio', 'Media Player', 'Media Server', 'Online Music', 'Phono', 'TV Audio', 'Tuner', 'iPod/USB']
>>> d.input_func = "Tuner"
>>> d.input_func
'Tuner'
>>> d.power_off()

>>> discovered_devices = denonavr.discover()
discovered_devices
[{'friendlyName': 'Denon AVR-X4100W', 'host': '192.168.0.250', 'modelName': '*AVR-X4100W', 'presentationURL': 'http://192.168.0.250'}]
>>> discovered_denon = denonavr.DenonAVR(discovered_devices[0]['host'])
>>> discovered_denon.power
'STANDBY'

>>> instanced_devices = denonavr.init_all_receivers()
>>> instanced_devices
[<denonavr.denonavr.DenonAVR object at 0x000001AF8EA63E10>]
>>> instanced_devices[0].update()
>>> instanced_devices[0].power
'STANDBY'
>>> instanced_devices[0].power_on()
>>> instanced_devices[0].update()
>>> instanced_devices[0].power
'ON'
>>> instanced_devices[0].power_off()
>>> instanced_devices[0].update()
>>> instanced_devices[0].power
'STANDBY'
```

The code examples for the Main Zone instance d from above are working for all zones. The other zones (and Main Zone as well) could be accessed via zones attribute.
```
d.zones['Zone2'].power
'OFF'
d.zones['Zone2'].power_on()
d.zones['Zone2'].update()
d.zones['Zone2'].power
'ON'
d.zones['Zone2'].power_off()
d.zones['Zone2'].update()
d.zones['Zone2'].power
'OFF
```

## Collection of HTTP calls
For a collection of HTTP calls for Denon receivers please have a look at the `doc` folder.

## License
MIT

## Author
@scarface-4711: https://github.com/scarface-4711

## Contributors
@soldag: https://github.com/soldag  
@shapiromatron: https://github.com/shapiromatron  
@glance-: https://github.com/glance-  
@p3dda: https://github.com/p3dda  
@russel: https://github.com/russell  
@starkillerOG: https://github.com/starkillerOG  
@andrewsayre: https://github.com/andrewsayre  
@JPHutchins: https://github.com/JPHutchins  
@MarBra: https://github.com/MarBra  

## Users
Home Assistant: https://github.com/home-assistant/home-assistant/
