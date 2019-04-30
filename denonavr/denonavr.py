#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the interface to Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

from collections import (namedtuple, OrderedDict)
from io import BytesIO
import logging
import time
import re
import html
import xml.etree.ElementTree as ET
import requests

_LOGGER = logging.getLogger("DenonAVR")

DEVICEINFO_AVR_X_PATTERN = re.compile(
    r"(.*AVR-S.*|.*SR500[6-9]|.*SR60(07|08|09|10|11|12|13)|.*NR1604)")
DEVICEINFO_COMMAPI_PATTERN = re.compile(r"(0210|0300)")

ReceiverType = namedtuple('ReceiverType', ["type", "port"])
AVR = ReceiverType(type="avr", port=80)
AVR_X = ReceiverType(type="avr-x", port=80)
AVR_X_2016 = ReceiverType(type="avr-x-2016", port=8080)

SOURCE_MAPPING = {"TV AUDIO": "TV", "iPod/USB": "USB/IPOD", "Bluetooth": "BT",
                  "Blu-ray": "BD", "CBL/SAT": "SAT/CBL", "NETWORK": "NET",
                  "Media Player": "MPLAY", "AUX": "AUX1", "Tuner": "TUNER"}

CHANGE_INPUT_MAPPING = {"Internet Radio": "IRP", "Online Music": "NET",
                        "Media Server": "SERVER", "Spotify": "SPOTIFY",
                        "Flickr": "FLICKR", "Favorites": "FAVORITES"}

ALL_ZONE_STEREO = "ALL ZONE STEREO"

SOUND_MODE_MAPPING = OrderedDict(
    [('MUSIC', ['PLII MUSIC', 'DTS NEO:6 MUSIC', 'DOLBY D +NEO:X M',
                'ROCK ARENA', 'JAZZ CLUB', 'MATRIX']),
     ('MOVIE', ['PLII MOVIE', 'PLII CINEMA', 'DTS NEO:X CINEMA',
                'DTS NEO:6 CINEMA', 'DOLBY D +NEO:X C', 'MONO MOVIE',
                'PLIIX CINEMA']),
     ('GAME', ['PLII GAME', 'DOLBY D +NEO:X G', 'VIDEO GAME']),
     ('AUTO', ['None']),
     ('VIRTUAL', ['VIRTUAL']),
     ('PURE DIRECT', ['DIRECT', 'PURE_DIRECT', 'PURE DIRECT']),
     ('DOLBY DIGITAL', ['DOLBY DIGITAL', 'DOLBY D + DOLBY SURROUND',
                        'DOLBY DIGITAL +', 'STANDARD(DOLBY)', 'DOLBY SURROUND',
                        'DOLBY D + +DOLBY SURROUND', 'NEURAL',
                        'MULTI IN + NEURAL:X', 'DOLBY D + NEURAL:X',
                        'DOLBY DIGITAL + NEURAL:X',
                        'DOLBY DIGITAL + + NEURAL:X',
                        'DOLBY AUDIO - DOLBY SURROUND']),
     ('DTS SURROUND', ['DTS SURROUND', 'DTS NEURAL:X', 'STANDARD(DTS)',
                       'DTS + NEURAL:X', 'MULTI CH IN', 'DTS-HD MSTR',
                       'DTS VIRTUAL:X']),
     ('MCH STEREO', ['MULTI CH STEREO', 'MULTI_CH_STEREO', 'MCH STEREO']),
     ('STEREO', ['STEREO']),
     (ALL_ZONE_STEREO, [ALL_ZONE_STEREO])])

PLAYING_SOURCES = ("Online Music", "Media Server", "iPod/USB", "Bluetooth",
                   "Internet Radio", "Favorites", "SpotifyConnect", "Flickr",
                   "TUNER", "NET/USB", "HDRADIO", "Music Server", "NETWORK",
                   "NET")
NETAUDIO_SOURCES = ("Online Music", "Media Server", "iPod/USB", "Bluetooth",
                    "Internet Radio", "Favorites", "SpotifyConnect", "Flickr",
                    "NET/USB", "Music Server", "NETWORK", "NET")

# Image URLs
STATIC_ALBUM_URL = "http://{host}:{port}/img/album%20art_S.png"
ALBUM_COVERS_URL = "http://{host}:{port}/NetAudio/art.asp-jpg?{time}"

# General URLs
APPCOMMAND_URL = "/goform/AppCommand.xml"
DEVICEINFO_URL = "/goform/Deviceinfo.xml"
NETAUDIOSTATUS_URL = "/goform/formNetAudio_StatusXml.xml"
TUNERSTATUS_URL = "/goform/formTuner_TunerXml.xml"
HDTUNERSTATUS_URL = "/goform/formTuner_HdXml.xml"
COMMAND_NETAUDIO_POST_URL = "/NetAudio/index.put.asp"


# Main Zone URLs
STATUS_URL = "/goform/formMainZone_MainZoneXmlStatus.xml"
MAINZONE_URL = "/goform/formMainZone_MainZoneXml.xml"
COMMAND_SEL_SRC_URL = "/goform/formiPhoneAppDirect.xml?SI"
COMMAND_FAV_SRC_URL = "/goform/formiPhoneAppDirect.xml?ZM"
COMMAND_POWER_ON_URL = "/goform/formiPhoneAppPower.xml?1+PowerOn"
COMMAND_POWER_STANDBY_URL = "/goform/formiPhoneAppPower.xml?1+PowerStandby"
COMMAND_VOLUME_UP_URL = "/goform/formiPhoneAppDirect.xml?MVUP"
COMMAND_VOLUME_DOWN_URL = "/goform/formiPhoneAppDirect.xml?MVDOWN"
COMMAND_SET_VOLUME_URL = "/goform/formiPhoneAppVolume.xml?1+%.1f"
COMMAND_MUTE_ON_URL = "/goform/formiPhoneAppMute.xml?1+MuteOn"
COMMAND_MUTE_OFF_URL = "/goform/formiPhoneAppMute.xml?1+MuteOff"
COMMAND_SEL_SM_URL = "/goform/formiPhoneAppDirect.xml?MS"
COMMAND_SET_ZST_URL = "/goform/formiPhoneAppDirect.xml?MN"

# Zone 2 URLs
STATUS_Z2_URL = "/goform/formZone2_Zone2XmlStatus.xml"
MAINZONE_Z2_URL = None
COMMAND_SEL_SRC_Z2_URL = "/goform/formiPhoneAppDirect.xml?Z2"
COMMAND_FAV_SRC_Z2_URL = "/goform/formiPhoneAppDirect.xml?Z2"
COMMAND_POWER_ON_Z2_URL = "/goform/formiPhoneAppPower.xml?2+PowerOn"
COMMAND_POWER_STANDBY_Z2_URL = "/goform/formiPhoneAppPower.xml?2+PowerStandby"
COMMAND_VOLUME_UP_Z2_URL = "/goform/formiPhoneAppDirect.xml?Z2UP"
COMMAND_VOLUME_DOWN_Z2_URL = "/goform/formiPhoneAppDirect.xml?Z2DOWN"
COMMAND_SET_VOLUME_Z2_URL = "/goform/formiPhoneAppVolume.xml?2+%.1f"
COMMAND_MUTE_ON_Z2_URL = "/goform/formiPhoneAppMute.xml?2+MuteOn"
COMMAND_MUTE_OFF_Z2_URL = "/goform/formiPhoneAppMute.xml?2+MuteOff"

