#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module implements the interface to Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging
import time
import html
import xml.etree.ElementTree as ET
import requests

_LOGGER = logging.getLogger('DenonAVR')

# For ModelId 1
SOURCES_1_ID = ("1",)
SOURCES_1 = {'Internet Radio': 'IRP', 'Tuner': 'TUNER', 'TV Audio': 'TV',
             'DVD/Blu-ray': 'DVD', 'Media Player': 'MPLAY', 'Game': 'GAME',
             'AUX1': 'AUX1', 'Bluetooth': 'BT', 'CBL/SAT': 'SAT/CBL',
             'Online Music': 'NETHOME', 'iPod/USB': 'USB/IPOD',
             'Blu-ray': 'BD'}

# For ModelId 2,3,7,8
SOURCES_2_ID = ("2", "3", "7", "8")
SOURCES_2 = {'Internet Radio': 'IRP', 'Tuner': 'TUNER', 'TV Audio': 'TV',
             'DVD': 'DVD', 'Media Player': 'MPLAY', 'CD': 'CD', 'Game': 'GAME',
             'AUX2': 'AUX2', 'AUX1': 'AUX1', 'Bluetooth': 'BT',
             'CBL/SAT': 'SAT/CBL', 'Online Music': 'NETHOME',
             'iPod/USB': 'USB/IPOD', 'Blu-ray': 'BD', 'Media Server': 'SERVER'}

# For ModelId 9
SOURCES_3_ID = ("9",)
SOURCES_3 = {'Internet Radio': 'IRP', 'Tuner': 'TUNER', 'TV Audio': 'TV',
             'DVD': 'DVD', 'Media Player': 'MPLAY', 'Game': 'GAME',
             'AUX2': 'AUX2', 'AUX1': 'AUX1', 'Bluetooth': 'BT',
             'CBL/SAT': 'SAT/CBL', 'Online Music': 'NETHOME',
             'iPod/USB': 'USB/IPOD', 'Phono': 'PHONO', 'Blu-ray': 'BD',
             'CD': 'CD'}

# For ModelId 4,5,6,10,11,12
SOURCES_4_ID = ("4", "5", "6", "10", "11", "12")
SOURCES_4 = {'Internet Radio': 'IRP', 'Online Music': 'NETHOME',
             'TV Audio': 'TV', 'DVD': 'DVD', 'Media Player': 'MPLAY',
             'CD': 'CD', 'Game': 'GAME', 'AUX2': 'AUX2',
             'iPod/USB': 'USB/IPOD', 'AUX1': 'AUX1', 'Bluetooth': 'BT',
             'CBL/SAT': 'SAT/CBL', 'Tuner': 'TUNER', 'Phono': 'PHONO',
             'Blu-ray': 'BD', 'Media Server': 'SERVER'}

# For ModelId 5,6,10,11,12 in SalesArea 0
SOURCES_5_ID = ("5", "6", "10", "11", "12")
SOURCES_5_SA = ("0",)
SOURCES_5 = {'Internet Radio': 'IRP', 'Online Music': 'NETHOME',
             'TV Audio': 'TV', 'DVD': 'DVD', 'Game': 'GAME',
             'Media Player': 'MPLAY', 'CD': 'CD', 'AUX2': 'AUX2',
             'HD Radio': 'HDRADIO', 'AUX1': 'AUX1', 'Bluetooth': 'BT',
             'CBL/SAT': 'SAT/CBL', 'iPod/USB': 'USB/IPOD', 'Phono': 'PHONO',
             'Blu-ray': 'BD', 'Media Server': 'SERVER'}

PLAYING_SOURCES = ("Online Music", "Media Server", "iPod/USB", "Bluetooth",
                   "Internet Radio", "Tuner", "HD Radio")
NETAUDIO_SOURCES = ("Online Music", "Media Server", "iPod/USB", "Bluetooth",
                    "Internet Radio")

