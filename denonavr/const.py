#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module inherits constants for Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import re
from collections import namedtuple
from typing import Literal

import attr

# Attr constants
DENON_ATTR_SETATTR = [attr.setters.validate, attr.setters.convert]

# Types for constants
ReceiverType = namedtuple("ReceiverType", ["type", "port"])
DescriptionType = namedtuple("DescriptionType", ["port", "url"])
ReceiverURLs = namedtuple(
    "ReceiverURLs",
    [
        "appcommand",
        "appcommand0300",
        "status",
        "mainzone",
        "deviceinfo",
        "netaudiostatus",
        "tunerstatus",
        "hdtunerstatus",
        "command_sel_src",
        "command_fav_src",
        "command_power_on",
        "command_power_standby",
        "command_volume_up",
        "command_volume_down",
        "command_set_volume",
        "command_mute_on",
        "command_mute_off",
        "command_sel_sound_mode",
        "command_neural_x_on_off",
        "command_imax_auto_off",
        "command_imax_audio_settings",
        "command_imax_hpf",
        "command_imax_lpf",
        "command_imax_subwoofer_mode",
        "command_imax_subwoofer_output",
        "command_cinema_eq",
        "command_netaudio_post",
        "command_set_all_zone_stereo",
        "command_pause",
        "command_play",
        "command_cusor_up",
        "command_cusor_down",
        "command_cusor_left",
        "command_cusor_right",
        "command_cusor_enter",
        "command_back",
        "command_info",
        "command_options",
        "command_setup_open",
        "command_setup_close",
        "command_setup_query",
        "command_channel_level_adjust",
        "command_dimmer_toggle",
        "command_dimmer_set",
        "command_channel_volume",
        "command_channel_volumes_reset",
        "command_subwoofer_on_off",
        "command_subwoofer_level",
        "command_lfe",
        "command_tactile_transducer",
        "command_tactile_transducer_level",
        "command_tactile_transducer_lpf",
        "command_delay_up",
        "command_delay_down",
        "command_auromatic_3d_preset",
        "command_auromatic_3d_strength",
        "command_auro_3d_mode",
        "command_dirac_filter",
        "command_eco_mode",
        "command_lfc",
        "command_containment_amount",
        "command_loudness_management",
        "command_bass_sync",
        "command_dialog_enhancer",
        "command_hdmi_output",
        "command_hdmi_audio_decode",
        "command_quick_select_mode",
        "command_quick_select_memory",
        "command_auto_standby",
        "command_sleep",
        "command_center_spread",
        "command_video_processing_mode",
        "command_room_size",
        "command_status",
        "command_system_reset",
        "command_network_restart",
        "command_trigger",
        "command_speaker_preset",
        "command_bluetooth_transmitter",
        "command_dialog_control",
        "command_speaker_virtualizer",
        "command_effect_speaker_selection",
        "command_drc",
        "command_delay_time",
        "command_audio_restorer",
        "command_remote_control_lock",
        "command_panel_lock",
        "command_panel_and_volume_lock",
        "command_graphic_eq",
        "command_headphone_eq",
    ],
)
TelnetCommands = namedtuple(
    "TelnetCommands",
    [
        "command_sel_src",
        "command_fav_src",
        "command_power_on",
        "command_power_standby",
        "command_volume_up",
        "command_volume_down",
        "command_set_volume",
        "command_mute_on",
        "command_mute_off",
        "command_sel_sound_mode",
        "command_neural_x_on_off",
        "command_imax_auto_off",
        "command_imax_audio_settings",
        "command_imax_hpf",
        "command_imax_lpf",
        "command_imax_subwoofer_mode",
        "command_imax_subwoofer_output",
        "command_cinema_eq",
        "command_set_all_zone_stereo",
        "command_pause",
        "command_play",
        "command_multieq",
        "command_dynamiceq",
        "command_reflevoffset",
        "command_dynamicvol",
        "command_tonecontrol",
        "command_bass",
        "command_treble",
        "command_cusor_up",
        "command_cusor_down",
        "command_cusor_left",
        "command_cusor_right",
        "command_cusor_enter",
        "command_back",
        "command_info",
        "command_options",
        "command_setup_open",
        "command_setup_close",
        "command_setup_query",
        "command_channel_level_adjust",
        "command_dimmer_toggle",
        "command_dimmer_set",
        "command_channel_volume",
        "command_channel_volumes_reset",
        "command_subwoofer_on_off",
        "command_subwoofer_level",
        "command_lfe",
        "command_tactile_transducer",
        "command_tactile_transducer_level",
        "command_tactile_transducer_lpf",
        "command_delay_up",
        "command_delay_down",
        "command_auromatic_3d_preset",
        "command_auromatic_3d_strength",
        "command_auro_3d_mode",
        "command_dirac_filter",
        "command_eco_mode",
        "command_lfc",
        "command_containment_amount",
        "command_loudness_management",
        "command_bass_sync",
        "command_dialog_enhancer",
        "command_hdmi_output",
        "command_hdmi_audio_decode",
        "command_quick_select_mode",
        "command_quick_select_memory",
        "command_auto_standby",
        "command_sleep",
        "command_center_spread",
        "command_video_processing_mode",
        "command_room_size",
        "command_status",
        "command_system_reset",
        "command_network_restart",
        "command_trigger",
        "command_speaker_preset",
        "command_bluetooth_transmitter",
        "command_dialog_control",
        "command_speaker_virtualizer",
        "command_effect_speaker_selection",
        "command_drc",
        "command_delay_time",
        "command_audio_restorer",
        "command_remote_control_lock",
        "command_panel_lock",
        "command_panel_and_volume_lock",
        "command_graphic_eq",
        "command_headphone_eq",
    ],
)

# AVR-X search patterns
DEVICEINFO_AVR_X_PATTERN = re.compile(
    r"(.*AV(C|R)-(X|S|A).*|.*SR500[6-9]|.*SR60(07|08|09|10|11|12|13)|."
    r"*SR70(07|08|09|10|11|12|13)|.*SR501[3-4]|.*NR1604|.*NR1710)"
)

DEVICEINFO_COMMAPI_PATTERN = re.compile(r"(0210|0220|0250|0300|0301)")

# Receiver types
AVR_NAME = "avr"
AVR_X_NAME = "avr-x"
AVR_X_2016_NAME = "avr-x-2016"

AVR = ReceiverType(type=AVR_NAME, port=80)
AVR_X = ReceiverType(type=AVR_X_NAME, port=80)
AVR_X_2016 = ReceiverType(type=AVR_X_2016_NAME, port=8080)
VALID_RECEIVER_TYPES = (AVR, AVR_X, AVR_X_2016)

DESCRIPTION_TYPES = {
    AVR_NAME: DescriptionType(port=8080, url="/description.xml"),
    AVR_X_NAME: DescriptionType(port=8080, url="/description.xml"),
    AVR_X_2016_NAME: DescriptionType(
        port=60006, url="/upnp/desc/aios_device/aios_device.xml"
    ),
}

SOURCE_MAPPING = {
    "TV AUDIO": "TV",
    "iPod/USB": "USB/IPOD",
    "Bluetooth": "BT",
    "Blu-ray": "BD",
    "CBL/SAT": "SAT/CBL",
    "NETWORK": "NET",
    "Media Player": "MPLAY",
    "AUX": "AUX1",
    "Tuner": "TUNER",
    "FM": "TUNER",
    "SpotifyConnect": "Spotify Connect",
}

CHANGE_INPUT_MAPPING = {
    "Favorites": "FAVORITES",
    "Flickr": "FLICKR",
    "Internet Radio": "IRADIO",
    "Media Server": "SERVER",
    "Online Music": "NET",
    "Spotify": "SPOTIFY",
}

TELNET_SOURCES = {
    "CD",
    "PHONO",
    "TUNER",
    "DVD",
    "BD",
    "TV",
    "SAT/CBL",
    "MPLAY",
    "GAME",
    "HDRADIO",
    "NET",
    "PANDORA",
    "SIRIUSXM",
    "SOURCE",
    "LASTFM",
    "FLICKR",
    "IRADIO",
    "IRP",
    "SERVER",
    "FAVORITES",
    "AUX1",
    "AUX2",
    "AUX3",
    "AUX4",
    "AUX5",
    "AUX6",
    "AUX7",
    "BT",
    "USB/IPOD",
    "USB DIRECT",
    "IPOD DIRECT",
}

TELNET_MAPPING = {
    "FAVORITES": "Favorites",
    "FLICKR": "Flickr",
    "IRADIO": "Internet Radio",
    "IRP": "Internet Radio",
    "SERVER": "Media Server",
    "SPOTIFY": "Spotify",
}

# Sound modes
ALL_ZONE_STEREO = "ALL ZONE STEREO"