# Zone 3 URLs
STATUS_Z3_URL = "/goform/formZone3_Zone3XmlStatus.xml"
MAINZONE_Z3_URL = None
COMMAND_SEL_SRC_Z3_URL = "/goform/formiPhoneAppDirect.xml?Z3"
COMMAND_FAV_SRC_Z3_URL = "/goform/formiPhoneAppDirect.xml?Z3"
COMMAND_POWER_ON_Z3_URL = "/goform/formiPhoneAppPower.xml?3+PowerOn"
COMMAND_POWER_STANDBY_Z3_URL = "/goform/formiPhoneAppPower.xml?3+PowerStandby"
COMMAND_VOLUME_UP_Z3_URL = "/goform/formiPhoneAppDirect.xml?Z3UP"
COMMAND_VOLUME_DOWN_Z3_URL = "/goform/formiPhoneAppDirect.xml?Z3DOWN"
COMMAND_SET_VOLUME_Z3_URL = "/goform/formiPhoneAppVolume.xml?3+%.1f"
COMMAND_MUTE_ON_Z3_URL = "/goform/formiPhoneAppMute.xml?3+MuteOn"
COMMAND_MUTE_OFF_Z3_URL = "/goform/formiPhoneAppMute.xml?3+MuteOff"


ReceiverURLs = namedtuple(
    "ReceiverURLs", ["appcommand", "status", "mainzone", "deviceinfo",
                     "netaudiostatus", "tunerstatus", "hdtunerstatus",
                     "command_sel_src", "command_fav_src", "command_power_on",
                     "command_power_standby", "command_volume_up",
                     "command_volume_down", "command_set_volume",
                     "command_mute_on", "command_mute_off",
                     "command_sel_sound_mode", "command_netaudio_post",
                     "command_set_all_zone_stereo"])

DENONAVR_URLS = ReceiverURLs(appcommand=APPCOMMAND_URL,
                             status=STATUS_URL,
                             mainzone=MAINZONE_URL,
                             deviceinfo=DEVICEINFO_URL,
                             netaudiostatus=NETAUDIOSTATUS_URL,
                             tunerstatus=TUNERSTATUS_URL,
                             hdtunerstatus=HDTUNERSTATUS_URL,
                             command_sel_src=COMMAND_SEL_SRC_URL,
                             command_fav_src=COMMAND_FAV_SRC_URL,
                             command_power_on=COMMAND_POWER_ON_URL,
                             command_power_standby=COMMAND_POWER_STANDBY_URL,
                             command_volume_up=COMMAND_VOLUME_UP_URL,
                             command_volume_down=COMMAND_VOLUME_DOWN_URL,
                             command_set_volume=COMMAND_SET_VOLUME_URL,
                             command_mute_on=COMMAND_MUTE_ON_URL,
                             command_mute_off=COMMAND_MUTE_OFF_URL,
                             command_sel_sound_mode=COMMAND_SEL_SM_URL,
                             command_netaudio_post=COMMAND_NETAUDIO_POST_URL,
                             command_set_all_zone_stereo=COMMAND_SET_ZST_URL)

ZONE2_URLS = ReceiverURLs(appcommand=APPCOMMAND_URL,
                          status=STATUS_Z2_URL,
                          mainzone=MAINZONE_Z2_URL,
                          deviceinfo=DEVICEINFO_URL,
                          netaudiostatus=NETAUDIOSTATUS_URL,
                          tunerstatus=TUNERSTATUS_URL,
                          hdtunerstatus=HDTUNERSTATUS_URL,
                          command_sel_src=COMMAND_SEL_SRC_Z2_URL,
                          command_fav_src=COMMAND_FAV_SRC_Z2_URL,
                          command_power_on=COMMAND_POWER_ON_Z2_URL,
                          command_power_standby=COMMAND_POWER_STANDBY_Z2_URL,
                          command_volume_up=COMMAND_VOLUME_UP_Z2_URL,
                          command_volume_down=COMMAND_VOLUME_DOWN_Z2_URL,
                          command_set_volume=COMMAND_SET_VOLUME_Z2_URL,
                          command_mute_on=COMMAND_MUTE_ON_Z2_URL,
                          command_mute_off=COMMAND_MUTE_OFF_Z2_URL,
                          command_sel_sound_mode=COMMAND_SEL_SM_URL,
                          command_netaudio_post=COMMAND_NETAUDIO_POST_URL,
                          command_set_all_zone_stereo=COMMAND_SET_ZST_URL)

ZONE3_URLS = ReceiverURLs(appcommand=APPCOMMAND_URL,
                          status=STATUS_Z3_URL,
                          mainzone=MAINZONE_Z3_URL,
                          deviceinfo=DEVICEINFO_URL,
                          netaudiostatus=NETAUDIOSTATUS_URL,
                          tunerstatus=TUNERSTATUS_URL,
                          hdtunerstatus=HDTUNERSTATUS_URL,
                          command_sel_src=COMMAND_SEL_SRC_Z3_URL,
                          command_fav_src=COMMAND_FAV_SRC_Z3_URL,
                          command_power_on=COMMAND_POWER_ON_Z3_URL,
                          command_power_standby=COMMAND_POWER_STANDBY_Z3_URL,
                          command_volume_up=COMMAND_VOLUME_UP_Z3_URL,
                          command_volume_down=COMMAND_VOLUME_DOWN_Z3_URL,
                          command_set_volume=COMMAND_SET_VOLUME_Z3_URL,
                          command_mute_on=COMMAND_MUTE_ON_Z3_URL,
                          command_mute_off=COMMAND_MUTE_OFF_Z3_URL,
                          command_sel_sound_mode=COMMAND_SEL_SM_URL,
                          command_netaudio_post=COMMAND_NETAUDIO_POST_URL,
                          command_set_all_zone_stereo=COMMAND_SET_ZST_URL)

POWER_ON = "ON"
POWER_OFF = "OFF"
POWER_STANDBY = "STANDBY"
STATE_ON = "on"
STATE_OFF = "off"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"

NO_ZONES = None
ZONE2 = {"Zone2": None}
ZONE3 = {"Zone3": None}
ZONE2_ZONE3 = {"Zone2": None, "Zone3": None}


