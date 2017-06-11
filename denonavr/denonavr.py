#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module implements the interface to Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""
# pylint: disable=too-many-lines
# pylint: disable=no-else-return

from collections import namedtuple
from io import BytesIO
import logging
import time
import re
import html
import xml.etree.ElementTree as ET
import requests

_LOGGER = logging.getLogger("DenonAVR")

DEVICEINFO_AVR_X_PATTERN = r"(.*AVR-X.*|.*SR5008|.*NR1604)"

SOURCE_MAPPING = {"TV AUDIO": "TV", "iPod/USB": "USB/IPOD", "Bluetooth": "BT",
                  "Blu-ray": "BD", "CBL/SAT": "SAT/CBL", "NETWORK": "NET"}

CHANGE_INPUT_MAPPING = {"Internet Radio": "IRP", "Online Music": "NET",
                        "Media Player": "MPLAY", "Media Server": "SERVER",
                        "Spotify": "SPOTIFY", "Flickr": "FLICKR",
                        "Favorites": "FAVORITES"}

PLAYING_SOURCES = ("Online Music", "Media Server", "iPod/USB", "Bluetooth",
                   "Internet Radio", "Favorites", "SpotifyConnect", "Flickr",
                   "TUNER", "NET/USB", "HDRADIO", "Music Server", "NETWORK",
                   "NET")
NETAUDIO_SOURCES = ("Online Music", "Media Server", "iPod/USB", "Bluetooth",
                    "Internet Radio", "Favorites", "SpotifyConnect", "Flickr",
                    "NET/USB", "Music Server", "NETWORK", "NET")

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
                     "command_netaudio_post"])

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
                             command_netaudio_post=COMMAND_NETAUDIO_POST_URL)

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
                          command_netaudio_post=COMMAND_NETAUDIO_POST_URL)

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
                          command_netaudio_post=COMMAND_NETAUDIO_POST_URL)

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