SOUND_MODE_MAPPING = {
    "MUSIC": [
        "DOLBY D +NEO:X M",
        "DOLBY PL2 M",
        "DOLBY PL2 MUSIC",
        "DOLBY PL2 X MUSIC",
        "DTS NEO:6 M",
        "DTS NEO:6 MUSIC",
        "DTS NEO:X M",
        "DTS NEO:X MUSIC",
        "PLII MUSIC",
        "PLIIX MUSIC",
    ],
    "MOVIE": [
        "DOLBY D +NEO:X C",
        "DOLBY PL2 C",
        "DOLBY PL2 CINEMA",
        "DOLBY PL2 MOVIE",
        "DOLBY PL2 X MOVIE",
        "DOLBY PLII MOVIE",
        "DTS NEO:6 C",
        "DTS NEO:6 CINEMA",
        "DTS NEO:X C",
        "DTS NEO:X CINEMA",
        "MULTI IN + VIRTUAL:X",
        "PLII CINEMA",
        "PLII MOVIE",
        "PLIIX CINEMA",
    ],
    "GAME": [
        "DOLBY D +NEO:X G",
        "DOLBY PL2 G",
        "DOLBY PL2 GAME",
        "DOLBY PL2 X GAME",
        "DOLBY PLII GAME",
        "PLII GAME",
    ],
    "AUTO": ["None"],
    "STANDARD": ["None2"],
    "VIRTUAL": ["VIRTUAL"],
    "MATRIX": ["MATRIX"],
    "ROCK ARENA": ["ROCK ARENA"],
    "JAZZ CLUB": ["JAZZ CLUB"],
    "VIDEO GAME": ["VIDEO GAME"],
    "MONO MOVIE": ["MONO MOVIE"],
    "DIRECT": ["DIRECT"],
    "PURE DIRECT": ["PURE_DIRECT", "PURE DIRECT"],
    "DOLBY DIGITAL": [
        "DOLBY ATMOS",
        "DOLBY AUDIO - DD + DSUR",
        "DOLBY AUDIO - DD + NEURAL:X",
        "DOLBY AUDIO - DD+   + DSUR",
        "DOLBY AUDIO - DD+   + NEURAL:X",
        "DOLBY AUDIO - DOLBY DIGITAL PLUS",
        "DOLBY AUDIO - DOLBY DIGITAL",
        "DOLBY AUDIO - DOLBY SURROUND",
        "DOLBY AUDIO - DOLBY TRUEHD",
        "DOLBY AUDIO - TRUEHD + DSUR",
        "DOLBY AUDIO - TRUEHD + NEURAL:X",
        "DOLBY AUDIO-DD",
        "DOLBY AUDIO-DD+ +DSUR",
        "DOLBY AUDIO-DD+ +NEURAL:X",
        "DOLBY AUDIO-DD+",
        "DOLBY AUDIO-DD+DSUR",
        "DOLBY AUDIO-DSUR",
        "DOLBY AUDIO-TRUEHD",
        "DOLBY AUDIO-TRUEHD+DSUR",
        "DOLBY AUDIO-TRUEHD+NEURAL:X",
        "DOLBY D + +DOLBY SURROUND",
        "DOLBY D + DOLBY SURROUND",
        "DOLBY D + NEURAL:X",
        "DOLBY D+ +DS",
        "DOLBY D+",
        "DOLBY D+DS",
        "DOLBY DIGITAL + + NEURAL:X",
        "DOLBY DIGITAL + NEURAL:X",
        "DOLBY DIGITAL +",
        "DOLBY DIGITAL",
        "DOLBY HD + DOLBY SURROUND",
        "DOLBY HD",
        "DOLBY PRO LOGIC",
        "DOLBY SURROUND",
        "DOLBY TRUEHD",
        "MULTI IN + DOLBY SURROUND",
        "MULTI IN + DSUR",
        "MULTI IN + NEURAL:X",
        "NEURAL",
        "STANDARD(DOLBY)",
        "DOLBY AUDIO-DD+NEURAL:X",
        "DOLBY AUDIO-DD+",
        # Added both variants as we don't know if type is intentional
        "DOLBY AUDIO-DD+ +NERUAL:X",
        "DOLBY AUDIO-DD+ +NEURAL:X",
    ],
    "DTS SURROUND": [
        "DTS + DOLBY SURROUND",
        "DTS + NEURAL:X",
        "DTS + VIRTUAL:X",
        "DTS NEURAL:X",
        "DTS SURROUND",
        "DTS VIRTUAL:X",
        "DTS-HD + DOLBY SURROUND",
        "DTS-HD + DSUR",
        "DTS-HD + NEURAL:X",
        "DTS-HD MSTR",
        "DTS-HD",
        "DTS:X MSTR",
        "DTS:X",
        "M CH IN+DSUR",
        "MULTI CH IN",
        "NEURAL:X",
        "STANDARD(DTS)",
        "VIRTUAL:X",
        "IMAX DTS",
        "IMAX DTS+NEURAL:X",
        "MAX DTS+VIRTUAL:X",
        "DTS+DSUR",
        "DTS+NEURAL:X",
        "DTS+VIRTUAL:X",
        "DTS HD",
        "DTS HD+DSUR",
        "DTS HD+NEURAL:X",
        "DTS HD+VIRTUAL:X",
        "DTS:X+VIRTUAL:X",
        "IMAX DTS:X",
        "IMAX DTS:X+VIRTUAL:X",
        "M CH IN+NEURAL:X",
        "M CH IN+VIRTUAL:X",
    ],
    "AURO3D": ["AURO-3D", "AURO3D"],
    "AURO2DSURR": ["AURO-2D SURROUND", "AURO2DSURR"],
    "MCH STEREO": [
        "MCH STEREO",
        "MULTI CH IN 7.1",
        "MULTI CH STEREO",
        "MULTI_CH_STEREO",
    ],
    "STEREO": ["STEREO"],
    ALL_ZONE_STEREO: ["ALL ZONE STEREO"],
}

# Receiver sources
NETAUDIO_SOURCES = {
    "AirPlay",
    "Online Music",
    "Media Server",
    "iPod/USB",
    "Bluetooth",
    "Internet Radio",
    "Favorites",
    "SpotifyConnect",
    "Flickr",
    "NET/USB",
    "Music Server",
    "NETWORK",
    "NET",
}
TUNER_SOURCES = {"Tuner", "TUNER"}
HDTUNER_SOURCES = {"HD Radio", "HDRADIO"}
PLAYING_SOURCES = set().union(*[NETAUDIO_SOURCES, TUNER_SOURCES, HDTUNER_SOURCES])

# Image URLs
STATIC_ALBUM_URL = "http://{host}:{port}/img/album%20art_S.png"
ALBUM_COVERS_URL = "http://{host}:{port}/NetAudio/art.asp-jpg?{hash}"

# General URLs
APPCOMMAND_URL = "/goform/AppCommand.xml"
APPCOMMAND0300_URL = "/goform/AppCommand0300.xml"
DEVICEINFO_URL = "/goform/Deviceinfo.xml"
NETAUDIOSTATUS_URL = "/goform/formNetAudio_StatusXml.xml"
TUNERSTATUS_URL = "/goform/formTuner_TunerXml.xml"
HDTUNERSTATUS_URL = "/goform/formTuner_HdXml.xml"
COMMAND_NETAUDIO_POST_URL = "/NetAudio/index.put.asp"
COMMAND_PAUSE = "/goform/formiPhoneAppDirect.xml?NS9B"
COMMAND_PLAY = "/goform/formiPhoneAppDirect.xml?NS9A"
COMMAND_ECO_MODE = "/goform/formiPhoneAppDirect.xml?ECO{mode}"


