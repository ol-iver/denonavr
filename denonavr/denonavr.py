#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module implements the interface to Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""
# pylint: disable=too-many-lines
# pylint: disable=no-else-return

from io import BytesIO
import logging
import time
import re
import html
import xml.etree.ElementTree as ET
import requests

_LOGGER = logging.getLogger('DenonAVR')

SOURCE_MAPPING = {'Internet Radio': 'IRP', 'Online Music': 'NET',
                  'TV Audio': 'TV', 'DVD': 'DVD', 'Media Player': 'MPLAY',
                  'CD': 'CD', 'Game': 'GAME', 'AUX1': 'AUX1', 'AUX2': 'AUX2',
                  'iPod/USB': 'USB/IPOD', 'Bluetooth': 'BT', 'Blu-ray': 'BD',
                  'CBL/SAT': 'SAT/CBL', 'Tuner': 'TUNER', 'Phono': 'PHONO',
                  'Media Server': 'SERVER', 'HD Radio': 'HDRADIO',
                  'DVD/Blu-ray': 'DVD', 'Spotify': 'SPOTIFY',
                  'Flickr': 'FLICKR', 'Favorites': 'FAVORITES'}

PLAYING_SOURCES = ("Online Music", "Media Server", "iPod/USB", "Bluetooth",
                   "Internet Radio", "Favorites", "Spotify", "Flickr", "Tuner",
                   "HD Radio", "TUNER", "NET/USB", "HDRADIO", "Music Server")
NETAUDIO_SOURCES = ("Online Music", "Media Server", "iPod/USB", "Bluetooth",
                    "Internet Radio", "Favorites", "Spotify", "Flickr",
                    "NET/USB", "Music Server", "NETWORK")

