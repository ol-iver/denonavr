# denonavr
[![Build Status](https://travis-ci.org/scarface-4711/denonavr.svg?branch=master)](https://travis-ci.org/scarface-4711/denonavr)

Automation Library for Denon AVR receivers - current version 0.5.3

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
>>> d.power
'STANDBY'
>>> d.power_on()
True
>>> d.update()
True
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
True
>>> d.previous_track()
True
>>> d.volume
-43.5
>>> d.volume_up()
True
>>> d.update()
True
>>> d.volume
-43.0
>>> d.volume_down()
True
>>> d.set_volume(-40.0)
True
>>> d.update()
True
>>> d.volume
-40.0
>>> d.mute(True)
True
>>> d.mute(False)
True
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
>>> instanced_devices[0].power
'STANDBY'
>>> instanced_devices[0].power_on()
True
>>> instanced_devices[0].update()
True
>>> instanced_devices[0].power
'ON'
>>> instanced_devices[0].power_off()
True
>>> instanced_devices[0].power
'STANDBY'
```

The code examples for the Main Zone instance d from above are working for all zones. The other zones (and Main Zone as well) could be accessed via zones attribute.
```
d.zones['Zone2'].power
'OFF'
d.zones['Zone2'].power_on()
True
d.zones['Zone2'].update()
True
d.zones['Zone2'].power
'ON'
d.zones['Zone2'].power_off()
True
d.zones['Zone2'].update()
True
d.zones['Zone2'].power
'OFF
```

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

## Users
Home Assistant: https://github.com/home-assistant/home-assistant/