# Main Zone URLs
STATUS_URL = "/goform/formMainZone_MainZoneXmlStatus.xml"
MAINZONE_URL = "/goform/formMainZone_MainZoneXml.xml"
COMMAND_SEL_SRC_URL = "/goform/formiPhoneAppDirect.xml?SI"
COMMAND_FAV_SRC_URL = "/goform/formiPhoneAppDirect.xml?ZM"
COMMAND_POWER_ON_URL = "/goform/formiPhoneAppPower.xml?1+PowerOn"
COMMAND_POWER_STANDBY_URL = "/goform/formiPhoneAppPower.xml?1+PowerStandby"
COMMAND_VOLUME_UP_URL = "/goform/formiPhoneAppDirect.xml?MVUP"
COMMAND_VOLUME_DOWN_URL = "/goform/formiPhoneAppDirect.xml?MVDOWN"
COMMAND_SET_VOLUME_URL = "/goform/formiPhoneAppVolume.xml?1+{volume:.1f}"
COMMAND_MUTE_ON_URL = "/goform/formiPhoneAppMute.xml?1+MuteOn"
COMMAND_MUTE_OFF_URL = "/goform/formiPhoneAppMute.xml?1+MuteOff"
COMMAND_SEL_SM_URL = "/goform/formiPhoneAppDirect.xml?MS"
COMMAND_SET_ZST_URL = "/goform/formiPhoneAppDirect.xml?MN"
COMMAND_NEURAL_X_ON_OFF = "/goform/formiPhoneAppDirect.xml?PSNEURAL%20{mode}"
COMMAND_IMAX_AUTO_OFF = "/goform/formiPhoneAppDirect.xml?PSIMAX%20{mode}"
COMMAND_IMAX_AUDIO_SETTINGS = "/goform/formiPhoneAppDirect.xml?PSIMAXAUD%20{mode}"
COMMAND_IMAX_HPF = "/goform/formiPhoneAppDirect.xml?PSIMAXHPF%20{frequency}"
COMMAND_IMAX_LPF = "/goform/formiPhoneAppDirect.xml?PSIMAXLPF%20{frequency}"
COMMAND_IMAX_SUBWOOFER_MODE = "/goform/formiPhoneAppDirect.xml?PSIMAXSWM%20{mode}"
COMMAND_IMAX_SUBWOOFER_OUTPUT = "/goform/formiPhoneAppDirect.xml?PSIMAXSWO%20{mode}"
COMMAND_CINEMA_EQ = "/goform/formiPhoneAppDirect.xml?PSCINEMA%20EQ.{mode}"
COMMAND_CURSOR_UP = "/goform/formiPhoneAppDirect.xml?MNCUP"
COMMAND_CURSOR_DOWN = "/goform/formiPhoneAppDirect.xml?MNCDN"
COMMAND_CURSOR_LEFT = "/goform/formiPhoneAppDirect.xml?MNCLT"
COMMAND_CURSOR_RIGHT = "/goform/formiPhoneAppDirect.xml?MNCRT"
COMMAND_CURSOR_ENTER = "/goform/formiPhoneAppDirect.xml?MNENT"
COMMAND_BACK = "/goform/formiPhoneAppDirect.xml?MNRTN"
COMMAND_INFO = "/goform/formiPhoneAppDirect.xml?MNINF"
COMMAND_OPTIONS = "/goform/formiPhoneAppDirect.xml?MNOPT"
COMMAND_SETUP_OPEN = "/goform/formiPhoneAppDirect.xml?MNMEN%20ON"
COMMAND_SETUP_CLOSE = "/goform/formiPhoneAppDirect.xml?MNMEN%20OFF"
COMMAND_SETUP_QUERY = "/goform/formiPhoneAppDirect.xml?MNMEN?"
COMMAND_CHANNEL_LEVEL_ADJUST = "/goform/formiPhoneAppDirect.xml?MNCHL"
COMMAND_DIMMER_TOGGLE = "/goform/formiPhoneAppDirect.xml?DIM%20SEL"
COMMAND_DIMMER_SET = "/goform/formiPhoneAppDirect.xml?DIM%20{mode}"
COMMAND_CHANNEL_VOLUME = "/goform/formiPhoneAppDirect.xml?CV{channel}%20{value}"
COMMAND_CHANNEL_VOLUMES_RESET = "/goform/formiPhoneAppDirect.xml?CVZRL"
COMMAND_SUBWOOFER_ON_OFF = "/goform/formiPhoneAppDirect.xml?PSSWR%20{mode}"
COMMAND_SUBWOOFER_LEVEL = "/goform/formiPhoneAppDirect.xml?PSSWL{number}%20{mode}"
COMMAND_LFE = "/goform/formiPhoneAppDirect.xml?PSLFE%20{mode}"
COMMAND_TACTILE_TRANSDUCER = "/goform/formiPhoneAppDirect.xml?SSTTR%20{mode}"
COMMAND_TACTILE_TRANSDUCER_LEVEL = "/goform/formiPhoneAppDirect.xml?SSTTRLEV%20{mode}"
COMMAND_TACTILE_TRANSDUCER_LPF = (
    "/goform/formiPhoneAppDirect.xml?SSTTRLPF%20{frequency}"
)
COMMAND_DELAY_UP = "/goform/formiPhoneAppDirect.xml?PSDELAY%20UP"
COMMAND_DELAY_DOWN = "/goform/formiPhoneAppDirect.xml?PSDELAY%20DOWN"
COMMAND_AUROMATIC_3D_PRESET = "/goform/formiPhoneAppDirect.xml?PSAUROPR%20{preset}"
COMMAND_AUROMATIC_3D_STRENGTH = "/goform/formiPhoneAppDirect.xml?PSAUROST%20{value}"
COMMAND_AURO_3D_MODE = "/goform/formiPhoneAppDirect.xml?PSAUROMODEM%20{mode}"
COMMAND_DIRAC_FILTER = "/goform/formiPhoneAppDirect.xml?PSDIRAC%20{filter}"
COMMAND_LFC = "/goform/formiPhoneAppDirect.xml?PSLFC%20{mode}"
COMMAND_CONTAMINATION_AMOUNT = "/goform/formiPhoneAppDirect.xml?PSCNTAMT%20{value}"
COMMAND_LOUDNESS_MANAGEMENT = "/goform/formiPhoneAppDirect.xml?PSLOM%20{mode}"
COMMAND_BASS_SYNC = "/goform/formiPhoneAppDirect.xml?PSBSC%20{mode}"
COMMAND_DIALOG_ENHANCER = "/goform/formiPhoneAppDirect.xml?PSDEH%20{level}"
COMMAND_HDMI_OUTPUT = "/goform/formiPhoneAppDirect.xml?VSMONI{output}"
COMMAND_HDMI_AUDIO_DECODE = "/goform/formiPhoneAppDirect.xml?VSAUDIO%20{mode}"
COMMAND_QUICK_SELECT_MODE = "/goform/formiPhoneAppDirect.xml?MSQUICK{number}"
COMMAND_QUICK_SELECT_MEMORY = "/goform/formiPhoneAppDirect.xml?MSQUICK{number}"
COMMAND_AUTO_STANDBY = "/goform/formiPhoneAppDirect.xml?STBY{mode}"
COMMAND_SLEEP = "/goform/formiPhoneAppDirect.xml?SLP{value}"
COMMAND_CENTER_SPREAD = "/goform/formiPhoneAppDirect.xml?PSCES%20{mode}"
COMMAND_VIDEO_PROCESSING_MODE = "/goform/formiPhoneAppDirect.xml?VSVPM{mode}"
COMMAND_ROOM_SIZE = "/goform/formiPhoneAppDirect.xml?PSRSZ%20{size}"
COMMAND_STATUS = "/goform/formiPhoneAppDirect.xml?RCSHP0230030"
COMMAND_SYSTEM_RESET = "/goform/formiPhoneAppDirect.xml?SYRST"
COMMAND_NETWORK_RESTART = "/goform/formiPhoneAppDirect.xml?NSRBT"
COMMAND_TRIGGER = "/goform/formiPhoneAppDirect.xml?TR{number}%20{mode}"
COMMAND_SPEAKER_PRESET = "/goform/formiPhoneAppDirect.xml?SPPR%20{number}"
COMMAND_BLUETOOTH_TRANSMITTER = "/goform/formiPhoneAppDirect.xml?BTTX%20{mode}"
COMMAND_DIALOG_CONTROL = "/goform/formiPhoneAppDirect.xml?PSDIC%20{value}"
COMMAND_SPEAKER_VIRTUALIZER = "/goform/formiPhoneAppDirect.xml?PSSPV%20{mode}"
COMMAND_EFFECT_SPEAKER_SELECTION = "/goform/formiPhoneAppDirect.xml?PSSP:{mode}"
COMMAND_DRC = "/goform/formiPhoneAppDirect.xml?PSDRC%20{mode}"
COMMAND_DELAY_TIME = "/goform/formiPhoneAppDirect.xml?PSDEL%20{value}"
COMMAND_AUDIO_RESTORER = "/goform/formiPhoneAppDirect.xml?PSRSTR%20{mode}"
COMMAND_REMOTE_CONTROL_LOCK = "/goform/formiPhoneAppDirect.xml?SYREMOTE%20LOCK%20{mode}"
COMMAND_PANEL_LOCK = "/goform/formiPhoneAppDirect.xml?SYPANEL%20LOCK%20{mode}"
COMMAND_PANEL_AND_VOLUME_LOCK = "/goform/formiPhoneAppDirect.xml?SYPANEL+V%20LOCK%20ON"
COMMAND_GRAPHIC_EQ = "/goform/formiPhoneAppDirect.xml?PSGEQ%20{mode}"
COMMAND_HEADPHONE_EQ = "/goform/formiPhoneAppDirect.xml?PSHEQ%20{mode}"

# Zone 2 URLs
STATUS_Z2_URL = "/goform/formZone2_Zone2XmlStatus.xml"
COMMAND_SEL_SRC_Z2_URL = "/goform/formiPhoneAppDirect.xml?Z2"
COMMAND_FAV_SRC_Z2_URL = "/goform/formiPhoneAppDirect.xml?Z2"
COMMAND_POWER_ON_Z2_URL = "/goform/formiPhoneAppPower.xml?2+PowerOn"
COMMAND_POWER_STANDBY_Z2_URL = "/goform/formiPhoneAppPower.xml?2+PowerStandby"
COMMAND_VOLUME_UP_Z2_URL = "/goform/formiPhoneAppDirect.xml?Z2UP"
COMMAND_VOLUME_DOWN_Z2_URL = "/goform/formiPhoneAppDirect.xml?Z2DOWN"
COMMAND_SET_VOLUME_Z2_URL = "/goform/formiPhoneAppVolume.xml?2+{volume:.1f}"
COMMAND_MUTE_ON_Z2_URL = "/goform/formiPhoneAppMute.xml?2+MuteOn"
COMMAND_MUTE_OFF_Z2_URL = "/goform/formiPhoneAppMute.xml?2+MuteOff"

