# denonavr
Automation Library for Denon AVR receivers

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
```

## License
MIT

## Author
@scarface-4711: https://github.com/scarface-4711

## Users
Home Assistant: https://github.com/home-assistant/home-assistant/
