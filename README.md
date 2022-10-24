# denonavr
[![Version](https://img.shields.io/badge/version-v0.10.12-orange.svg)](https://github.com/ol-iver/denonavr)
[![Build Status](https://github.com/ol-iver/denonavr/actions/workflows/python-tests.yml/badge.svg)](https://github.com/ol-iver/denonavr/actions/workflows/python-tests.yml)
[![PyPi](https://img.shields.io/pypi/v/denonavr.svg)](https://pypi.org/project/denonavr)
[![License](https://img.shields.io/github/license/ol-iver/denonavr.svg)](LICENSE)

Automation Library for Denon AVR receivers - current version 0.10.12

## Important changes for version 0.10.0 and above

### async

As of version 0.10.0 and newer, the `denonavr` library has switched to using`async` methods to interact with Denon receivers.

Legacy synchronous methods are still availlable to avoid breaking existing implementations, but may be deprecated in the future.  Switching to `async` methods is recommended.  The existing sync methods are inefficient because they use the corresponding async methods by starting and stopping its own `asyncio` loop for each command.

### Other changes:

When creating a new instance of `DenonAVR` there are no longer any API calls to avoid blocking the event loop. To initialize setup of your receiver you would use`(async_)setup()` and `(async_)update()` methods to populate the attributes. Calling `(async_)update()` invokes a call of `async_setup()` if the instance was not setup yet.

Methods do not return `True` or `False` anymore. If successful,  `None` is returned. Otherwise an exception is raised from a class in [denonavr/exceptions.py](https://github.com/ol-iver/denonavr/blob/master/denonavr/exceptions.py). 

It is no longer assumed that a command was successful even when the receiver returns an `HTTP 200 OK`. This is because the receiver can return an `HTTP 200 OK`  from some endpoints even when the API call has failed. As an example, you now have to call `(async_)update()` after you call `(async_)power_off()` to see the `power` attribute change.

## Installation

Use pip:

```$ pip install denonavr```

or 

```$ pip install --use-wheel denonavr```
  
## Usage with `async`

Writing `async` and `await` methods are outside the scope of the documentation.  You can test `async` usage from the Python REPL.  In a terminal run:

`python3 -m asyncio`

The `asyncio` library should automatically be imported in the REPL.  Import the `denonavr` library and set up your receiver.  If you know the  IP address, enter it below replacing `192.168.1.119`.

```
>>> import asyncio
>>> import denonavr
>>> d = denonavr.DenonAVR("192.168.1.119")
>>> await d.async_setup()
>>> await d.async_update()
>>> print(d.volume)
-36.5
```

### Power & Input
```
>>> await d.async_power_on()
>>> await d.async_update()
>>> d.power
'ON'

>>> await d.async_power_off()
>>> await d.async_update()
>>> d.power
'OFF'

>>> d.input_func
'Tuner'
>>> await d.async_set_input_func("Phono")
>>> d.input_func
'Phono'
```
### Sound
```
>>> await d.async_mute_on(True)
>>> await d.async_mute_off(False)
```

### Other methods

Other `async` methods available include:

* `d.async_bass_down`
* `d.async_bass_up`
* `d.async_treble_down`
* `d.async_treble_up`
* `d.async_volume_down`
* `d.async_volume_up`
* `d.async_set_volume(50)`

## Legacy Usage

Note: Legacy sync methods are still available, but may be deprecated in the future.  It is recommended to use the `async` methods described above.  The existing sync methods in versions 0.9.10 and below are inefficient as they use the corresponding async methods by starting and stopping its own asyncio loop for each command.

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
>>> d.set_input_func("Tuner")
>>> d.update()
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
@ol-iver: https://github.com/ol-iver

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
denonavr-cli: https://pypi.org/project/denonavr-cli/
