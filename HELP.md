Help on package denonavr:

NAME
    denonavr - Automation Library for Denon AVR receivers.

DESCRIPTION
    :copyright: (c) 2016 by Oliver Goetz.
    :license: MIT, see LICENSE for more details.

PACKAGE CONTENTS
    denonavr
    ssdp

FUNCTIONS
    discover()
        Discover all Denon AVR devices in LAN zone.
        
        Returns a list of dictionaries which includes all discovered Denon AVR
        devices with keys "host", "modelName", "friendlyName", "presentationURL".
        By default SSDP broadcasts are sent up to 3 times with a 2 seconds timeout.
    
    init_all_receivers()
        Initialize all discovered Denon AVR receivers in LAN zone.
        
        Returns a list of created Denon AVR instances.
        By default SSDP broadcasts are sent up to 3 times with a 2 seconds timeout.

DATA
    __title__ = 'denonavr'

VERSION
    0.8.0

====================================================================================

Help on module denonavr.denonavr in denonavr:

NAME
    denonavr.denonavr - This module implements the interface to Denon AVR receivers.

DESCRIPTION
    :copyright: (c) 2016 by Oliver Goetz.
    :license: MIT, see LICENSE for more details.

CLASSES
    builtins.object
        DenonAVR
            DenonAVRZones
    builtins.tuple(builtins.object)
        ReceiverType
        ReceiverURLs
    
    class DenonAVR(builtins.object)
     |  Representing a Denon AVR Device.
     |  
     |  Methods defined here:
     |  
     |  __init__(self, host, name=None, show_all_inputs=False, timeout=2.0, add_zones=None)
     |      Initialize MainZone of DenonAVR.
     |      
     |      :param host: IP or HOSTNAME.
     |      :type host: str
     |      
     |      :param name: Device name, if None FriendlyName of device is used.
     |      :type name: str or None
     |      
     |      :param show_all_inputs: If True deleted input functions are also shown
     |      :type show_all_inputs: bool
     |      
     |      :param add_zones: Additional Zones for which an instance are created
     |      :type add_zones: dict [str, str] or None
     |  
     |  construct_sm_match_dict(self)
     |      Construct the sm_match_dict.
     |      
     |      Reverse the key value structure. The sm_match_dict is bigger,
     |      but allows for direct matching using a dictionary key access.
     |      The sound_mode_dict is uses externally to set this dictionary
     |      because that has a nicer syntax.
     |  
     |  create_zones(self, add_zones)
     |      Create instances of additional zones for the receiver.
     |  
     |  exec_appcommand_post(self, attribute_list)
     |      Prepare and execute a HTTP POST call to AppCommand.xml end point.
     |      
     |      Returns XML ElementTree on success and None on fail.
     |  
     |  get_status_xml(self, command, suppress_errors=False)
     |      Get status XML via HTTP and return it as XML ElementTree.
     |  
     |  match_sound_mode(self, sound_mode_raw)
     |      Match the raw_sound_mode to its corresponding sound_mode.
     |  
     |  mute(self, mute)
     |      Mute receiver via HTTP get command.
     |  
     |  next_track(self)
     |      Send next track command to receiver command via HTTP post.
     |  
     |  power_off(self)
     |      Turn off receiver via HTTP get command.
     |  
     |  power_on(self)
     |      Turn off receiver via HTTP get command.
     |  
     |  previous_track(self)
     |      Send previous track command to receiver command via HTTP post.
     |  
     |  send_get_command(self, command)
     |      Send command via HTTP get to receiver.
     |  
     |  send_post_command(self, command, body)
     |      Send command via HTTP post to receiver.
     |  
     |  set_input_func(self, input_func)
     |      Set input_func of device.
     |      
     |      Valid values depend on the device and should be taken from
     |      "input_func_list".
     |      Return "True" on success and "False" on fail.
     |  
     |  set_sound_mode(self, sound_mode)
     |      Set sound_mode of device.
     |      
     |      Valid values depend on the device and should be taken from
     |      "sound_mode_list".
     |      Return "True" on success and "False" on fail.
     |  
     |  set_sound_mode_dict(self, sound_mode_dict)
     |      Set the matching dictionary used to match the raw sound mode.
     |  
     |  set_volume(self, volume)
     |      Set receiver volume via HTTP get command.
     |      
     |      Volume is send in a format like -50.0.
     |      Minimum is -80.0, maximum at 18.0
     |  
     |  toggle_play_pause(self)
     |      Toggle play pause media player.
     |  
     |  update(self)
     |      Get the latest status information from device.
     |      
     |      Method executes the update method for the current receiver type.
     |  
     |  volume_down(self)
     |      Volume down receiver via HTTP get command.
     |  
     |  volume_up(self)
     |      Volume up receiver via HTTP get command.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  album
     |      Return album name of current playing media as string.
     |  
     |  artist
     |      Return artist of current playing media as string.
     |  
     |  band
     |      Return band of current radio station as string.
     |  
     |  frequency
     |      Return frequency of current radio station as string.
     |  
     |  host
     |      Return the host of the device as string.
     |  
     |  image_url
     |      Return image URL of current playing media when powered on.
     |  
     |  input_func
     |      Return the current input source as string.
     |  
     |  input_func_list
     |      Return a list of available input sources as string.
     |  
     |  muted
     |      Boolean if volume is currently muted.
     |      
     |      Return "True" if muted and "False" if not muted.
     |  
     |  name
     |      Return the name of the device as string.
     |  
     |  netaudio_func_list
     |      Return list of network audio devices.
     |      
     |      Those devices should react to play, pause, next and previous
     |      track commands.
     |  
     |  playing_func_list
     |      Return list of playing devices.
     |      
     |      Those devices offer additional information about what they are playing
     |      (e.g. title, artist, album, band, frequency, station, image_url).
     |  
     |  power
     |      Return the power state of the device.
     |      
     |      Possible values are: "ON", "STANDBY" and "OFF"
     |  
     |  sm_match_dict
     |      Return a dict to map each sound_mode_raw to matching sound_mode.
     |  
     |  support_sound_mode
     |      Return True if sound mode supported.
     |  
     |  sound_mode
     |      Return the matched current sound mode as a string.
     |  
     |  sound_mode_dict
     |      Return a dict of available sound modes with their mapping values.
     |  
     |  sound_mode_list
     |      Return a list of available sound modes as string.
     |  
     |  sound_mode_raw
     |      Return the current sound mode as string as received from the AVR.
     |  
     |  state
     |      Return the state of the device.
     |      
     |      Possible values are: "on", "off", "playing", "paused"
     |      "playing" and "paused" are only available for input functions
     |      in PLAYING_SOURCES.
     |  
     |  station
     |      Return current radio station as string.
     |  
     |  title
     |      Return title of current playing media as string.
     |  
     |  volume
     |      Return volume of Denon AVR as float.
     |      
     |      Volume is send in a format like -50.0.
     |      Minimum is -80.0, maximum at 18.0
     |  
     |  zone
     |      Return Zone of this instance.
     |  
     |  zones
     |      Return all Zone instances of the device.
    
    class DenonAVRZones(DenonAVR)
     |  Representing an additional zone of a Denon AVR Device.
     |  
     |  Method resolution order:
     |      DenonAVRZones
     |      DenonAVR
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __init__(self, parent_avr, zone, name)
     |      Initialize additional zones of DenonAVR.
     |      
     |      :param parent_avr: Instance of parent DenonAVR.
     |      :type parent_avr: denonavr.DenonAVR
     |      
     |      :param zone: Zone name of this instance
     |      :type zone: str
     |      
     |      :param name: Device name, if None FriendlyName of device is used.
     |      :type name: str
     |  
     |  create_zones(self, add_zones)
     |      Only call this method from parent AVR (Main Zone).
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from DenonAVR:
     |  
     |  construct_sm_match_dict(self)
     |      Construct the sm_match_dict.
     |      
     |      Reverse the key value structure. The sm_match_dict is bigger,
     |      but allows for direct matching using a dictionary key access.
     |      The sound_mode_dict is uses externally to set this dictionary
     |      because that has a nicer syntax.
     |  
     |  exec_appcommand_post(self, attribute_list)
     |      Prepare and execute a HTTP POST call to AppCommand.xml end point.
     |      
     |      Returns XML ElementTree on success and None on fail.
     |  
     |  get_status_xml(self, command, suppress_errors=False)
     |      Get status XML via HTTP and return it as XML ElementTree.
     |  
     |  match_sound_mode(self, sound_mode_raw)
     |      Match the raw_sound_mode to its corresponding sound_mode.
     |  
     |  mute(self, mute)
     |      Mute receiver via HTTP get command.
     |  
     |  next_track(self)
     |      Send next track command to receiver command via HTTP post.
     |  
     |  power_off(self)
     |      Turn off receiver via HTTP get command.
     |  
     |  power_on(self)
     |      Turn off receiver via HTTP get command.
     |  
     |  previous_track(self)
     |      Send previous track command to receiver command via HTTP post.
     |  
     |  send_get_command(self, command)
     |      Send command via HTTP get to receiver.
     |  
     |  send_post_command(self, command, body)
     |      Send command via HTTP post to receiver.
     |  
     |  set_input_func(self, input_func)
     |      Set input_func of device.
     |      
     |      Valid values depend on the device and should be taken from
     |      "input_func_list".
     |      Return "True" on success and "False" on fail.
     |  
     |  set_sound_mode(self, sound_mode)
     |      Set sound_mode of device.
     |      
     |      Valid values depend on the device and should be taken from
     |      "sound_mode_list".
     |      Return "True" on success and "False" on fail.
     |  
     |  set_sound_mode_dict(self, sound_mode_dict)
     |      Set the matching dictionary used to match the raw sound mode.
     |  
     |  set_volume(self, volume)
     |      Set receiver volume via HTTP get command.
     |      
     |      Volume is send in a format like -50.0.
     |      Minimum is -80.0, maximum at 18.0
     |  
     |  toggle_play_pause(self)
     |      Toggle play pause media player.
     |  
     |  update(self)
     |      Get the latest status information from device.
     |      
     |      Method executes the update method for the current receiver type.
     |  
     |  volume_down(self)
     |      Volume down receiver via HTTP get command.
     |  
     |  volume_up(self)
     |      Volume up receiver via HTTP get command.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from DenonAVR:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  album
     |      Return album name of current playing media as string.
     |  
     |  artist
     |      Return artist of current playing media as string.
     |  
     |  band
     |      Return band of current radio station as string.
     |  
     |  frequency
     |      Return frequency of current radio station as string.
     |  
     |  host
     |      Return the host of the device as string.
     |  
     |  image_url
     |      Return image URL of current playing media when powered on.
     |  
     |  input_func
     |      Return the current input source as string.
     |  
     |  input_func_list
     |      Return a list of available input sources as string.
     |  
     |  muted
     |      Boolean if volume is currently muted.
     |      
     |      Return "True" if muted and "False" if not muted.
     |  
     |  name
     |      Return the name of the device as string.
     |  
     |  netaudio_func_list
     |      Return list of network audio devices.
     |      
     |      Those devices should react to play, pause, next and previous
     |      track commands.
     |  
     |  playing_func_list
     |      Return list of playing devices.
     |      
     |      Those devices offer additional information about what they are playing
     |      (e.g. title, artist, album, band, frequency, station, image_url).
     |  
     |  power
     |      Return the power state of the device.
     |      
     |      Possible values are: "ON", "STANDBY" and "OFF"
     |  
     |  sm_match_dict
     |      Return a dict to map each sound_mode_raw to matching sound_mode.
     |  
     |  sound_mode
     |      Return the matched current sound mode as a string.
     |  
     |  sound_mode_dict
     |      Return a dict of available sound modes with their mapping values.
     |  
     |  sound_mode_list
     |      Return a list of available sound modes as string.
     |  
     |  sound_mode_raw
     |      Return the current sound mode as string as received from the AVR.
     |  
     |  state
     |      Return the state of the device.
     |      
     |      Possible values are: "on", "off", "playing", "paused"
     |      "playing" and "paused" are only available for input functions
     |      in PLAYING_SOURCES.
     |  
     |  station
     |      Return current radio station as string.
     |  
     |  title
     |      Return title of current playing media as string.
     |  
     |  volume
     |      Return volume of Denon AVR as float.
     |      
     |      Volume is send in a format like -50.0.
     |      Minimum is -80.0, maximum at 18.0
     |  
     |  zone
     |      Return Zone of this instance.
     |  
     |  zones
     |      Return all Zone instances of the device.

====================================================================================

Help on module denonavr.ssdp in denonavr:

NAME
    denonavr.ssdp - This module implements a discovery function for Denon AVR receivers.

DESCRIPTION
    :copyright: (c) 2016 by Oliver Goetz.
    :license: MIT, see LICENSE for more details.

FUNCTIONS
    evaluate_scpd_xml(url)
        Get and evaluate SCPD XML to identified URLs.
        
        Returns dictionary with keys "host", "modelName", "friendlyName" and
        "presentationURL" if a Denon AVR device was found and "False" if not.
    
    identify_denonavr_receivers()
        Identify DenonAVR using SSDP and SCPD queries.
        
        Returns a list of dictionaries which includes all discovered Denon AVR
        devices with keys "host", "modelName", "friendlyName", "presentationURL".
    
    send_ssdp_broadcast()
        Send SSDP broadcast message to discover UPnP devices.
        
        Returns a list of dictionaries with "address" (IP, PORT) and "URL"
        of SCPD XML for all discovered devices.