# Zone 3 URLs
STATUS_Z3_URL = "/goform/formZone3_Zone3XmlStatus.xml"
COMMAND_SEL_SRC_Z3_URL = "/goform/formiPhoneAppDirect.xml?Z3"
COMMAND_FAV_SRC_Z3_URL = "/goform/formiPhoneAppDirect.xml?Z3"
COMMAND_POWER_ON_Z3_URL = "/goform/formiPhoneAppPower.xml?3+PowerOn"
COMMAND_POWER_STANDBY_Z3_URL = "/goform/formiPhoneAppPower.xml?3+PowerStandby"
COMMAND_VOLUME_UP_Z3_URL = "/goform/formiPhoneAppDirect.xml?Z3UP"
COMMAND_VOLUME_DOWN_Z3_URL = "/goform/formiPhoneAppDirect.xml?Z3DOWN"
COMMAND_SET_VOLUME_Z3_URL = "/goform/formiPhoneAppVolume.xml?3+{volume:.1f}"
COMMAND_MUTE_ON_Z3_URL = "/goform/formiPhoneAppMute.xml?3+MuteOn"
COMMAND_MUTE_OFF_Z3_URL = "/goform/formiPhoneAppMute.xml?3+MuteOff"

DENONAVR_URLS = ReceiverURLs(
    appcommand=APPCOMMAND_URL,
    appcommand0300=APPCOMMAND0300_URL,
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
    command_neural_x_on_off=COMMAND_NEURAL_X_ON_OFF,
    command_imax_auto_off=COMMAND_IMAX_AUTO_OFF,
    command_imax_audio_settings=COMMAND_IMAX_AUTO_OFF,
    command_imax_hpf=COMMAND_IMAX_HPF,
    command_imax_lpf=COMMAND_IMAX_LPF,
    command_imax_subwoofer_mode=COMMAND_IMAX_SUBWOOFER_MODE,
    command_imax_subwoofer_output=COMMAND_IMAX_SUBWOOFER_OUTPUT,
    command_cinema_eq=COMMAND_CINEMA_EQ,
    command_netaudio_post=COMMAND_NETAUDIO_POST_URL,
    command_set_all_zone_stereo=COMMAND_SET_ZST_URL,
    command_pause=COMMAND_PAUSE,
    command_play=COMMAND_PLAY,
    command_cusor_up=COMMAND_CURSOR_UP,
    command_cusor_down=COMMAND_CURSOR_DOWN,
    command_cusor_left=COMMAND_CURSOR_LEFT,
    command_cusor_right=COMMAND_CURSOR_RIGHT,
    command_cusor_enter=COMMAND_CURSOR_ENTER,
    command_back=COMMAND_BACK,
    command_info=COMMAND_INFO,
    command_options=COMMAND_OPTIONS,
    command_setup_open=COMMAND_SETUP_OPEN,
    command_setup_close=COMMAND_SETUP_CLOSE,
    command_setup_query=COMMAND_SETUP_QUERY,
    command_channel_level_adjust=COMMAND_CHANNEL_LEVEL_ADJUST,
    command_dimmer_toggle=COMMAND_DIMMER_TOGGLE,
    command_dimmer_set=COMMAND_DIMMER_SET,
    command_channel_volume=COMMAND_CHANNEL_VOLUME,
    command_channel_volumes_reset=COMMAND_CHANNEL_VOLUMES_RESET,
    command_subwoofer_on_off=COMMAND_SUBWOOFER_ON_OFF,
    command_subwoofer_level=COMMAND_SUBWOOFER_LEVEL,
    command_lfe=COMMAND_LFE,
    command_tactile_transducer=COMMAND_TACTILE_TRANSDUCER,
    command_tactile_transducer_level=COMMAND_TACTILE_TRANSDUCER_LEVEL,
    command_tactile_transducer_lpf=COMMAND_TACTILE_TRANSDUCER_LPF,
    command_delay_up=COMMAND_DELAY_UP,
    command_delay_down=COMMAND_DELAY_DOWN,
    command_auromatic_3d_preset=COMMAND_AUROMATIC_3D_PRESET,
    command_auromatic_3d_strength=COMMAND_AUROMATIC_3D_STRENGTH,
    command_auro_3d_mode=COMMAND_AURO_3D_MODE,
    command_dirac_filter=COMMAND_DIRAC_FILTER,
    command_eco_mode=COMMAND_ECO_MODE,
    command_lfc=COMMAND_LFC,
    command_containment_amount=COMMAND_CONTAMINATION_AMOUNT,
    command_loudness_management=COMMAND_LOUDNESS_MANAGEMENT,
    command_bass_sync=COMMAND_BASS_SYNC,
    command_dialog_enhancer=COMMAND_DIALOG_ENHANCER,
    command_hdmi_output=COMMAND_HDMI_OUTPUT,
    command_hdmi_audio_decode=COMMAND_HDMI_AUDIO_DECODE,
    command_quick_select_mode=COMMAND_QUICK_SELECT_MODE,
    command_quick_select_memory=COMMAND_QUICK_SELECT_MODE,
    command_auto_standby=COMMAND_AUTO_STANDBY,
    command_sleep=COMMAND_SLEEP,
    command_center_spread=COMMAND_CENTER_SPREAD,
    command_video_processing_mode=COMMAND_VIDEO_PROCESSING_MODE,
    command_room_size=COMMAND_ROOM_SIZE,
    command_status=COMMAND_STATUS,
    command_system_reset=COMMAND_SYSTEM_RESET,
    command_network_restart=COMMAND_NETWORK_RESTART,
    command_trigger=COMMAND_TRIGGER,
    command_speaker_preset=COMMAND_SPEAKER_PRESET,
    command_bluetooth_transmitter=COMMAND_BLUETOOTH_TRANSMITTER,
    command_dialog_control=COMMAND_DIALOG_CONTROL,
    command_speaker_virtualizer=COMMAND_SPEAKER_VIRTUALIZER,
    command_effect_speaker_selection=COMMAND_EFFECT_SPEAKER_SELECTION,
    command_drc=COMMAND_DRC,
    command_delay_time=COMMAND_DELAY_TIME,
    command_audio_restorer=COMMAND_AUDIO_RESTORER,
    command_remote_control_lock=COMMAND_REMOTE_CONTROL_LOCK,
    command_panel_lock=COMMAND_PANEL_LOCK,
    command_panel_and_volume_lock=COMMAND_PANEL_AND_VOLUME_LOCK,
    command_graphic_eq=COMMAND_GRAPHIC_EQ,
    command_headphone_eq=COMMAND_HEADPHONE_EQ,
)