class DenonAVR:
    """Representing a Denon AVR Device."""

    def __init__(self, host, name=None, show_all_inputs=False, timeout=2.0,
                 add_zones=NO_ZONES):
        """
        Initialize MainZone of DenonAVR.

        :param host: IP or HOSTNAME.
        :type host: str

        :param name: Device name, if None FriendlyName of device is used.
        :type name: str or None

        :param show_all_inputs: If True deleted input functions are also shown
        :type show_all_inputs: bool

        :param add_zones: Additional Zones for which an instance are created
        :type add_zones: dict [str, str] or None
        """
        self._name = name
        self._host = host
        # Main zone just set for DenonAVR class
        if self.__class__.__name__ == "DenonAVR":
            self._zone = "Main"
        self._zones = {self._zone: self}

        if self._zone == "Main":
            self._urls = DENONAVR_URLS
        elif self._zone == "Zone2":
            self._urls = ZONE2_URLS
        elif self._zone == "Zone3":
            self._urls = ZONE3_URLS
        else:
            raise ValueError("Invalid zone {}".format(self._zone))

        # Timeout for HTTP calls to receiver
        self.timeout = timeout
        # Receiver types could be avr, avr-x, avr-x-2016 after being determined
        self._receiver_type = None
        # Port 80 for avr and avr-x, Port 8080 port avr-x-2016
        self._receiver_port = None

        self._show_all_inputs = show_all_inputs

        self._mute = STATE_OFF
        self._volume = "--"
        self._input_func = None
        self._input_func_list = {}
        self._input_func_list_rev = {}
        self._sound_mode_raw = None
        self._sound_mode_dict = SOUND_MODE_MAPPING
        self._support_sound_mode = None
        self._sm_match_dict = self.construct_sm_match_dict()
        self._netaudio_func_list = []
        self._playing_func_list = []
        self._favorite_func_list = []
        self._state = None
        self._power = None
        self._image_url = None
        self._image_available = None
        self._title = None
        self._artist = None
        self._album = None
        self._band = None
        self._frequency = None
        self._station = None

        # Determine receiver type and input functions
        self._update_input_func_list()

        if self._receiver_type == AVR_X_2016.type:
            self._get_zone_name()
        else:
            self._get_receiver_name()
        # Determine if sound mode is supported
        self._get_support_sound_mode()
        # Get initial setting of values
        self.update()
        # Create instances of additional zones if requested
        if self._zone == "Main" and add_zones is not None:
            self.create_zones(add_zones)

    def exec_appcommand_post(self, attribute_list):
        """
        Prepare and execute a HTTP POST call to AppCommand.xml end point.

        Returns XML ElementTree on success and None on fail.
        """
        # Prepare POST XML body for AppCommand.xml
        post_root = ET.Element("tx")

        for attribute in attribute_list:
            # Append tags for each attribute
            item = ET.Element("cmd")
            item.set("id", "1")
            item.text = attribute
            post_root.append(item)

        # Buffer XML body as binary IO
        body = BytesIO()
        post_tree = ET.ElementTree(post_root)
        post_tree.write(body, encoding="utf-8", xml_declaration=True)

        # Query receivers AppCommand.xml
        try:
            res = self.send_post_command(
                self._urls.appcommand, body.getvalue())
        except requests.exceptions.RequestException:
            _LOGGER.error("No connection to %s end point on host %s",
                          self._urls.appcommand, self._host)
            body.close()
        else:
            # Buffered XML not needed anymore: close
            body.close()

            try:
                # Return XML ElementTree
                root = ET.fromstring(res)
            except (ET.ParseError, TypeError):
                _LOGGER.error(
                    "End point %s on host %s returned malformed XML.",
                    self._urls.appcommand, self._host)
            else:
                return root

    def get_status_xml(self, command, suppress_errors=False):
        """Get status XML via HTTP and return it as XML ElementTree."""
        # Get XML structure via HTTP get
        res = requests.get("http://{host}:{port}{command}".format(
            host=self._host, port=self._receiver_port, command=command),
                           timeout=self.timeout)
        # Continue with XML processing only if HTTP status code = 200
        if res.status_code == 200:
            try:
                # Return XML ElementTree
                return ET.fromstring(res.text)
            except ET.ParseError as err:
                if not suppress_errors:
                    _LOGGER.error(
                        "Host %s returned malformed XML for end point %s",
                        self._host, command)
                    _LOGGER.error(err)
                raise ValueError
        else:
            if not suppress_errors:
                _LOGGER.error((
                    "Host %s returned HTTP status code %s to GET request at "
                    "end point %s"), self._host, res.status_code, command)
            raise ValueError

    def send_get_command(self, command):
        """Send command via HTTP get to receiver."""
        # Send commands via HTTP get
        res = requests.get("http://{host}:{port}{command}".format(
            host=self._host, port=self._receiver_port, command=command),
                           timeout=self.timeout)
        if res.status_code == 200:
            return True
        else:
            _LOGGER.error((
                "Host %s returned HTTP status code %s to GET command at "
                "end point %s"), self._host, res.status_code, command)
            return False

    def send_post_command(self, command, body):
        """Send command via HTTP post to receiver."""
        # Send commands via HTTP post
        res = requests.post("http://{host}:{port}{command}".format(
            host=self._host, port=self._receiver_port, command=command),
                            data=body, timeout=self.timeout)
        if res.status_code == 200:
            return res.text
        else:
            _LOGGER.error((
                "Host %s returned HTTP status code %s to POST command at "
                "end point %s"), self._host, res.status_code, command)
            return False

    def create_zones(self, add_zones):
        """Create instances of additional zones for the receiver."""
        for zone, zname in add_zones.items():
            # Name either set explicitly or name of Main Zone with suffix
            zonename = "{} {}".format(self._name, zone) if (
                zname is None) else zname
            zone_inst = DenonAVRZones(self, zone, zonename)
            self._zones[zone] = zone_inst

    def update(self):
        """
        Get the latest status information from device.

        Method executes the update method for the current receiver type.
        """
        if self._receiver_type == AVR_X_2016.type:
            return self._update_avr_2016()
        else:
            return self._update_avr()

    def _update_avr(self):
        """
        Get the latest status information from device.

        Method queries device via HTTP and updates instance attributes.
        Returns "True" on success and "False" on fail.
        This method is for pre 2016 AVR(-X) devices
        """
        # Set all tags to be evaluated
        relevant_tags = {"Power": None, "InputFuncSelect": None, "Mute": None,
                         "MasterVolume": None}

        # Sound mode information only available in main zone
        if self._zone == "Main" and self._support_sound_mode:
            relevant_tags["selectSurround"] = None
            relevant_tags["SurrMode"] = None

        # Get status XML from Denon receiver via HTTP
        try:
            root = self.get_status_xml(self._urls.status)
        except ValueError:
            pass
        except requests.exceptions.RequestException:
            # On timeout and connection error, the device is probably off
            self._power = POWER_OFF
        else:
            # Get the tags from this XML
            relevant_tags = self._get_status_from_xml_tags(root, relevant_tags)

        # Second option to update variables from different source
        if relevant_tags and self._power != POWER_OFF:
            try:
                root = self.get_status_xml(self._urls.mainzone)
            except (ValueError,
                    requests.exceptions.RequestException):
                pass
            else:
                # Get the tags from this XML
                relevant_tags = self._get_status_from_xml_tags(root,
                                                               relevant_tags)

        # Error message if still some variables are not updated yet
        if relevant_tags and self._power != POWER_OFF:
            _LOGGER.error("Missing status information from XML of %s for: %s",
                          self._zone, ", ".join(relevant_tags.keys()))

        # Set state and media image URL based on current source
        # and power status
        if (self._power == POWER_ON) and (
                self._input_func in self._playing_func_list):
            if self._update_media_data():
                pass
            else:
                _LOGGER.error(
                    "Update of media data for source %s in %s failed",
                    self._input_func, self._zone)
        elif self._power == POWER_ON:
            self._state = STATE_ON
            self._title = None
            self._artist = None
            self._album = None
            self._band = None
            self._frequency = None
            self._station = None
            self._image_url = None
        else:
            self._state = STATE_OFF
            self._title = None
            self._artist = None
            self._album = None
            self._band = None
            self._frequency = None
            self._station = None

        # Get/update sources list if current source is not known yet
        if (self._input_func not in self._input_func_list and
                self._input_func is not None):
            if self._update_input_func_list():
                _LOGGER.info("List of input functions refreshed.")
                # If input function is still not known, create new entry.
                if (self._input_func not in self._input_func_list and
                        self._input_func is not None):
                    inputfunc = self._input_func
                    self._input_func_list_rev[inputfunc] = inputfunc
                    self._input_func_list[inputfunc] = inputfunc
            else:
                _LOGGER.error((
                    "Input function list for Denon receiver at host %s "
                    "could not be updated."), self._host)

        # Finished
        return True

    def _update_avr_2016(self):
        """
        Get the latest status information from device.

        Method queries device via HTTP and updates instance attributes.
        Returns "True" on success and "False" on fail.
        This method is for AVR-X  devices built in 2016 and later.
        """
        # Collect tags for AppCommand.xml call
        tags = ["GetAllZonePowerStatus", "GetAllZoneSource",
                "GetAllZoneVolume", "GetAllZoneMuteStatus",
                "GetSurroundModeStatus"]
        # Execute call
        root = self.exec_appcommand_post(tags)
        # Check result
        if root is None:
            _LOGGER.error("Update failed.")
            return False

        # Extract relevant information
        zone = self._get_own_zone()

        try:
            self._power = root[0].find(zone).text
        except (AttributeError, IndexError):
            _LOGGER.error("No PowerStatus found for zone %s", self.zone)

        try:
            self._mute = root[3].find(zone).text
        except (AttributeError, IndexError):
            _LOGGER.error("No MuteStatus found for zone %s", self.zone)

        try:
            self._volume = root.find(
                "./cmd/{zone}/volume".format(zone=zone)).text
        except AttributeError:
            _LOGGER.error("No VolumeStatus found for zone %s", self.zone)

        try:
            inputfunc = root.find(
                "./cmd/{zone}/source".format(zone=zone)).text
        except AttributeError:
            _LOGGER.error("No Source found for zone %s", self.zone)
        else:
            try:
                self._input_func = self._input_func_list_rev[inputfunc]
            except KeyError:
                _LOGGER.info("No mapping for source %s found", inputfunc)
                self._input_func = inputfunc
                # Get/update sources list if current source is not known yet
                if self._update_input_func_list():
                    _LOGGER.info("List of input functions refreshed.")
                    # If input function is still not known, create new entry.
                    if (inputfunc not in self._input_func_list and
                            inputfunc is not None):
                        self._input_func_list_rev[inputfunc] = inputfunc
                        self._input_func_list[inputfunc] = inputfunc
                else:
                    _LOGGER.error((
                        "Input function list for Denon receiver at host %s "
                        "could not be updated."), self._host)
        try:
            self._sound_mode_raw = root[4][0].text.rstrip()
        except (AttributeError, IndexError):
            _LOGGER.error("No SoundMode found for the main zone %s", self.zone)

        # Now playing information is not implemented for 2016+ models, because
        # a HEOS API query needed. So only sync the power state for now.
        if self._power == POWER_ON:
            self._state = STATE_ON
        else:
            self._state = STATE_OFF

        return True

    def _update_input_func_list(self):
        """
        Update sources list from receiver.

        Internal method which updates sources list of receiver after getting
        sources and potential renaming information from receiver.
        """
        # Get all sources and renaming information from receiver
        # For structural information of the variables please see the methods
        receiver_sources = self._get_receiver_sources()

        if not receiver_sources:
            _LOGGER.error("Receiver sources list empty. "
                          "Please check if device is powered on.")
            return False

        # First input_func_list determination of AVR-X receivers
        if self._receiver_type in [AVR_X.type, AVR_X_2016.type]:
            renamed_sources, deleted_sources, status_success = (
                self._get_renamed_deleted_sourcesapp())

            # Backup if previous try with AppCommand was not successful
            if not status_success:
                renamed_sources, deleted_sources = (
                    self._get_renamed_deleted_sources())

            # Remove all deleted sources
            if self._show_all_inputs is False:
                for deleted_source in deleted_sources.items():
                    if deleted_source[1] == "DEL":
                        receiver_sources.pop(deleted_source[0], None)

            # Clear and rebuild the sources lists
            self._input_func_list.clear()
            self._input_func_list_rev.clear()
            self._netaudio_func_list.clear()
            self._playing_func_list.clear()

            for item in receiver_sources.items():
                # Mapping of item[0] because some func names are inconsistant
                # at AVR-X receivers

                m_item_0 = SOURCE_MAPPING.get(item[0], item[0])

                # For renamed sources use those names and save the default name
                # for a later mapping
                if item[0] in renamed_sources:
                    self._input_func_list[renamed_sources[item[0]]] = m_item_0
                    self._input_func_list_rev[
                        m_item_0] = renamed_sources[item[0]]
                    # If the source is a netaudio source, save its renamed name
                    if item[0] in NETAUDIO_SOURCES:
                        self._netaudio_func_list.append(
                            renamed_sources[item[0]])
                    # If the source is a playing source, save its renamed name
                    if item[0] in PLAYING_SOURCES:
                        self._playing_func_list.append(
                            renamed_sources[item[0]])
                # Otherwise the default names are used
                else:
                    self._input_func_list[item[1]] = m_item_0
                    self._input_func_list_rev[m_item_0] = item[1]
                    # If the source is a netaudio source, save its name
                    if item[1] in NETAUDIO_SOURCES:
                        self._netaudio_func_list.append(item[1])
                    # If the source is a playing source, save its name
                    if item[1] in PLAYING_SOURCES:
                        self._playing_func_list.append(item[1])

        # Determination of input_func_list for non AVR-nonX receivers
        elif self._receiver_type == AVR.type:
            # Clear and rebuild the sources lists
            self._input_func_list.clear()
            self._input_func_list_rev.clear()
            self._netaudio_func_list.clear()
            self._playing_func_list.clear()
            for item in receiver_sources.items():
                self._input_func_list[item[1]] = item[0]
                self._input_func_list_rev[item[0]] = item[1]
                # If the source is a netaudio source, save its name
                if item[0] in NETAUDIO_SOURCES:
                    self._netaudio_func_list.append(item[1])
                # If the source is a playing source, save its name
                if item[0] in PLAYING_SOURCES:
                    self._playing_func_list.append(item[1])
        else:
            _LOGGER.error('Receiver type not set yet.')
            return False

        # Finished
        return True

    def _get_receiver_name(self):
        """Get name of receiver from web interface if not set."""
        # If name is not set yet, get it from Main Zone URL
        if self._name is None and self._urls.mainzone is not None:
            name_tag = {"FriendlyName": None}
            try:
                root = self.get_status_xml(self._urls.mainzone)
            except (ValueError,
                    requests.exceptions.RequestException):
                _LOGGER.warning("Receiver name could not be determined. "
                                "Using standard name: Denon AVR.")
                self._name = "Denon AVR"
            else:
                # Get the tags from this XML
                name_tag = self._get_status_from_xml_tags(root, name_tag)
                if name_tag:
                    _LOGGER.warning("Receiver name could not be determined. "
                                    "Using standard name: Denon AVR.")
                    self._name = "Denon AVR"

    def _get_zone_name(self):
        """Get receivers zone name if not set yet."""
        if self._name is None:
            # Collect tags for AppCommand.xml call
            tags = ["GetZoneName"]
            # Execute call
            root = self.exec_appcommand_post(tags)
            # Check result
            if root is None:
                _LOGGER.error("Getting ZoneName failed.")
            else:
                zone = self._get_own_zone()

                try:
                    name = root.find(
                        "./cmd/{zone}".format(zone=zone)).text
                except AttributeError:
                    _LOGGER.error("No ZoneName found for zone %s", self.zone)
                else:
                    self._name = name.strip()

    def _get_support_sound_mode(self):
        """
        Get if sound mode is supported from device.

        Method executes the method for the current receiver type.
        """
        if self._receiver_type == AVR_X_2016.type:
            return self._get_support_sound_mode_avr_2016()
        else:
            return self._get_support_sound_mode_avr()

    def _get_support_sound_mode_avr(self):
        """
        Get if sound mode is supported from device.

        Method queries device via HTTP.
        Returns "True" if sound mode supported and "False" if not.
        This method is for pre 2016 AVR(-X) devices
        """
        # Set sound mode tags to be checked if available
        relevant_tags = {"selectSurround": None, "SurrMode": None}

        # Get status XML from Denon receiver via HTTP
        try:
            root = self.get_status_xml(self._urls.status)
        except (ValueError, requests.exceptions.RequestException):
            pass
        else:
            # Process the tags from this XML
            relevant_tags = self._get_status_from_xml_tags(root, relevant_tags)

        # Second option to update variables from different source
        if relevant_tags:
            try:
                root = self.get_status_xml(self._urls.mainzone)
            except (ValueError,
                    requests.exceptions.RequestException):
                pass
            else:
                # Get the tags from this XML
                relevant_tags = self._get_status_from_xml_tags(root,
                                                               relevant_tags)

        # if sound mode not found in the status XML, return False
        if relevant_tags:
            self._support_sound_mode = False
            return False
        # if sound mode found, the relevant_tags are empty: return True.
        self._support_sound_mode = True
        return True

    def _get_support_sound_mode_avr_2016(self):
        """
        Get if sound mode is supported from device.

        Method enables sound mode.
        Returns "True" in all cases for 2016 AVR(-X) devices
        """
        self._support_sound_mode = True
        return True

    def _get_renamed_deleted_sources(self):
        """
        Get renamed and deleted sources lists from receiver .

        Internal method which queries device via HTTP to get names of renamed
        input sources.
        """
        # renamed_sources and deleted_sources are dicts with "source" as key
        # and "renamed_source" or deletion flag as value.
        renamed_sources = {}
        deleted_sources = {}
        xml_inputfunclist = []
        xml_renamesource = []
        xml_deletesource = []

        # This XML is needed to get names of eventually renamed sources
        try:
            # AVR-X and AVR-nonX using different XMLs to provide info about
            # deleted sources
            if self._receiver_type == AVR_X.type:
                root = self.get_status_xml(self._urls.status)
            # URL only available for Main Zone.
            elif (self._receiver_type == AVR.type and
                  self._urls.mainzone is not None):
                root = self.get_status_xml(self._urls.mainzone)
            else:
                return (renamed_sources, deleted_sources)
        except (ValueError, requests.exceptions.RequestException):
            return (renamed_sources, deleted_sources)

        # Get the relevant tags from XML structure
        for child in root:
            # Default names of the sources
            if child.tag == "InputFuncList":
                for value in child:
                    xml_inputfunclist.append(value.text)
            # Renamed sources
            if child.tag == "RenameSource":
                for value in child:
                    # Two different kinds of source structure types exist
                    # 1. <RenameSource><Value>...
                    if value.text is not None:
                        xml_renamesource.append(value.text.strip())
                    # 2. <RenameSource><Value><Value>
                    else:
                        try:
                            xml_renamesource.append(value[0].text.strip())
                        # Exception covers empty tags and appends empty line
                        # in this case, to ensure that sources and
                        # renamed_sources lists have always the same length
                        except IndexError:
                            xml_renamesource.append(None)
            # Deleted sources
            if child.tag == "SourceDelete":
                for value in child:
                    xml_deletesource.append(value.text)

        # Renamed and deleted sources are in the same row as the default ones
        # Only values which are not None are considered. Otherwise translation
        # is not valid and original name is taken
        for i, item in enumerate(xml_inputfunclist):
            try:
                if xml_renamesource[i] is not None:
                    renamed_sources[item] = xml_renamesource[i]
                else:
                    renamed_sources[item] = item
            except IndexError:
                _LOGGER.error(
                    "List of renamed sources incomplete, continuing anyway")
            try:
                deleted_sources[item] = xml_deletesource[i]
            except IndexError:
                _LOGGER.error(
                    "List of deleted sources incomplete, continuing anyway")

        return (renamed_sources, deleted_sources)

    def _get_renamed_deleted_sourcesapp(self):
        """
        Get renamed and deleted sources lists from receiver .

        Internal method which queries device via HTTP to get names of renamed
        input sources. In this method AppCommand.xml is used.
        """
        # renamed_sources and deleted_sources are dicts with "source" as key
        # and "renamed_source" or deletion flag as value.
        renamed_sources = {}
        deleted_sources = {}

        # Collect tags for AppCommand.xml call
        tags = ["GetRenameSource", "GetDeletedSource"]
        # Execute call
        root = self.exec_appcommand_post(tags)
        # Check result
        if root is None:
            _LOGGER.error("Getting renamed and deleted sources failed.")
            return (renamed_sources, deleted_sources, False)

        # Detect "Document Error: Data follows" title if URL does not exist
        document_error = root.find("./head/title")
        if document_error is not None:
            if document_error.text == "Document Error: Data follows":
                return (renamed_sources, deleted_sources, False)

        for child in root.findall("./cmd/functionrename/list"):
            try:
                renamed_sources[child.find("name").text.strip()] = (
                    child.find("rename").text.strip())
            except AttributeError:
                continue

        for child in root.findall("./cmd/functiondelete/list"):
            try:
                deleted_sources[child.find("FuncName").text.strip(
                )] = "DEL" if (
                    child.find("use").text.strip() == "0") else None
            except AttributeError:
                continue

        return (renamed_sources, deleted_sources, True)

    def _get_receiver_sources(self):
        """
        Get sources list from receiver.

        Internal method which queries device via HTTP to get the receiver's
        input sources.
        This method also determines the type of the receiver
        (avr, avr-x, avr-x-2016).
        """
        # Test if receiver is a AVR-X with port 80 for pre 2016 devices and
        # port 8080 devices 2016 and later
        r_types = [AVR_X, AVR_X_2016]
        for r_type, port in r_types:
            self._receiver_port = port

            # This XML is needed to get the sources of the receiver
            try:
                root = self.get_status_xml(self._urls.deviceinfo,
                                           suppress_errors=True)
            except (ValueError, requests.exceptions.RequestException):
                self._receiver_type = None
            else:
                # First test by CommApiVers
                try:
                    if bool(DEVICEINFO_COMMAPI_PATTERN.search(
                            root.find("CommApiVers").text) is not None):
                        self._receiver_type = r_type
                        # receiver found break the loop
                        break
                except AttributeError:
                    # AttributeError occurs when ModelName tag is not found.
                    # In this case there is no AVR-X device
                    self._receiver_type = None

                # if first test did not find AVR-X device, check by model name
                if self._receiver_type is None:
                    try:
                        if bool(DEVICEINFO_AVR_X_PATTERN.search(
                                root.find("ModelName").text) is not None):
                            self._receiver_type = r_type
                            # receiver found break the loop
                            break
                    except AttributeError:
                        # AttributeError occurs when ModelName tag is not found
                        # In this case there is no AVR-X device
                        self._receiver_type = None

        # Set ports and update method
        if self._receiver_type is None:
            self._receiver_type = AVR.type
            self._receiver_port = AVR.port
        elif self._receiver_type == AVR_X_2016.type:
            self._receiver_port = AVR_X_2016.port
        else:
            self._receiver_port = AVR_X.port

        _LOGGER.info("Identified receiver type: '%s' on port: '%s'",
                     self._receiver_type, self._receiver_port)

        # Not an AVR-X device, start determination of sources
        if self._receiver_type == AVR.type:
            # Sources list is equal to list of renamed sources.
            non_x_sources, deleted_non_x_sources, status_success = (
                self._get_renamed_deleted_sourcesapp())

            # Backup if previous try with AppCommand was not successful
            if not status_success:
                non_x_sources, deleted_non_x_sources = (
                    self._get_renamed_deleted_sources())

            # Remove all deleted sources
            if self._show_all_inputs is False:
                for deleted_source in deleted_non_x_sources.items():
                    if deleted_source[1] == "DEL":
                        non_x_sources.pop(deleted_source[0], None)
            # Invalid source "SOURCE" needs to be deleted
            non_x_sources.pop("SOURCE", None)
            return non_x_sources

        # Following source determination of AVR-X receivers
        else:
            # receiver_sources is of type dict with "FuncName" as key and
            # "DefaultName" as value.
            receiver_sources = {}
            # Source determination from XML
            favorites = root.find(".//FavoriteStation")
            if favorites:
                for child in favorites:
                    if not child.tag.startswith("Favorite"):
                        continue
                    func_name = child.tag.upper()
                    self._favorite_func_list.append(func_name)
                    receiver_sources[func_name] = child.find("Name").text
            for xml_zonecapa in root.findall("DeviceZoneCapabilities"):
                # Currently only Main Zone (No=0) supported
                if xml_zonecapa.find("./Zone/No").text == "0":
                    # Get list of all input sources of receiver
                    xml_list = xml_zonecapa.find("./InputSource/List")
                    for xml_source in xml_list.findall("Source"):
                        receiver_sources[
                            xml_source.find(
                                "FuncName").text] = xml_source.find(
                                    "DefaultName").text

            return receiver_sources

    def _get_own_zone(self):
        """
        Get zone from actual instance.

        These zone information are used to evaluate responses of HTTP POST
        commands.
        """
        if self._zone == "Main":
            return "zone1"
        else:
            return self.zone.lower()

    def _update_media_data(self):
        """
        Update media data for playing devices.

        Internal method which queries device via HTTP to update media
        information (title, artist, etc.) and URL of cover image.
        """
        # Use different query URL based on selected source
        if self._input_func in self._netaudio_func_list:
            try:
                root = self.get_status_xml(self._urls.netaudiostatus)
            except (ValueError, requests.exceptions.RequestException):
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
                        self._image_url = (ALBUM_COVERS_URL.format(
                            host=self._host, port=self._receiver_port,
                            time=int(time.time())))
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

        elif self._input_func == "Tuner" or self._input_func == "TUNER":
            try:
                root = self.get_status_xml(self._urls.tunerstatus)
            except (ValueError, requests.exceptions.RequestException):
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
            self._image_url = (
                STATIC_ALBUM_URL.format(
                    host=self._host, port=self._receiver_port))

        elif self._input_func == "HD Radio" or self._input_func == "HDRADIO":
            try:
                root = self.get_status_xml(self._urls.hdtunerstatus)
            except (ValueError, requests.exceptions.RequestException):
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
            self._image_url = (
                STATIC_ALBUM_URL.format(
                    host=self._host, port=self._receiver_port))

        # No behavior implemented, so reset all variables for that source
        else:
            self._band = None
            self._frequency = None
            self._title = None
            self._artist = None
            self._album = None
            self._station = None
            # Assume PLAYING_DEVICE is always PLAYING
            self._state = STATE_PLAYING
            # No special cover, using a static one
            self._image_url = (
                STATIC_ALBUM_URL.format(
                    host=self._host, port=self._receiver_port))

        # Test if image URL is accessable
        if self._image_available is None and self._image_url is not None:
            try:
                imgres = requests.get(self._image_url, timeout=self.timeout)
            except requests.exceptions.RequestException:
                # No result set image URL to None
                self._image_url = None
            else:
                if imgres.status_code == 200:
                    self._image_available = True
                else:
                    _LOGGER.info('No album art available for your receiver')
                    # No image available. Save this status.
                    self._image_available = False
                    #  Set image URL to None.
                    self._image_url = None
        # Already tested that image URL is not accessible
        elif self._image_available is False:
            self._image_url = None

        # Finished
        return True

    def _get_status_from_xml_tags(self, root, relevant_tags):
        """
        Get relevant status tags from XML structure with this internal method.

        Status is saved to internal attributes.
        Return dictionary of tags not found in XML.
        """
        for child in root:
            if child.tag not in relevant_tags.keys():
                continue
            elif child.tag == "Power":
                self._power = child[0].text
                relevant_tags.pop(child.tag, None)
            elif child.tag == "InputFuncSelect":
                inputfunc = child[0].text
                if inputfunc is not None:
                    try:
                        self._input_func = self._input_func_list_rev[inputfunc]
                    except KeyError:
                        _LOGGER.info(
                            "No mapping for source %s found", inputfunc)
                        self._input_func = inputfunc
                    finally:
                        relevant_tags.pop(child.tag, None)
            elif child.tag == "MasterVolume":
                self._volume = child[0].text
                relevant_tags.pop(child.tag, None)
            elif child.tag == "Mute":
                self._mute = child[0].text
                relevant_tags.pop(child.tag, None)
            elif child.tag == "FriendlyName" and self._name is None:
                self._name = child[0].text
                relevant_tags.pop(child.tag, None)
            elif child.tag == "selectSurround" or child.tag == "SurrMode":
                self._sound_mode_raw = child[0].text.rstrip()
                relevant_tags.pop("selectSurround", None)
                relevant_tags.pop("SurrMode", None)

        return relevant_tags

    @property
    def zone(self):
        """Return Zone of this instance."""
        return self._zone

    @property
    def zones(self):
        """Return all Zone instances of the device."""
        return self._zones

    @property
    def name(self):
        """Return the name of the device as string."""
        return self._name

    @property
    def host(self):
        """Return the host of the device as string."""
        return self._host

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
        return bool(self._mute == STATE_ON)

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
    def support_sound_mode(self):
        """Return True if sound mode supported."""
        return self._get_support_sound_mode()

    @property
    def sound_mode(self):
        """Return the matched current sound mode as a string."""
        sound_mode_matched = self.match_sound_mode(self._sound_mode_raw)
        return sound_mode_matched

    @property
    def sound_mode_list(self):
        """Return a list of available sound modes as string."""
        return list(self._sound_mode_dict.keys())

    @property
    def sound_mode_dict(self):
        """Return a dict of available sound modes with their mapping values."""
        return dict(self._sound_mode_dict)

    @property
    def sm_match_dict(self):
        """Return a dict to map each sound_mode_raw to matching sound_mode."""
        return self._sm_match_dict

    @property
    def sound_mode_raw(self):
        """Return the current sound mode as string as received from the AVR."""
        return self._sound_mode_raw

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

    @property
    def netaudio_func_list(self):
        """Return list of network audio devices.

        Those devices should react to play, pause, next and previous
        track commands.
        """
        return self._netaudio_func_list

    @property
    def playing_func_list(self):
        """Return list of playing devices.

        Those devices offer additional information about what they are playing
        (e.g. title, artist, album, band, frequency, station, image_url).
        """
        return self._playing_func_list

    @property
    def receiver_port(self):
        """Return the receiver's port."""
        return self._receiver_port

    @property
    def receiver_type(self):
        """Return the receiver's type."""
        return self._receiver_type

    @property
    def show_all_inputs(self):
        """Indicate if all inputs are shown or just active one."""
        return self._show_all_inputs

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
        # AVR-X receiver needs source mapping to set input_func
        if self._receiver_type in [AVR_X.type, AVR_X_2016.type]:
            direct_mapping = False
            try:
                linp = CHANGE_INPUT_MAPPING[self._input_func_list[input_func]]
            except KeyError:
                direct_mapping = True
        else:
            direct_mapping = True
        # AVR-nonX receiver and if no mapping was found get parameter for
        # setting input_func directly
        if direct_mapping is True:
            try:
                linp = self._input_func_list[input_func]
            except KeyError:
                _LOGGER.error("No mapping for input source %s", input_func)
                return False
        # Create command URL and send command via HTTP GET
        try:
            if linp in self._favorite_func_list:
                command_url = self._urls.command_fav_src + linp
            else:
                command_url = self._urls.command_sel_src + linp

            if self.send_get_command(command_url):
                self._input_func = input_func
                return True
            else:
                return False
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: input function %s not set.",
                          input_func)
            return False

    @sound_mode.setter
    def sound_mode(self, sound_mode):
        """Setter function for sound_mode to switch sound_mode of device."""
        self.set_sound_mode(sound_mode)

    def _set_all_zone_stereo(self, zst_on):
        """
        Set All Zone Stereo option on the device.

        Calls command to activate/deactivate the mode
        Return "True" when successfully sent.
        """
        command_url = self._urls.command_set_all_zone_stereo
        if zst_on:
            command_url += "ZST ON"
        else:
            command_url += "ZST OFF"

        try:
            return self.send_get_command(command_url)
        except requests.exceptions.RequestException:
            _LOGGER.error(
                "Connection error: unable to set All Zone Stereo to %s",
                zst_on)
            return False

    def set_sound_mode(self, sound_mode):
        """
        Set sound_mode of device.

        Valid values depend on the device and should be taken from
        "sound_mode_list".
        Return "True" on success and "False" on fail.
        """
        if sound_mode == ALL_ZONE_STEREO:
            if self._set_all_zone_stereo(True):
                self._sound_mode_raw = ALL_ZONE_STEREO
                return True
            else:
                return False
        if self._sound_mode_raw == ALL_ZONE_STEREO:
            if not self._set_all_zone_stereo(False):
                return False
        # For selection of sound mode other names then at receiving sound modes
        # have to be used
        # Therefore source mapping is needed to get sound_mode
        # Create command URL and send command via HTTP GET
        command_url = self._urls.command_sel_sound_mode + sound_mode
        # sent command
        try:
            if self.send_get_command(command_url):
                self._sound_mode_raw = self._sound_mode_dict[sound_mode][0]
                return True
            else:
                return False
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: sound mode function %s not set.",
                          sound_mode)
            return False

    def set_sound_mode_dict(self, sound_mode_dict):
        """Set the matching dictionary used to match the raw sound mode."""
        error_msg = ("Syntax of sound mode dictionary not valid, "
                     "use: OrderedDict([('COMMAND', ['VALUE1','VALUE2'])])")
        if isinstance(sound_mode_dict, dict):
            mode_list = list(sound_mode_dict.values())
            for sublist in mode_list:
                if isinstance(sublist, list):
                    for element in sublist:
                        if not isinstance(element, str):
                            _LOGGER.error(error_msg)
                            return False
                else:
                    _LOGGER.error(error_msg)
                    return False
        else:
            _LOGGER.error(error_msg)
            return False
        self._sound_mode_dict = sound_mode_dict
        self._sm_match_dict = self.construct_sm_match_dict()
        return True

    def construct_sm_match_dict(self):
        """
        Construct the sm_match_dict.

        Reverse the key value structure. The sm_match_dict is bigger,
        but allows for direct matching using a dictionary key access.
        The sound_mode_dict is uses externally to set this dictionary
        because that has a nicer syntax.
        """
        mode_dict = list(self._sound_mode_dict.items())
        match_mode_dict = {}
        for matched_mode, sublist in mode_dict:
            for raw_mode in sublist:
                match_mode_dict[raw_mode.upper()] = matched_mode
        return match_mode_dict

    def match_sound_mode(self, sound_mode_raw):
        """Match the raw_sound_mode to its corresponding sound_mode."""
        try:
            sound_mode = self._sm_match_dict[sound_mode_raw.upper()]
            return sound_mode
        except KeyError:
            smr_up = sound_mode_raw.upper()
            self._sound_mode_dict[smr_up] = [smr_up]
            self._sm_match_dict = self.construct_sm_match_dict()
            _LOGGER.warning("Not able to match sound mode: '%s', "
                            "returning raw sound mode.", sound_mode_raw)
        return sound_mode_raw

    def toggle_play_pause(self):
        """Toggle play pause media player."""
        # Use Play/Pause button only for sources which support NETAUDIO
        if (self._state == STATE_PLAYING and
                self._input_func in self._netaudio_func_list):
            return self._pause()
        elif self._input_func in self._netaudio_func_list:
            return self._play()

    def _play(self):
        """Send play command to receiver command via HTTP post."""
        # Use pause command only for sources which support NETAUDIO
        if self._input_func in self._netaudio_func_list:
            body = {"cmd0": "PutNetAudioCommand/CurEnter",
                    "cmd1": "aspMainZone_WebUpdateStatus/",
                    "ZoneName": "MAIN ZONE"}
            try:
                if self.send_post_command(
                        self._urls.command_netaudio_post, body):
                    self._state = STATE_PLAYING
                    return True
                else:
                    return False
            except requests.exceptions.RequestException:
                _LOGGER.error("Connection error: play command not sent.")
                return False

    def _pause(self):
        """Send pause command to receiver command via HTTP post."""
        # Use pause command only for sources which support NETAUDIO
        if self._input_func in self._netaudio_func_list:
            body = {"cmd0": "PutNetAudioCommand/CurEnter",
                    "cmd1": "aspMainZone_WebUpdateStatus/",
                    "ZoneName": "MAIN ZONE"}
            try:
                if self.send_post_command(
                        self._urls.command_netaudio_post, body):
                    self._state = STATE_PAUSED
                    return True
                else:
                    return False
            except requests.exceptions.RequestException:
                _LOGGER.error("Connection error: pause command not sent.")
                return False

    def previous_track(self):
        """Send previous track command to receiver command via HTTP post."""
        # Use previous track button only for sources which support NETAUDIO
        if self._input_func in self._netaudio_func_list:
            body = {"cmd0": "PutNetAudioCommand/CurUp",
                    "cmd1": "aspMainZone_WebUpdateStatus/",
                    "ZoneName": "MAIN ZONE"}
            try:
                return bool(self.send_post_command(
                    self._urls.command_netaudio_post, body))
            except requests.exceptions.RequestException:
                _LOGGER.error(
                    "Connection error: previous track command not sent.")
                return False

    def next_track(self):
        """Send next track command to receiver command via HTTP post."""
        # Use next track button only for sources which support NETAUDIO
        if self._input_func in self._netaudio_func_list:
            body = {"cmd0": "PutNetAudioCommand/CurDown",
                    "cmd1": "aspMainZone_WebUpdateStatus/",
                    "ZoneName": "MAIN ZONE"}
            try:
                return bool(self.send_post_command(
                    self._urls.command_netaudio_post, body))
            except requests.exceptions.RequestException:
                _LOGGER.error("Connection error: next track command not sent.")
                return False

    def power_on(self):
        """Turn off receiver via HTTP get command."""
        try:
            if self.send_get_command(self._urls.command_power_on):
                self._power = POWER_ON
                self._state = STATE_ON
                return True
            else:
                return False
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: power on command not sent.")
            return False

    def power_off(self):
        """Turn off receiver via HTTP get command."""
        try:
            if self.send_get_command(self._urls.command_power_standby):
                self._power = POWER_STANDBY
                self._state = STATE_OFF
                return True
            else:
                return False
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: power off command not sent.")
            return False

    def volume_up(self):
        """Volume up receiver via HTTP get command."""
        try:
            return bool(self.send_get_command(self._urls.command_volume_up))
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: volume up command not sent.")
            return False

    def volume_down(self):
        """Volume down receiver via HTTP get command."""
        try:
            return bool(self.send_get_command(self._urls.command_volume_down))
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: volume down command not sent.")
            return False

    def set_volume(self, volume):
        """
        Set receiver volume via HTTP get command.

        Volume is send in a format like -50.0.
        Minimum is -80.0, maximum at 18.0
        """
        if volume < -80 or volume > 18:
            raise ValueError("Invalid volume")

        try:
            return bool(self.send_get_command(
                self._urls.command_set_volume % volume))
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: set volume command not sent.")
            return False

    def mute(self, mute):
        """Mute receiver via HTTP get command."""
        try:
            if mute:
                if self.send_get_command(self._urls.command_mute_on):
                    self._mute = STATE_ON
                    return True
                else:
                    return False
            else:
                if self.send_get_command(self._urls.command_mute_off):
                    self._mute = STATE_OFF
                    return True
                else:
                    return False
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: mute command not sent.")
            return False