class DenonAVR(object):
    """Representing a Denon AVR Device."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    def __init__(self, host, name=None, show_all_inputs=False,
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
        self._zone = "Main"
        self._zones = {self._zone: self}
        self._urls = DENONAVR_URLS
        # Initially assume receiver is a model like AVR-X...
        self._avr_x = True
        self._show_all_inputs = show_all_inputs
        self._mute = STATE_OFF
        self._volume = "--"
        self._input_func = None
        self._input_func_list = {}
        self._input_func_list_rev = {}
        self._netaudio_func_list = []
        self._playing_func_list = []
        self._favorite_func_list = []
        self._state = None
        self._power = None
        self._image_url = (
            "http://{host}/img/album%20art_S.png".format(host=self._host))
        self._title = None
        self._artist = None
        self._album = None
        self._band = None
        self._frequency = None
        self._station = None
        # Fill variables with initial values
        self._update_input_func_list()
        self.update()
        # Create instances of additional zones if requested
        if add_zones is not None:
            self.create_zones(add_zones)

    @classmethod
    def get_status_xml(cls, host, command):
        """Get status XML via HTTP and return it as XML ElementTree."""
        # Get XML structure via HTTP get
        try:
            res = requests.get("http://{host}{command}"
                               .format(host=host, command=command), timeout=2)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Connection error retrieving data from host %s",
                          host)
            raise ConnectionError
        except requests.exceptions.Timeout:
            _LOGGER.error("Timeout retrieving data from host %s", host)
            raise ConnectionError
        # Continue with XML processing only if HTTP status code = 200
        if res.status_code == 200:
            try:
                # Return XML ElementTree
                return ET.fromstring(res.text)
            except ET.ParseError:
                _LOGGER.error(
                    "Host %s returned malformed XML after command: %s",
                    host, command)
                raise ConnectionError
        else:
            _LOGGER.error((
                "Host %s returned HTTP status code %s "
                "when trying to receive data"), host, res.status_code)
            raise ConnectionError

    @classmethod
    def send_get_command(cls, host, command):
        """Send command via HTTP get to receiver."""
        # Send commands via HTTP get
        try:
            res = requests.get("http://{host}{command}"
                               .format(host=host, command=command), timeout=2)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Connection error sending GET request to host %s",
                          host)
            raise ConnectionError
        except requests.exceptions.Timeout:
            _LOGGER.error("Timeout sending GET request to host %s", host)
            raise ConnectionError
        if res.status_code == 200:
            return True
        else:
            _LOGGER.error((
                "Host %s returned HTTP status code %s "
                "when trying to send GET commands"), host, res.status_code)
            return False

    @classmethod
    def send_post_command(cls, host, command, body):
        """Send command via HTTP post to receiver."""
        # Send commands via HTTP post
        try:
            res = requests.post(
                "http://{host}{command}"
                .format(host=host, command=command), data=body)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Connection error sending POST request to host %s",
                          host)
            raise ConnectionError
        except requests.exceptions.Timeout:
            _LOGGER.error("Timeout sending POST request to host %s", host)
            raise ConnectionError
        if res.status_code == 200:
            return res.text
        else:
            _LOGGER.error((
                "Host %s returned HTTP status code %s when trying to "
                "send POST commands"), host, res.status_code)
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

        Method queries device via HTTP and updates instance attributes.
        Returns "True" on success and "False" on fail.
        """
        # pylint: disable=too-many-branches
        # If name is not set yet, get it from Main Zone URL
        if self._name is None and self._urls.mainzone is not None:
            name_tag = {"FriendlyName": None}
            try:
                root = self.get_status_xml(self._host, self._urls.mainzone)
                # Get the tags from this XML
                name_tag = self._get_status_from_xml_tags(root, name_tag)
            except ConnectionError:
                _LOGGER.error("Receiver name could not be determined")

        # Set all tags to be evaluated
        relevant_tags = {"Power": None, "InputFuncSelect": None, "Mute": None,
                         "MasterVolume": None}

        # Get status XML from Denon receiver via HTTP
        try:
            root = self.get_status_xml(self._host, self._urls.status)
            # Get the tags from this XML
            relevant_tags = self._get_status_from_xml_tags(root, relevant_tags)
        except ConnectionError:
            pass

        if relevant_tags:
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

        # Get/update sources list if current source is not known yet
        if (self._input_func not in self._input_func_list
                and self._input_func is not None):
            if self._update_input_func_list():
                _LOGGER.info("List of input functions refreshed.")
            else:
                _LOGGER.error((
                    "Input function list for Denon receiver at host %s "
                    "could not be updated."), self._host)

        # Finished
        return True

    def _update_input_func_list(self):
        """
        Update sources list from receiver.

        Internal method which updates sources list of receiver after getting
        sources and potential renaming information from receiver.
        """
        # pylint: disable=too-many-branches
        # Get all sources and renaming information from receiver
        # For structural information of the variables please see the methods
        try:
            receiver_sources = self._get_receiver_sources()
        except ConnectionError:
            # If connection error occurred, update failed
            _LOGGER.error("Connection error: Receiver sources list empty")
            return False

        # First input_func_list determination of AVR-X receivers
        if self._avr_x is True:
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
        else:
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

        # Finished
        return True

    def _get_renamed_deleted_sources(self):
        """
        Get renamed and deleted sources lists from receiver .

        Internal method which queries device via HTTP to get names of renamed
        input sources.
        """
        # pylint: disable=too-many-branches
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
            if self._avr_x is True:
                root = self.get_status_xml(self._host, self._urls.status)
            # URL only available for Main Zone.
            elif self._urls.mainzone is not None:
                root = self.get_status_xml(self._host, self._urls.mainzone)
            else:
                return (renamed_sources, deleted_sources)
        except ConnectionError:
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

        # Prepare POST XML body for AppCommand.xml
        post_root = ET.Element("tx")
        # Append tag for renamed sources
        item = ET.Element("cmd")
        item.set("id", "1")
        item.text = "GetRenameSource"
        post_root.append(item)
        # Append tag for deleted sources
        item = ET.Element("cmd")
        item.set("id", "1")
        item.text = "GetDeletedSource"
        post_root.append(item)
        # Buffer XML body as binary IO
        body = BytesIO()
        post_tree = ET.ElementTree(post_root)
        post_tree.write(body, encoding="utf-8", xml_declaration=True)

        # Query receivers AppCommand.xml
        try:
            res = self.send_post_command(
                self._host, self._urls.appcommand, body.getvalue())
        except ConnectionError:
            body.close()
            return (renamed_sources, deleted_sources, False)

        # Buffered XML not needed anymore: close
        body.close()

        try:
            # Return XML ElementTree
            root = ET.fromstring(res)
        except (ET.ParseError, TypeError):
            _LOGGER.error(
                "Host %s returned malformed XML after command: %s",
                self._host, self._urls.appcommand)
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
        """
        # pylint: disable=too-many-branches
        # This XML is needed to get the sources of the receiver
        root = self.get_status_xml(self._host, self._urls.deviceinfo)

        # Test if receiver is a AVR-X
        try:
            avr_x_pattern = re.compile(DEVICEINFO_AVR_X_PATTERN)
            self._avr_x = bool(
                avr_x_pattern.search(root.find("ModelName").text) is not None)
        except AttributeError:
            # AttributeError occurs when ModelName tag is not found.
            # In this case there is no AVR-X device
            self._avr_x = False

        if self._avr_x is False:
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

        else:
            # Following source determination of AVR-X receivers
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

    def _update_media_data(self):
        """
        Update media data for playing devices.

        Internal method which queries device via HTTP to update media
        information (title, artist, etc.) and URL of cover image.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # Use different query URL based on selected source
        if self._input_func in self._netaudio_func_list:
            try:
                root = self.get_status_xml(
                    self._host, self._urls.netaudiostatus)
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

        elif self._input_func == "Tuner" or self._input_func == "TUNER":
            try:
                root = self.get_status_xml(self._host, self._urls.tunerstatus)
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
        elif self._input_func == "HD Radio" or self._input_func == "HDRADIO":
            try:
                root = self.get_status_xml(
                    self._host, self._urls.hdtunerstatus)
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
                "http://{host}/img/album%20art_S.png".format(host=self._host))

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
                        _LOGGER.error(
                            "No mapping for source %s", inputfunc)
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
        if self._avr_x is True:
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

            if self.send_get_command(self._host, command_url):
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
            return self._pause()
        elif self._input_func in NETAUDIO_SOURCES:
            return self._play()

    def _play(self):
        """Send play command to receiver command via HTTP post."""
        # Use pause command only for sources which support NETAUDIO
        if self._input_func in NETAUDIO_SOURCES:
            body = {"cmd0": "PutNetAudioCommand/CurEnter",
                    "cmd1": "aspMainZone_WebUpdateStatus/",
                    "ZoneName": "MAIN ZONE"}
            try:
                if self.send_post_command(
                        self._host, self._urls.command_netaudio_post, body):
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
                        self._host, self._urls.command_netaudio_post, body):
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
                    self._host, self._urls.command_netaudio_post, body))
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
                    self._host, self._urls.command_netaudio_post, body))
            except ConnectionError:
                return False

    def power_on(self):
        """Turn off receiver via HTTP get command."""
        try:
            if self.send_get_command(self._host, self._urls.command_power_on):
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
            if self.send_get_command(self._host,
                                     self._urls.command_power_standby):
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
                self._host, self._urls.command_volume_up))
        except ConnectionError:
            return False

    def volume_down(self):
        """Volume down receiver via HTTP get command."""
        try:
            return bool(self.send_get_command(
                self._host, self._urls.command_volume_down))
        except ConnectionError:
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
                self._host, self._urls.command_set_volume % volume))
        except ConnectionError:
            return False

    def mute(self, mute):
        """Mute receiver via HTTP get command."""
        try:
            if mute:
                if self.send_get_command(self._host,
                                         self._urls.command_mute_on):
                    self._mute = STATE_ON
                    return True
                else:
                    return False
            else:
                if self.send_get_command(self._host,
                                         self._urls.command_mute_off):
                    self._mute = STATE_OFF
                    return True
                else:
                    return False
        except ConnectionError:
            return False