ZONE2_URLS = ReceiverURLs(
    appcommand=APPCOMMAND_URL,
    appcommand0300=APPCOMMAND0300_URL,
    status=STATUS_Z2_URL,
    mainzone=MAINZONE_URL,
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
    command_neural_x_on_off=COMMAND_NEURAL_X_ON_OFF,
    command_imax_auto_off=COMMAND_IMAX_AUTO_OFF,
    command_imax_audio_settings=COMMAND_IMAX_AUDIO_SETTINGS,
    command_imax_hpf=COMMAND_IMAX_HPF,
    command_imax_lpf=COMMAND_IMAX_LPF,
    command_imax_subwoofer_mode=COMMAND_IMAX_SUBWOOFER_MODE,
    command_imax_subwoofer_output=COMMAND_IMAX_SUBWOOFER_OUTPUT,
    command_cinema_eq=COMMAND_CINEMA_EQ,
    command_netaudio_post=COMMAND_NETAUDIO_POST_URL,
    command_set_all_zone_stereo=COMMAND_SET_ZST_URL,
    command_pause=COMMAND_PAUSE,
    command_play=COMMAND_PLAY,
    command_cusor_up=COMMAND_CURSOR_UP,
    command_cusor_down=COMMAND_CURSOR_DOWN,
    command_cusor_left=COMMAND_CURSOR_LEFT,
    command_cusor_right=COMMAND_CURSOR_RIGHT,
    command_cusor_enter=COMMAND_CURSOR_ENTER,
    command_back=COMMAND_BACK,
    command_info=COMMAND_INFO,
    command_options=COMMAND_OPTIONS,
    command_setup_open=COMMAND_SETUP_OPEN,
    command_setup_close=COMMAND_SETUP_CLOSE,
    command_setup_query=COMMAND_SETUP_QUERY,
    command_channel_level_adjust=COMMAND_CHANNEL_LEVEL_ADJUST,
    command_dimmer_toggle=COMMAND_DIMMER_TOGGLE,
    command_dimmer_set=COMMAND_DIMMER_SET,
    command_channel_volume=COMMAND_CHANNEL_VOLUME,
    command_channel_volumes_reset=COMMAND_CHANNEL_VOLUMES_RESET,
    command_subwoofer_on_off=COMMAND_SUBWOOFER_ON_OFF,
    command_subwoofer_level=COMMAND_SUBWOOFER_LEVEL,
    command_lfe=COMMAND_LFE,
    command_tactile_transducer=COMMAND_TACTILE_TRANSDUCER,
    command_tactile_transducer_level=COMMAND_TACTILE_TRANSDUCER_LEVEL,
    command_tactile_transducer_lpf=COMMAND_TACTILE_TRANSDUCER_LPF,
    command_delay_up=COMMAND_DELAY_UP,
    command_delay_down=COMMAND_DELAY_DOWN,
    command_auromatic_3d_preset=COMMAND_AUROMATIC_3D_PRESET,
    command_auromatic_3d_strength=COMMAND_AUROMATIC_3D_STRENGTH,
    command_auro_3d_mode=COMMAND_AURO_3D_MODE,
    command_dirac_filter=COMMAND_DIRAC_FILTER,
    command_eco_mode=COMMAND_ECO_MODE,
    command_lfc=COMMAND_LFC,
    command_containment_amount=COMMAND_CONTAMINATION_AMOUNT,
    command_loudness_management=COMMAND_LOUDNESS_MANAGEMENT,
    command_bass_sync=COMMAND_BASS_SYNC,
    command_dialog_enhancer=COMMAND_DIALOG_ENHANCER,
    command_hdmi_output=COMMAND_HDMI_OUTPUT,
    command_hdmi_audio_decode=COMMAND_HDMI_AUDIO_DECODE,
    command_quick_select_mode=COMMAND_QUICK_SELECT_MODE,
    command_quick_select_memory=COMMAND_QUICK_SELECT_MEMORY,
    command_auto_standby=COMMAND_AUTO_STANDBY,
    command_sleep=COMMAND_SLEEP,
    command_center_spread=COMMAND_CENTER_SPREAD,
    command_video_processing_mode=COMMAND_VIDEO_PROCESSING_MODE,
    command_room_size=COMMAND_ROOM_SIZE,
    command_status=COMMAND_STATUS,
    command_system_reset=COMMAND_SYSTEM_RESET,
    command_network_restart=COMMAND_NETWORK_RESTART,
    command_trigger=COMMAND_TRIGGER,
    command_speaker_preset=COMMAND_SPEAKER_PRESET,
    command_bluetooth_transmitter=COMMAND_BLUETOOTH_TRANSMITTER,
    command_dialog_control=COMMAND_DIALOG_CONTROL,
    command_speaker_virtualizer=COMMAND_SPEAKER_VIRTUALIZER,
    command_effect_speaker_selection=COMMAND_EFFECT_SPEAKER_SELECTION,
    command_drc=COMMAND_DRC,
    command_delay_time=COMMAND_DELAY_TIME,
    command_audio_restorer=COMMAND_AUDIO_RESTORER,
    command_remote_control_lock=COMMAND_REMOTE_CONTROL_LOCK,
    command_panel_lock=COMMAND_PANEL_LOCK,
    command_panel_and_volume_lock=COMMAND_PANEL_AND_VOLUME_LOCK,
    command_graphic_eq=COMMAND_GRAPHIC_EQ,
    command_headphone_eq=COMMAND_HEADPHONE_EQ,
)

ZONE3_URLS = ReceiverURLs(
    appcommand=APPCOMMAND_URL,
    appcommand0300=APPCOMMAND0300_URL,
    status=STATUS_Z3_URL,
    mainzone=MAINZONE_URL,
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
    command_neural_x_on_off=COMMAND_NEURAL_X_ON_OFF,
    command_imax_auto_off=COMMAND_IMAX_AUTO_OFF,
    command_imax_audio_settings=COMMAND_IMAX_AUDIO_SETTINGS,
    command_imax_hpf=COMMAND_IMAX_HPF,
    command_imax_lpf=COMMAND_IMAX_LPF,
    command_imax_subwoofer_mode=COMMAND_IMAX_SUBWOOFER_MODE,
    command_imax_subwoofer_output=COMMAND_IMAX_SUBWOOFER_OUTPUT,
    command_cinema_eq=COMMAND_CINEMA_EQ,
    command_netaudio_post=COMMAND_NETAUDIO_POST_URL,
    command_set_all_zone_stereo=COMMAND_SET_ZST_URL,
    command_pause=COMMAND_PAUSE,
    command_play=COMMAND_PLAY,
    command_cusor_up=COMMAND_CURSOR_UP,
    command_cusor_down=COMMAND_CURSOR_DOWN,
    command_cusor_left=COMMAND_CURSOR_LEFT,
    command_cusor_right=COMMAND_CURSOR_RIGHT,
    command_cusor_enter=COMMAND_CURSOR_ENTER,
    command_back=COMMAND_BACK,
    command_info=COMMAND_INFO,
    command_options=COMMAND_OPTIONS,
    command_setup_open=COMMAND_SETUP_OPEN,
    command_setup_close=COMMAND_SETUP_CLOSE,
    command_setup_query=COMMAND_SETUP_QUERY,
    command_channel_level_adjust=COMMAND_CHANNEL_LEVEL_ADJUST,
    command_dimmer_toggle=COMMAND_DIMMER_TOGGLE,
    command_dimmer_set=COMMAND_DIMMER_SET,
    command_channel_volume=COMMAND_CHANNEL_VOLUME,
    command_channel_volumes_reset=COMMAND_CHANNEL_VOLUMES_RESET,
    command_subwoofer_on_off=COMMAND_SUBWOOFER_ON_OFF,
    command_subwoofer_level=COMMAND_SUBWOOFER_LEVEL,
    command_lfe=COMMAND_LFE,
    command_tactile_transducer=COMMAND_TACTILE_TRANSDUCER,
    command_tactile_transducer_level=COMMAND_TACTILE_TRANSDUCER_LEVEL,
    command_tactile_transducer_lpf=COMMAND_TACTILE_TRANSDUCER_LPF,
    command_delay_up=COMMAND_DELAY_UP,
    command_delay_down=COMMAND_DELAY_DOWN,
    command_auromatic_3d_preset=COMMAND_AUROMATIC_3D_PRESET,
    command_auromatic_3d_strength=COMMAND_AUROMATIC_3D_STRENGTH,
    command_auro_3d_mode=COMMAND_AURO_3D_MODE,
    command_dirac_filter=COMMAND_DIRAC_FILTER,
    command_eco_mode=COMMAND_ECO_MODE,
    command_lfc=COMMAND_LFC,
    command_containment_amount=COMMAND_CONTAMINATION_AMOUNT,
    command_loudness_management=COMMAND_LOUDNESS_MANAGEMENT,
    command_bass_sync=COMMAND_BASS_SYNC,
    command_dialog_enhancer=COMMAND_DIALOG_ENHANCER,
    command_hdmi_output=COMMAND_HDMI_OUTPUT,
    command_hdmi_audio_decode=COMMAND_HDMI_AUDIO_DECODE,
    command_quick_select_mode=COMMAND_QUICK_SELECT_MODE,
    command_quick_select_memory=COMMAND_QUICK_SELECT_MEMORY,
    command_auto_standby=COMMAND_AUTO_STANDBY,
    command_sleep=COMMAND_SLEEP,
    command_center_spread=COMMAND_CENTER_SPREAD,
    command_video_processing_mode=COMMAND_VIDEO_PROCESSING_MODE,
    command_room_size=COMMAND_ROOM_SIZE,
    command_status=COMMAND_STATUS,
    command_system_reset=COMMAND_SYSTEM_RESET,
    command_network_restart=COMMAND_NETWORK_RESTART,
    command_trigger=COMMAND_TRIGGER,
    command_speaker_preset=COMMAND_SPEAKER_PRESET,
    command_bluetooth_transmitter=COMMAND_BLUETOOTH_TRANSMITTER,
    command_dialog_control=COMMAND_DIALOG_CONTROL,
    command_speaker_virtualizer=COMMAND_SPEAKER_VIRTUALIZER,
    command_effect_speaker_selection=COMMAND_EFFECT_SPEAKER_SELECTION,
    command_drc=COMMAND_DRC,
    command_delay_time=COMMAND_DELAY_TIME,
    command_audio_restorer=COMMAND_AUDIO_RESTORER,
    command_remote_control_lock=COMMAND_REMOTE_CONTROL_LOCK,
    command_panel_lock=COMMAND_PANEL_LOCK,
    command_panel_and_volume_lock=COMMAND_PANEL_AND_VOLUME_LOCK,
    command_graphic_eq=COMMAND_GRAPHIC_EQ,
    command_headphone_eq=COMMAND_HEADPHONE_EQ,
)

# Telnet Events
ALL_TELNET_EVENTS = "ALL"
TELNET_EVENTS = {
    "BT",
    "CV",
    "DC",
    "DIM",
    "ECO",
    "HD",
    "MN",
    "MS",
    "MU",
    "MV",
    "NS",
    "NSA",
    "NSE",
    "OP",
    "PS",
    "PV",
    "PW",
    "RM",
    "SD",
    "SI",
    "SLP",
    "SP",
    "SR",
    "SS",
    "STBY",
    "SV",
    "SY",
    "TF",
    "TM",
    "TP",
    "TR",
    "UG",
    "VS",
    "ZM",
    "Z2",
    "Z3",
}
ALL_ZONE_TELNET_EVENTS = {
    "DIM",
    "HD",
    "NS",
    "NSA",
    "NSE",
    "MN",
    "PW",
    "RM",
    "SY",
    "TF",
    "TM",
    "TP",
    "TR",
    "UG",
}

