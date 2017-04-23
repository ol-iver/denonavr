# denonavr
[![Build Status](https://travis-ci.org/scarface-4711/denonavr.svg?branch=master)](https://travis-ci.org/scarface-4711/denonavr)

Automation Library for Denon AVR receivers - current version 0.4.0

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

Some code examples:
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

## License
MIT

## Author
@scarface-4711: https://github.com/scarface-4711

## Contributors
@soldag: https://github.com/soldag

## Users
Home Assistant: https://github.com/home-assistant/home-assistant/