STATUS_URL = "/goform/formMainZone_MainZoneXmlStatus.xml"
MAINZONE_URL = "/goform/formMainZone_MainZoneXml.xml"
NETAUDIOSTATUS_URL = "/goform/formNetAudio_StatusXml.xml"
TUNERSTATUS_URL = "/goform/formTuner_TunerXml.xml"
HDTUNERSTATUS_URL = "/goform/formTuner_HdXml.xml"
COMMAND_SEL_SRC_URL = "/goform/formiPhoneAppDirect.xml?SI"
COMMAND_POWER_ON_URL = "/goform/formiPhoneAppPower.xml?1+PowerOn"
COMMAND_POWER_STANDBY_URL = "/goform/formiPhoneAppPower.xml?1+PowerStandby"
COMMAND_VOLUME_UP_URL = "/goform/formiPhoneAppDirect.xml?MVUP"
COMMAND_VOLUME_DOWN_URL = "/goform/formiPhoneAppDirect.xml?MVDOWN"
COMMAND_SET_VOLUME_URL = "/goform/formiPhoneAppVolume.xml?1+%.1f"
COMMAND_MUTE_ON_URL = "/goform/formiPhoneAppMute.xml?1+MuteOn"
COMMAND_MUTE_OFF_URL = "/goform/formiPhoneAppMute.xml?1+MuteOff"
COMMAND_NETAUDIO_POST_URL = "/NetAudio/index.put.asp"

POWER_ON = "ON"
POWER_OFF = "OFF"
POWER_STANDBY = "STANDBY"
STATE_ON = "on"
STATE_OFF = "off"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"