DENONAVR_TELNET_COMMANDS = TelnetCommands(
    command_sel_src="SI",
    command_fav_src="ZM",
    command_power_on="ZMON",
    command_power_standby="ZMOFF",
    command_volume_up="MVUP",
    command_volume_down="MVDOWN",
    command_set_volume="MV{volume:02d}",
    command_mute_on="MUON",
    command_mute_off="MUOFF",
    command_sel_sound_mode="MS",
    command_neural_x_on_off="PSNEURAL {mode}",
    command_imax_auto_off="PSIMAX {mode}",
    command_imax_audio_settings="PSIMAXAUD {mode}",
    command_imax_hpf="PSIMAXHPF {frequency}",
    command_imax_lpf="PSIMAXLPF {frequency}",
    command_imax_subwoofer_mode="PSIMAXSWM {mode}",
    command_imax_subwoofer_output="PSIMAXSWO {mode}",
    command_cinema_eq="PSCINEMA EQ.{mode}",
    command_set_all_zone_stereo="MN",
    command_pause="NS9B",
    command_play="NS9A",
    command_multieq="PSMULTEQ:",
    command_dynamiceq="PSDYNEQ ",
    command_reflevoffset="PSREFLEV ",
    command_dynamicvol="PSDYNVOL ",
    command_tonecontrol="PSTONE CTRL ",
    command_bass="PSBAS ",
    command_treble="PSTRE ",
    command_cusor_up="MNCUP",
    command_cusor_down="MNCDN",
    command_cusor_left="MNCLT",
    command_cusor_right="MNCRT",
    command_cusor_enter="MNENT",
    command_back="MNRTN",
    command_info="MNINF",
    command_options="MNOPT",
    command_setup_open="MNMEN ON",
    command_setup_close="MNMEN OFF",
    command_setup_query="MNMEN?",
    command_channel_level_adjust="MNCHL",
    command_dimmer_toggle="DIM SEL",
    command_dimmer_set="DIM {mode}",
    command_channel_volume="CV{channel} {value}",
    command_channel_volumes_reset="CVZRL",
    command_subwoofer_on_off="PSSWR {mode}",
    command_subwoofer_level="PSSWL{number} {mode}",
    command_lfe="PSLFE {mode}",
    command_tactile_transducer="SSTTR {mode}",
    command_tactile_transducer_level="SSTTRLEV {mode}",
    command_tactile_transducer_lpf="SSTTRLPF {frequency}",
    command_delay_up="PSDELAY UP",
    command_delay_down="PSDELAY DOWN",
    command_auromatic_3d_preset="PSAUROPR {preset}",
    command_auromatic_3d_strength="PSAUROST {value}",
    command_auro_3d_mode="PSAUROMODE {mode}",
    command_dirac_filter="PSDIRAC {filter}",
    command_eco_mode="ECO{mode}",
    command_lfc="PSLFC {mode}",
    command_containment_amount="PSCNTAMT {value}",
    command_loudness_management="PSLOM {mode}",
    command_bass_sync="PSBSC {mode}",
    command_dialog_enhancer="PSDEH {level}",
    command_hdmi_output="VSMONI{output}",
    command_hdmi_audio_decode="VSAUDIO {mode}",
    command_quick_select_mode="MSQUICK{number}",
    command_quick_select_memory="MSQUICK{number} MEMORY",
    command_auto_standby="STBY{mode}",
    command_sleep="SLP{value}",
    command_center_spread="PSCES {mode}",
    command_video_processing_mode="VSVPM{mode}",
    command_room_size="PSRSZ {size}",
    command_status="RCSHP0230030",
    command_system_reset="SYRST",
    command_network_restart="NSRBT",
    command_trigger="TR{number} {mode}",
    command_speaker_preset="SPPR {number}",
    command_bluetooth_transmitter="BTTX {mode}",
    command_dialog_control="PSDIC {value}",
    command_speaker_virtualizer="PSSPV {mode}",
    command_effect_speaker_selection="PSSP:{mode}",
    command_drc="PSDRC {mode}",
    command_delay_time="PSDEL {value}",
    command_audio_restorer="PSRSTR {mode}",
    command_remote_control_lock="SYREMOTE LOCK {mode}",
    command_panel_lock="SYPANEL LOCK {mode}",
    command_panel_and_volume_lock="SYPANEL+V LOCK ON",
    command_graphic_eq="PSGEQ {mode}",
    command_headphone_eq="PSHEQ {mode}",
)

ZONE2_TELNET_COMMANDS = TelnetCommands(
    command_sel_src="Z2",
    command_fav_src="Z2",
    command_power_on="Z2ON",
    command_power_standby="Z2OFF",
    command_volume_up="Z2UP",
    command_volume_down="Z2DOWN",
    command_set_volume="Z2{volume:02d}",
    command_mute_on="Z2MUON",
    command_mute_off="Z2MUOFF",
    command_sel_sound_mode="MS",
    command_neural_x_on_off="PSNEURAL {mode}",
    command_imax_auto_off="PSIMAX {mode}",
    command_imax_audio_settings="PSIMAXAUD {mode}",
    command_imax_hpf="PSIMAXHPF {frequency}",
    command_imax_lpf="PSIMAXLPF {frequency}",
    command_imax_subwoofer_mode="PSIMAXSWM {mode}",
    command_imax_subwoofer_output="PSIMAXSWO {mode}",
    command_cinema_eq="PSCINEMA EQ.{mode}",
    command_set_all_zone_stereo="MN",
    command_pause="NS9B",
    command_play="NS9A",
    command_multieq="PSMULTEQ:",
    command_dynamiceq="PSDYNEQ ",
    command_reflevoffset="PSREFLEV ",
    command_dynamicvol="PSDYNVOL ",
    command_tonecontrol="PSTONE CTRL ",
    command_bass="PSBAS ",
    command_treble="PSTRE ",
    command_cusor_up="MNCUP",
    command_cusor_down="MNCDN",
    command_cusor_left="MNCLT",
    command_cusor_right="MNCRT",
    command_cusor_enter="MNENT",
    command_back="MNRTN",
    command_info="MNINF",
    command_options="MNOPT",
    command_setup_open="MNMEN ON",
    command_setup_close="MNMEN OFF",
    command_setup_query="MNMEN?",
    command_channel_level_adjust="MNCHL",
    command_dimmer_toggle="DIM SEL",
    command_dimmer_set="DIM {mode}",
    command_channel_volume="CV{channel} {value}",
    command_channel_volumes_reset="CVZRL",
    command_subwoofer_on_off="PSSWR {mode}",
    command_subwoofer_level="PSSWL{number} {mode}",
    command_lfe="PSLFE {mode}",
    command_tactile_transducer="SSTTR {mode}",
    command_tactile_transducer_level="SSTTRLEV {mode}",
    command_tactile_transducer_lpf="SSTTRLPF {frequency}",
    command_delay_up="PSDELAY UP",
    command_delay_down="PSDELAY DOWN",
    command_auromatic_3d_preset="PSAUROPR {preset}",
    command_auromatic_3d_strength="PSAUROST {value}",
    command_auro_3d_mode="PSAUROMODE {mode}",
    command_dirac_filter="PSDIRAC {filter}",
    command_eco_mode="ECO{mode}",
    command_lfc="PSLFC {mode}",
    command_containment_amount="PSCNTAMT {value}",
    command_loudness_management="PSLOM {mode}",
    command_bass_sync="PSBSC {mode}",
    command_dialog_enhancer="PSDEH {level}",
    command_hdmi_output="VSMONI{output}",
    command_hdmi_audio_decode="VSAUDIO {mode}",
    command_quick_select_mode="MSQUICK{number}",
    command_quick_select_memory="MSQUICK{number} MEMORY",
    command_auto_standby="STBY{mode}",
    command_sleep="SLP{value}",
    command_center_spread="PSCES {mode}",
    command_video_processing_mode="VSVPM{mode}",
    command_room_size="PSRSZ {size}",
    command_status="RCSHP0230030",
    command_system_reset="SYRST",
    command_network_restart="NSRBT",
    command_trigger="TR{number} {mode}",
    command_speaker_preset="SPPR {number}",
    command_bluetooth_transmitter="BTTX {mode}",
    command_dialog_control="PSDIC {value}",
    command_speaker_virtualizer="PSSPV {mode}",
    command_effect_speaker_selection="PSSP:{mode}",
    command_drc="PSDRC {mode}",
    command_delay_time="PSDEL {value}",
    command_audio_restorer="PSRSTR {mode}",
    command_remote_control_lock="SYREMOTE LOCK {mode}",
    command_panel_lock="SYPANEL LOCK {mode}",
    command_panel_and_volume_lock="SYPANEL+V LOCK ON",
    command_graphic_eq="PSGEQ {mode}",
    command_headphone_eq="PSHEQ {mode}",
)