class DenonAVRZones(DenonAVR):
    """Representing an additional zone of a Denon AVR Device."""

    def __init__(self, parent_avr, zone, name):
        """
        Initialize additional zones of DenonAVR.

        :param parent_avr: Instance of parent DenonAVR.
        :type parent_avr: denonavr.DenonAVR

        :param zone: Zone name of this instance
        :type zone: str

        :param name: Device name, if None FriendlyName of device is used.
        :type name: str
        """
        self._parent_avr = parent_avr
        self._zone = zone
        super().__init__(self._parent_avr.host, name=name,
                         show_all_inputs=self._parent_avr.show_all_inputs,
                         timeout=self._parent_avr.timeout)

    @property
    def sound_mode(self):
        """Return the matched current sound mode as a string."""
        sound_mode_matched = self._parent_avr.match_sound_mode(
            self._parent_avr.sound_mode_raw)
        return sound_mode_matched

    @property
    def sound_mode_list(self):
        """Return a list of available sound modes as string."""
        return list(self._parent_avr.sound_mode_dict.keys())

    @property
    def sound_mode_dict(self):
        """Return a dict of available sound modes with their mapping values."""
        return dict(self._parent_avr.sound_mode_dict)

    @property
    def sm_match_dict(self):
        """Return a dict to map each sound_mode_raw to matching sound_mode."""
        return self._parent_avr.sm_match_dict

    @property
    def sound_mode_raw(self):
        """Return the current sound mode as string as received from the AVR."""
        return self._parent_avr.sound_mode_raw

    @sound_mode.setter
    def sound_mode(self, sound_mode):
        """Setter function for sound_mode to switch sound_mode of device."""
        self.set_sound_mode(sound_mode)

    def set_sound_mode(self, sound_mode):
        """
        Set sound_mode of device.

        Valid values depend on the device and should be taken from
        "sound_mode_list".
        Return "True" on success and "False" on fail.
        """
        return self._parent_avr.set_sound_mode(sound_mode)
