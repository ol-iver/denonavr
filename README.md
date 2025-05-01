# denonavr
[![Release](https://img.shields.io/github/v/release/ol-iver/denonavr?sort=semver)](https://github.com/ol-iver/denonavr/releases/latest)
[![Build Status](https://github.com/ol-iver/denonavr/actions/workflows/python-tests.yml/badge.svg)](https://github.com/ol-iver/denonavr/actions/workflows/python-tests.yml)
[![PyPi](https://img.shields.io/pypi/v/denonavr.svg)](https://pypi.org/project/denonavr)
[![License](https://img.shields.io/github/license/ol-iver/denonavr.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Automation Library for Denon AVR receivers

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

### Monitoring with telnet
In addition to retrieving the current device status via HTTP calls, `denonavr` library also has the ability to setup a task that will connect to the receiver via telnet on TCP port 23 and listen for real-time events to notify of status changes.
This provides instant updates via a callback when the device status changes. Receivers support only one active telnet connection.

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
For a collection of HTTP calls for Denon receivers please have a look at the [doc folder](doc/XML_data_dump.txt).

## License
MIT

## Users
Home Assistant: https://github.com/home-assistant/home-assistant/  
denonavr-cli: https://pypi.org/project/denonavr-cli/