APPCOMMAND_URL = "/goform/AppCommand.xml"
STATUS_URL = "/goform/formMainZone_MainZoneXmlStatus.xml"
MAINZONE_URL = "/goform/formMainZone_MainZoneXml.xml"
DEVICEINFO_URL = "/goform/Deviceinfo.xml"
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
        # Initially assume receiver is a model like AVR-X...
        self._avr_x = True
        self._mute = STATE_OFF
        self._volume = "--"
        self._input_func = None
        self._input_func_list = {}
        self._input_func_list_rev = {}
        self._netaudio_func_list = []
        self._playing_func_list = []
        self._state = None
        self._power = None
        self._image_url = (
            "http://{host}/img/album%20art_S.png".format(host=host))
        self._title = None
        self._artist = None
        self._album = None
        self._band = None
        self._frequency = None
        self._station = None
        # Fill variables with initial values
        self._update_input_func_list()
        self.update()

    @classmethod
    def get_status_xml(cls, host, command):
        """Get status XML via HTTP and return it as XML ElementTree."""
        # Get XML structure via HTTP get
        try:
            res = requests.get("http://{host}{command}"
                               .format(host=host, command=command), timeout=2)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("ConnectionError retrieving data from host %s",
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
            _LOGGER.error("ConnectionError sending GET request to host %s",
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
            _LOGGER.error("ConnectionError sending POST request to host %s",
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
            return False

        # Set all tags to be evaluated
        relevant_tags = {'Power': None, 'InputFuncSelect': None, 'Mute': None,
                         'MasterVolume': None, 'FriendlyName': None}

        if self._name is not None:
            relevant_tags.pop("FriendlyName", None)

        # Get the relevant tags from the XML structure and save them to
        # internal attributes
        relevant_tags = self._get_status_from_xml_tags(root, relevant_tags)

        # If not all tags could be found try to find them in different XML
        if relevant_tags:
            try:
                root = self.get_status_xml(self._host, STATUS_URL)
            except ConnectionError:
                return False

            # Try to get the rest of the tags from this XML
            relevant_tags = self._get_status_from_xml_tags(root, relevant_tags)

            if relevant_tags:
                _LOGGER.error("Missing status information from XML for: %s",
                              ", ".join(relevant_tags.keys()))

        # Set state and media image URL based on current source
        # and power status
        if (self._power == POWER_ON) and (
                self._input_func in self._playing_func_list):
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

        # Get/update sources list if current source is not known yet
        if self._input_func not in self._input_func_list:
            if self._update_input_func_list():
                pass
            else:
                _LOGGER.error((
                    "Input function list for Denon receiver at host %s "
                    "could not be updated"), self._host)

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
        receiver_sources = self._get_receiver_sources()

        # If no sources for the receiver could be found, update failed
        if receiver_sources is None:
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
            for deleted_source in deleted_sources.items():
                if deleted_source[1] == "DEL":
                    receiver_sources.pop(deleted_source[0], None)

            # Clear and rebuild the sources lists
            self._input_func_list.clear()
            self._input_func_list_rev.clear()
            self._netaudio_func_list.clear()
            self._playing_func_list.clear()
            for item in receiver_sources.items():
                # For renamed sources use those names and save the default name
                # for a later mapping
                if item[0] in renamed_sources:
                    self._input_func_list[renamed_sources[item[0]]] = item[1]
                    self._input_func_list_rev[
                        item[0]] = renamed_sources[item[0]]
                    # If the source is a netaudio source, save its renamed name
                    if item[1] in NETAUDIO_SOURCES:
                        self._netaudio_func_list.append(
                            renamed_sources[item[0]])
                    # If the source is a playing source, save its renamed name
                    if item[1] in PLAYING_SOURCES:
                        self._playing_func_list.append(
                            renamed_sources[item[0]])
                # Otherwise the default names are used
                else:
                    self._input_func_list[item[1]] = item[1]
                    self._input_func_list_rev[item[0]] = item[1]
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
                if item[1] in NETAUDIO_SOURCES:
                    self._netaudio_func_list.append(item[1])
                # If the source is a playing source, save its name
                if item[1] in PLAYING_SOURCES:
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
                root = self.get_status_xml(self._host, STATUS_URL)
            else:
                root = self.get_status_xml(self._host, MAINZONE_URL)
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
        post_tree.write(body, encoding='utf-8', xml_declaration=True)

        # Query receivers AppCommand.xml
        try:
            res = self.send_post_command(
                self._host, APPCOMMAND_URL, body.getvalue())
        except ConnectionError:
            body.close()
            return (renamed_sources, deleted_sources, False)

        # Buffered XML not needed anymore: close
        body.close()

        if 'Access Error: Data follows' in res:
            return (renamed_sources, deleted_sources, False)

        try:
            # Return XML ElementTree
            root = ET.fromstring(res)
        except (ET.ParseError, TypeError):
            _LOGGER.error(
                "Host %s returned malformed XML after command: %s",
                self._host, APPCOMMAND_URL)
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
        # This XML is needed to get the sources of the receiver
        try:
            root = self.get_status_xml(self._host, DEVICEINFO_URL)
        except ConnectionError:
            _LOGGER.error("Connection Error: Receiver sources list empty")
            return None

        # Test if receiver is a AVR-X
        try:
            avr_x_pattern = re.compile(r'.*AVR-X.*')
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

    def _get_active_input_func(self, input_func, net_func):
        """
        Get active input function from receiver.

        Internal method which determines the currently active input function.
        Handling of AVR-X and AVR-nonX receivers is different. AVR-X receivers
        are returning the renamed value whereas AVR-nonX receivers are
        returning the original value of input_func
        Additionally for AVR-X receivers a special handling is necessary
        because network audio sources could not be completely determined
        by the input_func field.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements
        # input_func handling of AVR-X receivers
        if self._avr_x is True:
            if input_func in self._netaudio_func_list:
                # Get status XML from Denon receiver via HTTP
                try:
                    root = self.get_status_xml(self._host, STATUS_URL)
                except ConnectionError:
                    return input_func

                tmp_input_func = root.find("InputFuncSelect")[0].text

                try:
                    new_input_func = self._input_func_list_rev[tmp_input_func]
                except KeyError:
                    source_found = False
                    for k, i in SOURCE_MAPPING.items():
                        if i == tmp_input_func:
                            new_input_func = k
                            source_found = True

                    if source_found is False:
                        _LOGGER.error(
                            "No mapping for network audio source %s",
                            tmp_input_func)
                        return input_func

                return new_input_func

            # Not a network audio function -> output = input
            else:
                return input_func

        # input_func handling of AVR-nonX receivers
        else:
            if input_func == "NET":
                try:
                    new_input_func = self._input_func_list_rev[net_func]
                except KeyError:
                    _LOGGER.error(
                        "No mapping for network audio source %s", net_func)
                    return net_func
            else:
                try:
                    new_input_func = self._input_func_list_rev[input_func]
                except KeyError:
                    _LOGGER.error(
                        "No mapping for audio source %s", input_func)
                    return input_func

            return new_input_func

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

        elif self._input_func == "Tuner" or self._input_func == "TUNER":
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
        elif self._input_func == "HD Radio" or self._input_func == "HDRADIO":
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
                self._input_func = self._get_active_input_func(
                    child[0].text, root.find("NetFuncSelect")[0].text)
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
                linp = SOURCE_MAPPING[self._input_func_list[input_func]]
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
                    self._mute = STATE_ON
                    return True
                else:
                    return False
            else:
                if self.send_get_command(self._host, COMMAND_MUTE_OFF_URL):
                    self._mute = STATE_OFF
                    return True
                else:
                    return False
        except ConnectionError:
            return False