ZONE3_TELNET_COMMANDS = TelnetCommands(
    command_sel_src="Z3",
    command_fav_src="Z3",
    command_power_on="Z3ON",
    command_power_standby="Z3OFF",
    command_volume_up="Z3UP",
    command_volume_down="Z3DOWN",
    command_set_volume="Z3{volume:02d}",
    command_mute_on="Z3MUON",
    command_mute_off="Z3MUOFF",
    command_sel_sound_mode="MS",
    command_neural_x_on_off="PSNEURAL {mode}",
    command_imax_auto_off="PSIMAX {mode}",
    command_imax_audio_settings="PSIMAXAUD {mode}",
    command_imax_hpf="PSIMAXHPF {frequency}",
    command_imax_lpf="PSIMAXLPF {frequency}",
    command_imax_subwoofer_mode="PSIMAXSWM {mode}",
    command_imax_subwoofer_output="PSIMAXSWO {mode}",
    command_cinema_eq="PSCINEMA EQ.{mode}",
    command_set_all_zone_stereo="MN",
    command_pause="NS9B",
    command_play="NS9A",
    command_multieq="PSMULTEQ:",
    command_dynamiceq="PSDYNEQ ",
    command_reflevoffset="PSREFLEV ",
    command_dynamicvol="PSDYNVOL ",
    command_tonecontrol="PSTONE CTRL ",
    command_bass="PSBAS ",
    command_treble="PSTRE ",
    command_cusor_up="MNCUP",
    command_cusor_down="MNCDN",
    command_cusor_left="MNCLT",
    command_cusor_right="MNCRT",
    command_cusor_enter="MNENT",
    command_back="MNRTN",
    command_info="MNINF",
    command_options="MNOPT",
    command_setup_open="MNMEN ON",
    command_setup_close="MNMEN OFF",
    command_setup_query="MNMEN?",
    command_channel_level_adjust="MNCHL",
    command_dimmer_toggle="DIM SEL",
    command_dimmer_set="DIM {mode}",
    command_channel_volume="CV{channel} {value}",
    command_channel_volumes_reset="CVZRL",
    command_subwoofer_on_off="PSSWR {mode}",
    command_subwoofer_level="PSSWL{number} {mode}",
    command_lfe="PSLFE {mode}",
    command_tactile_transducer="SSTTR {mode}",
    command_tactile_transducer_level="SSTTRLEV {mode}",
    command_tactile_transducer_lpf="SSTTRLPF {frequency}",
    command_delay_up="PSDELAY UP",
    command_delay_down="PSDELAY DOWN",
    command_auromatic_3d_preset="PSAUROPR {preset}",
    command_auromatic_3d_strength="PSAUROST {value}",
    command_auro_3d_mode="PSAUROMODE {mode}",
    command_dirac_filter="PSDIRAC {filter}",
    command_eco_mode="ECO{mode}",
    command_lfc="PSLFC {mode}",
    command_containment_amount="PSCNTAMT {value}",
    command_loudness_management="PSLOM {mode}",
    command_bass_sync="PSBSC {mode}",
    command_dialog_enhancer="PSDEH {level}",
    command_hdmi_output="VSMONI{output}",
    command_hdmi_audio_decode="VSAUDIO {mode}",
    command_quick_select_mode="MSQUICK{number}",
    command_quick_select_memory="MSQUICK{number} MEMORY",
    command_auto_standby="STBY{mode}",
    command_sleep="SLP{value}",
    command_center_spread="PSCES {mode}",
    command_video_processing_mode="VSVPM{mode}",
    command_room_size="PSRSZ {size}",
    command_status="RCSHP0230030",
    command_system_reset="SYRST",
    command_network_restart="NSRBT",
    command_trigger="TR{number} {mode}",
    command_speaker_preset="SPPR {number}",
    command_bluetooth_transmitter="BTTX {mode}",
    command_dialog_control="PSDIC {value}",
    command_speaker_virtualizer="PSSPV {mode}",
    command_effect_speaker_selection="PSSP:{mode}",
    command_drc="PSDRC {mode}",
    command_delay_time="PSDEL {value}",
    command_audio_restorer="PSRSTR {mode}",
    command_remote_control_lock="SYREMOTE LOCK {mode}",
    command_panel_lock="SYPANEL LOCK {mode}",
    command_panel_and_volume_lock="SYPANEL+V LOCK ON",
    command_graphic_eq="PSGEQ {mode}",
    command_headphone_eq="PSHEQ {mode}",
)

# States
POWER_ON = "ON"
POWER_OFF = "OFF"
POWER_STANDBY = "STANDBY"
POWER_STATES = {POWER_ON, POWER_OFF, POWER_STANDBY}
STATE_ON = "on"
STATE_OFF = "off"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
SETTINGS_MENU_ON = "ON"
SETTINGS_MENU_OFF = "OFF"
SETTINGS_MENU_STATES = {SETTINGS_MENU_ON, SETTINGS_MENU_OFF}
DIMER_BRIGHT = "BRI"
DIMER_DIM = "DIM"
DIMER_DARK = "DAR"
DIMER_OFF = "OFF"
DIMMER_STATES = {DIMER_BRIGHT, DIMER_DIM, DIMER_DARK, DIMER_OFF}

# Zones
ALL_ZONES = "All"
MAIN_ZONE = "Main"
ZONE2 = "Zone2"
ZONE3 = "Zone3"
VALID_ZONES = {MAIN_ZONE, ZONE2, ZONE3}

# Setup additional zones
NO_ZONES = None
ZONE2_NAME = {ZONE2: None}
ZONE3_NAME = {ZONE3: None}
ZONE2_ZONE3_NAME = {ZONE2: None, ZONE3: None}

# AppCommand related
APPCOMMAND_CMD_TEXT = "cmd_text"
APPCOMMAND_NAME = "name"

# Audyssey parameter
MULTI_EQ_MAP_APPCOMMAND = {"0": "Off", "1": "Flat", "2": "L/R Bypass", "3": "Reference"}
MULTI_EQ_MAP_TELNET = {
    "OFF": "Off",
    "FLAT": "Flat",
    "BYP.LR": "L/R Bypass",
    "AUDYSSEY": "Reference",
    "MANUAL": "Manual",
}
MULTI_EQ_MAP = {**MULTI_EQ_MAP_APPCOMMAND, **MULTI_EQ_MAP_TELNET}
MULTI_EQ_MAP_LABELS_APPCOMMAND = {
    value: key for key, value in MULTI_EQ_MAP_APPCOMMAND.items()
}
MULTI_EQ_MAP_LABELS_TELNET = {value: key for key, value in MULTI_EQ_MAP_TELNET.items()}

REF_LVL_OFFSET_MAP_APPCOMMAND = {"0": "0dB", "1": "+5dB", "2": "+10dB", "3": "+15dB"}
REF_LVL_OFFSET_MAP_TELNET = {"0": "0dB", "5": "+5dB", "10": "+10dB", "15": "+15dB"}
REF_LVL_OFFSET_MAP = {**REF_LVL_OFFSET_MAP_APPCOMMAND, **REF_LVL_OFFSET_MAP_TELNET}
REF_LVL_OFFSET_MAP_LABELS_APPCOMMAND = {
    value: key for key, value in REF_LVL_OFFSET_MAP_APPCOMMAND.items()
}
REF_LVL_OFFSET_MAP_LABELS_TELNET = {
    value: key for key, value in REF_LVL_OFFSET_MAP_TELNET.items()
}

DYNAMIC_VOLUME_MAP_APPCOMMAND = {"0": "Off", "1": "Light", "2": "Medium", "3": "Heavy"}
DYNAMIC_VOLUME_MAP_TELNET = {
    "OFF": "Off",
    "LIT": "Light",
    "MED": "Medium",
    "HEV": "Heavy",
}
DYNAMIC_VOLUME_MAP = {**DYNAMIC_VOLUME_MAP_APPCOMMAND, **DYNAMIC_VOLUME_MAP_TELNET}
DYNAMIC_VOLUME_MAP_LABELS_APPCOMMAND = {
    value: key for key, value in DYNAMIC_VOLUME_MAP_APPCOMMAND.items()
}
DYNAMIC_VOLUME_MAP_LABELS_TELNET = {
    value: key for key, value in DYNAMIC_VOLUME_MAP_TELNET.items()
}

AudioRestorers = Literal["Off", "Low", "Medium", "High"]
"""Audio Restorer settings."""

AUDIO_RESTORER_MAP = {
    "Off": "OFF",
    "Low": "LOW",
    "Medium": "MED",
    "High": "HI",
}
AUDIO_RESTORER_MAP_LABELS = {value: key for key, value in AUDIO_RESTORER_MAP.items()}

AuroMatic3DPresets = Literal[
    "Small",
    "Medium",
    "Large",
    "Speech",
    "Movie",
]
"""Auro-Matic 3D Presets."""

AURO_MATIC_3D_PRESET_MAP = {
    "Small": "SMA",
    "Medium": "MED",
    "Large": "LAR",
    "Speech": "SPE",
    "Movie": "MOV",
}
AURO_MATIC_3D_PRESET_MAP_LABELS = {
    value: key for key, value in AURO_MATIC_3D_PRESET_MAP.items()
}

Auro3DModes = Literal["Direct", "Channel Expansion"]
"""Auro 3D Modes."""

AURO_3D_MODE_MAP = {"Direct": "DRCT", "Channel Expansion": "EXP"}
AURO_3D_MODE_MAP_MAP_LABELS = {value: key for key, value in AURO_3D_MODE_MAP.items()}

AutoStandbys = Literal["OFF", "15M", "30M", "60M"]

