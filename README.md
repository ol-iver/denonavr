# denonavr
[![Release](https://img.shields.io/github/v/release/ol-iver/denonavr?sort=semver)](https://github.com/ol-iver/denonavr/releases/latest)
[![Build Status](https://github.com/ol-iver/denonavr/actions/workflows/python-tests.yml/badge.svg)](https://github.com/ol-iver/denonavr/actions/workflows/python-tests.yml)
[![PyPi](https://img.shields.io/pypi/v/denonavr.svg)](https://pypi.org/project/denonavr)
[![License](https://img.shields.io/github/license/ol-iver/denonavr.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Automation Library for Denon AVR receivers

### TCP monitoring

In addition to retrieving the current device status via HTTP calls, this version also adds the ability to setup a task that will connect to the receiver on TCP port 23 and listen for real-time events to notify of status changes. This provides instant updates via a callback when the device status changes.

## Important changes for version 0.10.0 and above

### async

As of version 0.10.0 and newer, the `denonavr` library has switched to using`async` methods to interact with Denon receivers.

Legacy synchronous methods are still available to avoid breaking existing implementations, but may be deprecated in the future.  Switching to `async` methods is recommended.  The existing sync methods are inefficient because they use the corresponding async methods by starting and stopping its own `asyncio` loop for each command.

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

### Monitoring with TCP
```
>>> import asyncio
>>> import denonavr
>>> d = denonavr.DenonAVR("192.168.1.119")
>>> await d.async_setup()
>>> await d.async_telnet_connect()
>>> await d.async_update()
>>> async def update_callback(zone, event, parameter):
>>>>>> print("Zone: " + zone + " Event: " + event + " Parameter: " + parameter)
>>> d.register_callback("ALL", update_callback)
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
>>> await d.async_mute(True)
>>> await d.async_mute(False)
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
@dcmeglio: https://github.com/dcmeglio  
@bdraco: https://github.com/bdraco  

## Users
Home Assistant: https://github.com/home-assistant/home-assistant/  
denonavr-cli: https://pypi.org/project/denonavr-cli/