class DenonAVRZones(DenonAVR):
    """Representing an additional zone of a Denon AVR Device."""

    # pylint: disable=too-many-instance-attributes

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
        # pylint: disable=super-init-not-called
        # pylint: disable=protected-access
        self._parent_avr = parent_avr
        self._zone = zone

        if self._zone == "Zone2":
            self._urls = ZONE2_URLS
        elif self._zone == "Zone3":
            self._urls = ZONE3_URLS
        else:
            raise ValueError("Invalid zone {}".format(self._zone))

        self._name = name
        self._host = self._parent_avr.host
        # Initially assume receiver is a model like AVR-X...
        self._avr_x = self._parent_avr._avr_x
        self._show_all_inputs = self._parent_avr._show_all_inputs
        self._mute = STATE_OFF
        self._volume = "--"
        self._input_func = None
        # Get func lists from parent receiver
        self._input_func_list = self._parent_avr._input_func_list
        self._input_func_list_rev = self._parent_avr._input_func_list_rev
        self._netaudio_func_list = self._parent_avr._netaudio_func_list
        self._playing_func_list = self._parent_avr._playing_func_list
        self._favorite_func_list = self._parent_avr._favorite_func_list
        self._state = None
        self._power = None
        self._image_url = (
            "http://{host}/img/album%20art_S.png".format(host=self._host))
        self._title = None
        self._artist = None
        self._album = None
        self._band = None
        self._frequency = None
        self._station = None
        # Fill variables with initial values
        self.update()

    def _update_input_func_list(self):
        """
        Update sources list from receiver.

        Input func list is prepared by parent receiver.
        Thus calling its method instead.
        """
        # pylint: disable=protected-access
        return self._parent_avr._update_input_func_list()

    def create_zones(self, add_zones):
        """Only call this method from parent AVR (Main Zone)."""
        raise NotImplementedError(
            "Only call this method at parent AVR (Main Zone).")

    def _get_renamed_deleted_sources(self):
        """Only call this method from parent AVR (Main Zone)."""
        raise NotImplementedError(
            "Only call this method at parent AVR (Main Zone).")

    def _get_renamed_deleted_sourcesapp(self):
        """Only call this method from parent AVR (Main Zone)."""
        raise NotImplementedError(
            "Only call this method at parent AVR (Main Zone).")

    def _get_receiver_sources(self):
        """Only call this method from parent AVR (Main Zone)."""
        raise NotImplementedError(
            "Only call this method at parent AVR (Main Zone).")