class DenonAVR(object):
    """Representing a Denon AVR Device."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    def __init__(self, host, name=None):
        """
        Initialize MainZone of DenonAVR.

        Variable definition:
        host: IP or HOSTNAME.
        name: string (Optional - otherwise FriendlyName of device is used).
        """
        self._name = name
        self._host = host
        self._mute = False
        self._volume = "--"
        self._input_func = None
        self._input_func_list = {}
        self._state = None
        self._power = None
        self._modelid = None
        self._salesarea = None
        self._image_url = (
            "http://{host}/img/album%20art_S.png".format(host=host))
        self._title = None
        self._artist = None
        self._album = None
        self._band = None
        self._frequency = None
        self._station = None
        # Fill variables with initial values
        self.update()

    @classmethod
    def get_status_xml(cls, host, command):
        """Get status XML via HTTP and return it as XML ElementTree."""
        # Get XML structure via HTTP get
        try:
            req = requests.get("http://{host}{command}"
                               .format(host=host, command=command), timeout=2)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("ConnectionError retrieving data from host %s",
                          host)
            raise ConnectionError
        except requests.exceptions.Timeout:
            _LOGGER.error("Timeout retrieving data from host %s", host)
            raise ConnectionError
        # Continue with XML processing only if HTTP status code = 200
        if req.status_code == 200:
            # Convert bytecode to string
            r_string = ""
            for line in req:
                line_string = str(line, req.encoding)
                r_string += line_string
            # Return XML ElementTree
            return ET.fromstring(r_string)
        else:
            _LOGGER.error("Host %s returned HTTP status code %s\
                when trying to receive data", host, req.status_code)
            raise ConnectionError

    @classmethod
    def send_get_command(cls, host, command):
        """Send command via HTTP get to receiver."""
        # Send commands via HTTP get
        try:
            req = requests.get("http://{host}{command}"
                               .format(host=host, command=command), timeout=2)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("ConnectionError sending GET request to host %s",
                          host)
            raise ConnectionError
        except requests.exceptions.Timeout:
            _LOGGER.error("Timeout sending GET request to host %s", host)
            raise ConnectionError
        if req.status_code == 200:
            return True
        else:
            _LOGGER.error(
                "Host %s returned HTTP status code %s\
                when trying to send GET commands", host, req.status_code)
            return False

    @classmethod
    def send_post_command(cls, host, command, body):
        """Send command via HTTP post to receiver."""
        # Send commands via HTTP post
        try:
            req = requests.post(
                "http://{host}{command}"
                .format(host=host, command=command), data=body)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("ConnectionError sending POST request to host %s",
                          host)
            raise ConnectionError
        except requests.exceptions.Timeout:
            _LOGGER.error("Timeout sending POST request to host %s", host)
            raise ConnectionError
        if req.status_code == 200:
            return True
        else:
            _LOGGER.error("Host %s returned HTTP status code %s when trying to\
                send POST commands", host, req.status_code)
            return False

    def update(self):
        """
        Get the latest status information from device.

        Method queries device via HTTP and updates instance attributes.
        Returns "True" on success and "False" on fail.
        """
        # pylint: disable=too-many-branches
        # Get status XML from Denon receiver via HTTP
        try:
            root = self.get_status_xml(self._host, MAINZONE_URL)
        except ConnectionError:
            self._power = POWER_OFF
            self._state = STATE_OFF
            return False

        # Get the relevant tags from the XML structure
        for child in root:
            if child.tag == "Power":
                self._power = child[0].text
            elif child.tag == "InputFuncSelect":
                self._input_func = child[0].text
            elif child.tag == "MasterVolume":
                self._volume = child[0].text
            elif child.tag == "Mute":
                self._mute = child[0].text
            elif child.tag == "ModelId":
                self._modelid = child[0].text
            elif child.tag == "SalesArea":
                self._salesarea = child[0].text
            elif child.tag == "FriendlyName" and self._name is None:
                self._name = child[0].text

        # Set state and media image URL based on current source
        # and power status
        if self._power == POWER_ON and self._input_func in PLAYING_SOURCES:
            if self._update_media_data():
                pass
            else:
                _LOGGER.error("Update of media data for source %s failed",
                              self._input_func)
        elif self._power == POWER_ON:
            self._state = STATE_ON
            self._title = None
            self._artist = None
            self._album = None
            self._band = None
            self._frequency = None
            self._station = None
            if self._image_url != ("http://{host}/img/album%20art_S.png"
                                   .format(host=self._host)):
                self._image_url = ("http://{host}/img/album%20art_S.png"
                                   .format(host=self._host))
        else:
            self._state = STATE_OFF
            self._title = None
            self._artist = None
            self._album = None
            self._band = None
            self._frequency = None
            self._station = None

        # Get/update sources list if current source is not know yet
        if self._input_func not in self._input_func_list:
            if self._update_input_func_list():
                pass
            else:
                _LOGGER.error(
                    "Input function list for Denon receiver at host %s\
                    could not be updated", self._host)

        # Finished
        return True

    def _update_input_func_list(self):
        """
        Update sources list from receiver.

        Internal method which queries device via HTTP to identify input
        functions based on modelid and salescode, to map renamed sources
        and to update instance attributes.
        """
        # pylint: disable=too-many-branches
        # A different XML is needed to get names of eventually renamed sources
        try:
            root = self.get_status_xml(self._host, STATUS_URL)
        except ConnectionError:
            self._input_func_list = None
            return False

        renamed_sources = {}
        xml_inputfunclist = []
        xml_renamesource = []

        # Get the relevant tags from XML structure
        for child in root:
            # Default names of the sources
            if child.tag == "InputFuncList":
                for value in child:
                    # For some reason some functions are written in capital
                    # letters in this structure.
                    # We need to lower them for a later mapping
                    xml_inputfunclist.append(value.text.lower())
            # Renamed sources
            if child.tag == "RenameSource":
                for value in child:
                    for value2 in value:
                        xml_renamesource.append(value2.text.strip())

        # The renamed sources are in the same row as the default ones
        for i, item in enumerate(xml_inputfunclist):
            try:
                renamed_sources[item] = xml_renamesource[i]
            except IndexError:
                return False

        # Get the sources mapping based on the ModelId and SalesArea
        # Mapping is needed because displaying and sending interfaces
        # are using different names
        if self._modelid in SOURCES_5_ID and self._salesarea in SOURCES_5_SA:
            selected_sources = SOURCES_5
        elif self._modelid in SOURCES_4_ID:
            selected_sources = SOURCES_4
        elif self._modelid in SOURCES_3_ID:
            selected_sources = SOURCES_3
        elif self._modelid in SOURCES_2_ID:
            selected_sources = SOURCES_2
        elif self._modelid in SOURCES_1_ID:
            selected_sources = SOURCES_1
        else:
            _LOGGER.error("No sources for ModelId %s and SalesArea %s defined",
                          self._modelid, self._salesarea)
            return False

        # Clear and rebuild the sources list
        self._input_func_list.clear()
        for item in selected_sources.items():
            # For renamed sources use those names
            if item[0].lower() in renamed_sources:
                self._input_func_list[renamed_sources[item[0].lower()]] = \
                    item[1]
            # Otherwise the standard names
            else:
                self._input_func_list[item[0]] = item[1]

        # Finished
        return True

    def _update_media_data(self):
        """
        Update media data for playing devices.

        Internal method which queries device via HTTP to update media
        information (title, artist, etc.) and URL of cover image.
        """
        # pylint: disable=too-many-branches
        # Use different query URL based on selected source
        if self._input_func in NETAUDIO_SOURCES:
            try:
                root = self.get_status_xml(
                    self._host, "{url}?ZoneName=MAIN+ZONE"
                    .format(url=NETAUDIOSTATUS_URL))
            except ConnectionError:
                return False

            # Get the relevant tags from XML structure
            for child in root:
                if child.tag == "szLine":
                    if (self._title != html.unescape(child[1].text) if (
                            child[1].text is not None) else None or
                            self._artist != html.unescape(child[2].text) if (
                                child[2].text is not None) else None or
                            self._album != html.unescape(child[4].text) if (
                                child[4].text is not None) else None):
                        # Refresh cover with a new time stamp for media URL
                        # when track is changing
                        self._image_url = (
                            "http://{host}/NetAudio/art.asp-jpg?{time}"
                            .format(host=self._host, time=int(time.time()))
                            )
                        # On track change assume device is PLAYING
                        self._state = STATE_PLAYING
                    self._title = html.unescape(child[1].text) if (
                        child[1].text is not None) else None
                    self._artist = html.unescape(child[2].text) if (
                        child[2].text is not None) else None
                    self._album = html.unescape(child[4].text)if (
                        child[4].text is not None) else None
                    self._band = None
                    self._frequency = None
                    self._station = None

        elif self._input_func == "Tuner":
            try:
                root = self.get_status_xml(self._host,
                                           "{url}?ZoneName=MAIN+ZONE"
                                           .format(url=TUNERSTATUS_URL))
            except ConnectionError:
                return False

            # Get the relevant tags from XML structure
            for child in root:
                if child.tag == "Band":
                    self._band = child[0].text
                elif child.tag == "Frequency":
                    self._frequency = child[0].text

            self._title = None
            self._artist = None
            self._album = None
            self._station = None

            # Assume Tuner is always PLAYING
            self._state = STATE_PLAYING

            # No special cover, using a static one
            if self._image_url != ("http://{host}/img/album%20art_S.png"
                                   .format(host=self._host)):
                self._image_url = ("http://{host}/img/album%20art_S.png"
                                   .format(host=self._host))
        elif self._input_func == "HD Radio":
            try:
                root = self.get_status_xml(
                    self._host, "{url}?ZoneName=MAIN+ZONE"
                    .format(url=HDTUNERSTATUS_URL))
            except ConnectionError:
                return False

            # Get the relevant tags from XML structure
            for child in root:
                if child.tag == "Artist":
                    self._artist = html.unescape(child[0].text) if (
                        child[0].text is not None) else None
                elif child.tag == "Title":
                    self._title = html.unescape(child[0].text) if (
                        child[0].text is not None) else None
                elif child.tag == "Album":
                    self._album = html.unescape(child[0].text) if (
                        child[0].text is not None) else None
                elif child.tag == "Band":
                    self._band = html.unescape(child[0].text) if (
                        child[0].text is not None) else None
                elif child.tag == "Frequency":
                    self._frequency = html.unescape(child[0].text) if (
                        child[0].text is not None) else None
                elif child.tag == "StationNameSh":
                    self._station = html.unescape(child[0].text) if (
                        child[0].text is not None) else None

            # Assume Tuner is always PLAYING
            self._state = STATE_PLAYING

            # No special cover, using a static one
            if self._image_url != ("http://{host}/img/album%20art_S.png"
                                   .format(host=self._host)):
                self._image_url = ("http://{host}/img/album%20art_S.png"
                                   .format(host=self._host))

        # Finished
        return True

    @property
    def name(self):
        """Return the name of the device as string."""
        return self._name

    @property
    def power(self):
        """
        Return the power state of the device.

        Possible values are: "ON", "STANDBY" and "OFF"
        """
        return self._power

    @property
    def state(self):
        """
        Return the state of the device.

        Possible values are: "on", "off", "playing", "paused"
        "playing" and "paused" are only available for input functions
        in PLAYING_SOURCES.
        """
        return self._state

    @property
    def muted(self):
        """
        Boolean if volume is currently muted.

        Return "True" if muted and "False" if not muted.
        """
        return bool(self._mute == 'on')

    @property
    def volume(self):
        """
        Return volume of Denon AVR as float.

        Volume is send in a format like -50.0.
        Minimum is -80.0, maximum at 18.0
        """
        if self._volume == "--":
            return -80.0
        else:
            return float(self._volume)

    @property
    def input_func(self):
        """Return the current input source as string."""
        return self._input_func

    @property
    def input_func_list(self):
        """Return a list of available input sources as string."""
        return sorted(self._input_func_list.keys())

    @property
    def image_url(self):
        """Return image URL of current playing media when powered on."""
        if self._power == POWER_ON:
            return self._image_url
        else:
            return None

    @property
    def title(self):
        """Return title of current playing media as string."""
        return self._title

    @property
    def artist(self):
        """Return artist of current playing media as string."""
        return self._artist

    @property
    def album(self):
        """Return album name of current playing media as string."""
        return self._album

    @property
    def band(self):
        """Return band of current radio station as string."""
        return self._band

    @property
    def frequency(self):
        """Return frequency of current radio station as string."""
        return self._frequency

    @property
    def station(self):
        """Return current radio station as string."""
        return self._station

    @input_func.setter
    def input_func(self, input_func):
        """Setter function for input_func to switch input_func of device."""
        self.set_input_func(input_func)

    def set_input_func(self, input_func):
        """
        Set input_func of device.

        Valid values depend on the device and should be taken from
        "input_func_list".
        Return "True" on success and "False" on fail.
        """
        # For selection of sources other names then at receiving sources
        # have to be used
        try:
            linp = self._input_func_list[input_func]
        except KeyError:
            _LOGGER.error("No mapping rule for source %s", input_func)
            return False
        try:
            if self.send_get_command(self._host, COMMAND_SEL_SRC_URL + linp):
                self._input_func = input_func
                return True
            else:
                return False
        except ConnectionError:
            return False

    def toggle_play_pause(self):
        """Toggle play pause media player."""
        # Use Play/Pause button only for sources which support NETAUDIO
        if (self._state == STATE_PLAYING and
                self._input_func in NETAUDIO_SOURCES):
            self._pause()
        elif self._input_func in NETAUDIO_SOURCES:
            self._play()

    def _play(self):
        """Send play command to receiver command via HTTP post."""
        # Use pause command only for sources which support NETAUDIO
        if self._input_func in NETAUDIO_SOURCES:
            body = {"cmd0": "PutNetAudioCommand/CurEnter",
                    "cmd1": "aspMainZone_WebUpdateStatus/",
                    "ZoneName": "MAIN ZONE"}
            try:
                if self.send_post_command(
                        self._host, COMMAND_NETAUDIO_POST_URL, body):
                    self._state = STATE_PLAYING
                    return True
                else:
                    return False
            except ConnectionError:
                return False

    def _pause(self):
        """Send pause command to receiver command via HTTP post."""
        # Use pause command only for sources which support NETAUDIO
        if self._input_func in NETAUDIO_SOURCES:
            body = {"cmd0": "PutNetAudioCommand/CurEnter",
                    "cmd1": "aspMainZone_WebUpdateStatus/",
                    "ZoneName": "MAIN ZONE"}
            try:
                if self.send_post_command(
                        self._host, COMMAND_NETAUDIO_POST_URL, body):
                    self._state = STATE_PAUSED
                    return True
                else:
                    return False
            except ConnectionError:
                return False

    def previous_track(self):
        """Send previous track command to receiver command via HTTP post."""
        # Use previous track button only for sources which support NETAUDIO
        if self._input_func in NETAUDIO_SOURCES:
            body = {"cmd0": "PutNetAudioCommand/CurUp",
                    "cmd1": "aspMainZone_WebUpdateStatus/",
                    "ZoneName": "MAIN ZONE"}
            try:
                return bool(self.send_post_command(
                    self._host, COMMAND_NETAUDIO_POST_URL, body))
            except ConnectionError:
                return False

    def next_track(self):
        """Send next track command to receiver command via HTTP post."""
        # Use next track button only for sources which support NETAUDIO
        if self._input_func in NETAUDIO_SOURCES:
            body = {"cmd0": "PutNetAudioCommand/CurDown",
                    "cmd1": "aspMainZone_WebUpdateStatus/",
                    "ZoneName": "MAIN ZONE"}
            try:
                return bool(self.send_post_command(
                    self._host, COMMAND_NETAUDIO_POST_URL, body))
            except ConnectionError:
                return False

    def power_on(self):
        """Turn off receiver via HTTP get command."""
        try:
            if self.send_get_command(self._host, COMMAND_POWER_ON_URL):
                self._power = POWER_ON
                self._state = STATE_ON
                return True
            else:
                return False
        except ConnectionError:
            return False

    def power_off(self):
        """Turn off receiver via HTTP get command."""
        try:
            if self.send_get_command(self._host, COMMAND_POWER_STANDBY_URL):
                self._power = POWER_STANDBY
                self._state = STATE_OFF
                return True
            else:
                return False
        except ConnectionError:
            return False

    def volume_up(self):
        """Volume up receiver via HTTP get command."""
        try:
            return bool(self.send_get_command(
                self._host, COMMAND_VOLUME_UP_URL))
        except ConnectionError:
            return False

    def volume_down(self):
        """Volume down receiver via HTTP get command."""
        try:
            return bool(self.send_get_command(
                self._host, COMMAND_VOLUME_DOWN_URL))
        except ConnectionError:
            return False

    def set_volume(self, volume):
        """
        Set receiver volume via HTTP get command.

        Volume is send in a format like -50.0.
        Minimum is -80.0, maximum at 18.0
        """
        if volume < -80 or volume > 18:
            raise ValueError("Invalid volume!")

        try:
            return bool(self.send_get_command(
                self._host, COMMAND_SET_VOLUME_URL % volume))
        except ConnectionError:
            return False

    def mute(self, mute):
        """Mute receiver via HTTP get command."""
        try:
            if mute:
                if self.send_get_command(self._host, COMMAND_MUTE_ON_URL):
                    self._mute = mute
                    return True
                else:
                    return False
            else:
                if self.send_get_command(self._host, COMMAND_MUTE_OFF_URL):
                    self._mute = mute
                    return True
                else:
                    return False
        except ConnectionError:
            return False