BluetoothOutputModes = Literal["Bluetooth + Speakers", "Bluetooth Only"]
"""Bluetooth Output Modes."""

BLUETOOTH_OUTPUT_MODES_MAP = {
    "Bluetooth + Speakers": "SP",
    "Bluetooth Only": "BT",
}
BLUETOOTH_OUTPUT_MAP_LABELS = {
    value: key for key, value in BLUETOOTH_OUTPUT_MODES_MAP.items()
}

DIMMER_MODE_MAP = {
    "Off": DIMER_OFF,
    "Dark": DIMER_DARK,
    "Dim": DIMER_DIM,
    "Bright": DIMER_BRIGHT,
}
DIMMER_MODE_MAP_LABELS = {value: key for key, value in DIMMER_MODE_MAP.items()}

DimmerModes = Literal["Off", "Dark", "Dim", "Bright"]
"""Dimmer Modes."""

DIRAC_FILTER_MAP = {"Off": "OFF", "Slot 1": "1", "Slot 2": "2", "Slot 3": "3"}
DIRAC_FILTER_MAP_LABELS = {value: key for key, value in DIRAC_FILTER_MAP.items()}

DiracFilters = Literal["Slot 1", "Slot 2", "Slot 3", "Off"]
"""Dirac Filters."""

ECO_MODE_MAP = {
    "On": "ON",
    "Auto": "AUTO",
    "Off": "OFF",
}
ECO_MODE_MAP_LABELS = {value: key for key, value in ECO_MODE_MAP.items()}

EcoModes = Literal["On", "Auto", "Off"]
"""Eco Modes."""

EffectSpeakers = Literal[
    "Floor",
    "Front",
    "Front Height",
    "Front Wide",
    "Front Height + Front Wide",
    "Height + Floor",
    "Surround Back",
    "Surround Back + Front Height",
    "Surround Back + Front Wide",
]
"""Effect Speakers."""

EFFECT_SPEAKER_SELECTION_MAP = {
    "Floor": "FL",
    "Front": "FR",
    "Front Height": "FH",
    "Front Wide": "FW",
    "Front Height + Front Wide": "HW",
    "Height + Floor": "HF",
    "Surround Back": "SB",
    "Surround Back + Front Height": "BH",
    "Surround Back + Front Wide": "BW",
}
EFFECT_SPEAKER_SELECTION_MAP_LABELS = {
    value: key for key, value in EFFECT_SPEAKER_SELECTION_MAP.items()
}

DRCs = Literal["AUTO", "LOW", "MID", "HI", "OFF"]
"""Dynamic Range Control (DRC) Settings."""

HDMI_OUTPUT_MAP = {
    "Auto": "AUTO",
    "HDMI1": "1",
    "HDMI2": "2",
}
HDMI_OUTPUT_MAP_LABELS = {
    "MONIAUTO": "Auto",
    "MONI1": "HDMI1",
    "MONI2": "HDMI2",
}

HDMIOutputs = Literal["Auto", "HDMI1", "HDMI2"]
"""HDMI Output Modes."""

HDMIAudioDecodes = Literal["AMP", "TV"]

Subwoofers = Literal["Subwoofer", "Subwoofer 2", "Subwoofer 3", "Subwoofer 4"]
"""Subwoofers."""

SUBWOOFERS_MAP = {
    "Subwoofer": "",
    "Subwoofer 2": "2",
    "Subwoofer 3": "3",
    "Subwoofer 4": "4",
}
"""Subwoofers."""

SUBWOOFERS_MAP_LABELS = {
    "SWL": "Subwoofer",
    "SWL2": "Subwoofer 2",
    "SWL3": "Subwoofer 3",
    "SWL4": "Subwoofer 4",
}

CHANNEL_MAP = {
    "Front Left": "FL",
    "Front Right": "FR",
    "Center": "C",
    "Subwoofer": "SW",
    "Subwoofer 2": "SW2",
    "Subwoofer 3": "SW3",
    "Subwoofer 4": "SW4",
    "Surround Left": "SL",
    "Surround Right": "SR",
    "Surround Back Left": "SBL",
    "Surround Back Right": "SBR",
    "Front Height Left": "FHL",
    "Front Height Right": "FHR",
    "Front Wide Left": "FWL",
    "Front Wide Right": "FWR",
    "Top Front Left": "TFL",
    "Top Front Right": "TFR",
    "Top Middle Left": "TML",
    "Top Middle Right": "TMR",
    "Top Rear Left": "TRL",
    "Top Rear Right": "TRR",
    "Rear Height Left": "RHL",
    "Rear Height Right": "RHR",
    "Front Dolby Left": "FDL",
    "Front Dolby Right": "FDR",
    "Surround Dolby Left": "SDL",
    "Surround Dolby Right": "SDR",
    "Back Dolby Left": "BDL",
    "Back Dolby Right": "BDR",
    "Surround Height Left": "SHL",
    "Surround Height Right": "SHR",
    "Top Surround": "TS",
    "Center Height": "CH",
}
CHANNEL_MAP_LABELS = {value: key for key, value in CHANNEL_MAP.items()}

Channels = Literal[
    "Front Left",
    "Front Right",
    "Center",
    "Subwoofer",
    "Subwoofer 2",
    "Subwoofer 3",
    "Subwoofer 4",
    "Surround Left",
    "Surround Right",
    "Surround Back Left",
    "Surround Back Right",
    "Front Height Left",
    "Front Height Right",
    "Front Wide Left",
    "Front Wide Right",
    "Top Front Left",
    "Top Front Right",
    "Top Middle Left",
    "Top Middle Right",
    "Top Rear Left",
    "Top Rear Right",
    "Rear Height Left",
    "Rear Height Right",
    "Front Dolby Left",
    "Front Dolby Right",
    "Surround Dolby Left",
    "Surround Dolby Right",
    "Back Dolby Left",
    "Back Dolby Right",
    "Surround Height Left",
    "Surround Height Right",
    "Top Surround",
    "Center Height",
]
"""Receiver Channels."""

CHANNEL_VOLUME_MAP = {
    "38": -12.0,
    "385": -11.5,
    "39": -11.0,
    "395": -10.5,
    "40": -10.0,
    "405": -9.5,
    "41": -9.0,
    "415": -8.5,
    "42": -8.0,
    "425": -7.5,
    "43": -7.0,
    "435": -6.5,
    "44": -6.0,
    "445": -5.5,
    "45": -5.0,
    "455": -4.5,
    "46": -4.0,
    "465": -3.5,
    "47": -3.0,
    "475": -2.5,
    "48": -2.0,
    "485": -1.5,
    "49": -1.0,
    "495": -0.5,
    "50": 0.0,
    "505": 0.5,
    "51": 1.0,
    "515": 1.5,
    "52": 2.0,
    "525": 2.5,
    "53": 3.0,
    "535": 3.5,
    "54": 4.0,
    "545": 4.5,
    "55": 5.0,
    "555": 5.5,
    "56": 6.0,
    "565": 6.5,
    "57": 7.0,
    "575": 7.5,
    "58": 8.0,
    "585": 8.5,
    "59": 9.0,
    "595": 9.5,
    "60": 10.0,
    "605": 10.5,
    "61": 11.0,
    "615": 11.5,
    "62": 12.0,
}
CHANNEL_VOLUME_MAP_LABELS = {value: key for key, value in CHANNEL_VOLUME_MAP.items()}

DialogEnhancerLevels = Literal["Off", "Low", "Medium", "High"]
"""Dialog Enhancer Levels."""

DIALOG_ENHANCER_LEVEL_MAP = {
    "Off": "OFF",
    "Low": "LOW",
    "Medium": "MED",
    "High": "HIGH",
}

DIALOG_ENHANCER_LEVEL_MAP_LABELS = {
    value: key for key, value in DIALOG_ENHANCER_LEVEL_MAP.items()
}

TransducerLPFs = Literal[
    "40 Hz",
    "60 Hz",
    "80 Hz",
    "90 Hz",
    "100 Hz",
    "110 Hz",
    "120 Hz",
    "150 Hz",
    "180 Hz",
    "200 Hz",
    "250 Hz",
]
"""Tactile Transducer Low Pass Frequencies."""

IMAXHPFs = Literal[
    "40", "60", "80", "90", "100", "110", "120", "150", "180", "200", "250"
]
"""IMAX High Pass Frequencies."""

IMAXLPFs = Literal["80", "90", "100", "110", "120", "150", "180", "200", "250"]
"""IMAX Low Pass Frequencies."""

PanelLocks = Literal["Panel", "Panel + Master Volume"]
"""Panel Lock Modes."""

RoomSizes = Literal[
    "S",
    "MS",
    "M",
    "ML",
    "L",
]
"""Room Sizes."""

VideoProcessingModes = Literal["Auto", "Game", "Movie", "Bypass"]
"""Video Processing Modes."""

VIDEO_PROCESSING_MODES_MAP = {
    "Auto": "AUTO",
    "Game": "GAME",
    "Movie": "MOVI",
    "Bypass": "BYP",
}

VIDEO_PROCESSING_MODES_MAP_LABELS = {
    value: key for key, value in VIDEO_PROCESSING_MODES_MAP.items()
}
