#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the interface to Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import asyncio
import logging
import time
from typing import Awaitable, Callable, Dict, List, Optional

import attr
import httpx

from .audyssey import DenonAVRAudyssey, audyssey_factory
from .const import DENON_ATTR_SETATTR, MAIN_ZONE, VALID_ZONES
from .exceptions import AvrCommandError
from .foundation import DenonAVRFoundation, set_api_host, set_api_timeout
from .input import DenonAVRInput, input_factory
from .soundmode import DenonAVRSoundMode, sound_mode_factory
from .tonecontrol import DenonAVRToneControl, tone_control_factory
from .volume import DenonAVRVolume, volume_factory

_LOGGER = logging.getLogger(__name__)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVR(DenonAVRFoundation):
    """
    Representing a Denon AVR Device.

    Initialize MainZone of DenonAVR.

    :param host: IP or HOSTNAME.
    :type host: str

    :param name: Device name, if None FriendlyName of device is used.
    :type name: str or None

    :param show_all_inputs: If True deleted input functions are also shown
    :type show_all_inputs: bool

    :param timeout: Timeout when calling device APIs.
    :type timeout: float

    :param add_zones: Additional Zones for which an instance are created
    :type add_zones: dict [str, str] or None
    """

    _host: str = attr.ib(converter=str, on_setattr=[*DENON_ATTR_SETATTR, set_api_host])
    _name: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _show_all_inputs: bool = attr.ib(converter=bool, default=False)
    _add_zones: Optional[Dict[str, str]] = attr.ib(
        validator=attr.validators.optional(
            attr.validators.deep_mapping(
                attr.validators.in_(VALID_ZONES),
                attr.validators.optional(attr.validators.instance_of(str)),
                attr.validators.instance_of(dict),
            )
        ),
        default=None,
    )
    _timeout: float = attr.ib(
        converter=float, on_setattr=[*DENON_ATTR_SETATTR, set_api_timeout], default=2.0
    )
    _zones: Dict[str, DenonAVRFoundation] = attr.ib(
        validator=attr.validators.deep_mapping(
            attr.validators.in_(VALID_ZONES),
            attr.validators.instance_of(DenonAVRFoundation),
            attr.validators.instance_of(dict),
        ),
        default=attr.Factory(dict),
        init=False,
    )
    _setup_lock: asyncio.Lock = attr.ib(default=attr.Factory(asyncio.Lock))
    audyssey: DenonAVRAudyssey = attr.ib(
        validator=attr.validators.instance_of(DenonAVRAudyssey),
        default=attr.Factory(audyssey_factory, takes_self=True),
        init=False,
    )
    input: DenonAVRInput = attr.ib(
        validator=attr.validators.instance_of(DenonAVRInput),
        default=attr.Factory(input_factory, takes_self=True),
        init=False,
    )
    soundmode: DenonAVRSoundMode = attr.ib(
        validator=attr.validators.instance_of(DenonAVRSoundMode),
        default=attr.Factory(sound_mode_factory, takes_self=True),
        init=False,
    )
    tonecontrol: DenonAVRToneControl = attr.ib(
        validator=attr.validators.instance_of(DenonAVRToneControl),
        default=attr.Factory(tone_control_factory, takes_self=True),
        init=False,
    )
    vol: DenonAVRVolume = attr.ib(
        validator=attr.validators.instance_of(DenonAVRVolume),
        default=attr.Factory(volume_factory, takes_self=True),
        init=False,
    )

    def __attrs_post_init__(self) -> None:
        """Initialize special attributes."""
        # Set host and timeout again to start its custom setattr function
        self._host = self._host
        self._timeout = self._timeout

        # Add own instance to zone dictionary
        self._zones[self._device.zone] = self

        # Create instances of additional zones if requested
        if self._device.zone == MAIN_ZONE and self._add_zones is not None:
            self.create_zones(self._add_zones)

    def create_zones(self, add_zones):
        """Create instances of additional zones for the receiver."""
        for zone, zname in add_zones.items():
            # Name either set explicitly or name of Main Zone with suffix
            zonename = None
            if zname is None and self._name is not None:
                zonename = f"{self._name} {zone}"
            zone_device = attr.evolve(self._device, zone=zone)
            zone_inst = DenonAVR(
                host=self._host,
                device=zone_device,
                name=zonename,
                timeout=self._timeout,
                show_all_inputs=self._show_all_inputs,
            )
            self._zones[zone] = zone_inst

    async def async_setup(self) -> None:
        """Ensure that configuration is loaded from receiver asynchronously."""
        async with self._setup_lock:
            _LOGGER.debug("Starting denonavr setup")
            # Device setup
            await self._device.async_setup()
            if self._name is None:
                self._name = self._device.friendly_name

            # Setup other functions
            self.input.setup()
            await self.soundmode.async_setup()
            await self.tonecontrol.async_setup()
            self.vol.setup()
            self.audyssey.setup()

            for zone_name, zone_item in self._zones.items():
                if zone_name != self.zone:
                    await zone_item.async_setup()

            self._is_setup = True
            _LOGGER.debug("Finished denonavr setup")

    async def async_update(self):
        """
        Get the latest status information from device asynchronously.

        Method executes the update method for the current receiver type.
        """
        _LOGGER.debug("Starting denonavr update")
        # Ensure that the device is setup
        if not self._is_setup:
            await self.async_setup()

        # Create a cache id for this global update
        cache_id = time.time()

        # Verify update method
        _LOGGER.debug("Verifying update method")
        await self._device.async_verify_avr_2016_update_method(cache_id=cache_id)

        # Update device
        await self._device.async_update(global_update=True, cache_id=cache_id)

        # Update other functions
        await self.input.async_update(global_update=True, cache_id=cache_id)
        await self.soundmode.async_update(global_update=True, cache_id=cache_id)
        await self.tonecontrol.async_update(global_update=True, cache_id=cache_id)
        await self.vol.async_update(global_update=True, cache_id=cache_id)

        # AppCommand0300.xml interface is very slow, thus it is not included
        # into main update
        # await self.audyssey.async_update(
        #     global_update=True, cache_id=cache_id)
        _LOGGER.debug("Finished denonavr update")

    async def async_update_tonecontrol(self):
        """Get Tonecontrol settings."""
        await self.tonecontrol.async_update()

    async def async_update_audyssey(self):
        """Get Audyssey settings."""
        await self.audyssey.async_update()

    async def async_get_command(self, request: str) -> str:
        """Send HTTP GET command to Denon AVR receiver asynchronously."""
        return await self._device.api.async_get_command(request)

    async def async_send_telnet_commands(self, *commands: str) -> None:
        """Send telnet commands to the receiver."""
        await self._device.telnet_api.async_send_commands(*commands)

    def send_telnet_commands(self, *commands: str) -> None:
        """Send telnet commands to the receiver."""
        self._device.telnet_api.send_commands(*commands)

    def register_callback(
        self, event: str, callback: Callable[[str, str, str], Awaitable[None]]
    ):
        """Register a callback for telnet events."""
        self._device.telnet_api.register_callback(event, callback=callback)

    def unregister_callback(
        self, event: str, callback: Callable[[str, str, str], Awaitable[None]]
    ):
        """Unregister a callback for telnet events."""
        self._device.telnet_api.unregister_callback(event, callback=callback)

    async def async_telnet_connect(self):
        """Connect to the telnet interface of the receiver."""
        await self._device.telnet_api.async_connect()

    async def async_telnet_disconnect(self):
        """Disconnect from the telnet interface of the receiver."""
        await self._device.telnet_api.async_disconnect()

    ##############
    # Properties #
    ##############
    @property
    def zone(self) -> str:
        """Return Zone of this instance."""
        return self._device.zone

    @property
    def zones(self) -> Dict[str, DenonAVRFoundation]:
        """Return all Zone instances of the device."""
        zones = self._zones.copy()
        return zones

    @property
    def name(self) -> Optional[str]:
        """Return the name of the device as string."""
        return self._name

    @property
    def host(self) -> str:
        """Return the host of the device as string."""
        return self._host

    @property
    def manufacturer(self) -> Optional[str]:
        """Return the manufacturer of the device as string."""
        return self._device.manufacturer

    @property
    def model_name(self) -> Optional[str]:
        """Return the model name of the device as string."""
        return self._device.model_name

    @property
    def serial_number(self) -> Optional[str]:
        """Return the serial number of the device as string."""
        return self._device.serial_number

    @property
    def power(self) -> Optional[str]:
        """
        Return the power state of the device.

        Possible values are: "ON", "STANDBY" and "OFF"
        """
        return self._device.power

    @property
    def state(self) -> Optional[str]:
        """
        Return the state of the device.

        Possible values are: "on", "off", "playing", "paused"
        "playing" and "paused" are only available for input functions
        in PLAYING_SOURCES.
        """
        return self.input.state

    @property
    def muted(self) -> bool:
        """
        Boolean if volume is currently muted.

        Return "True" if muted and "False" if not muted.
        """
        return self.vol.muted

    @property
    def volume(self) -> float:
        """
        Return volume of Denon AVR as float.

        Volume is send in a format like -50.0.
        Minimum is -80.0, maximum at 18.0
        """
        return self.vol.volume

    @property
    def input_func(self) -> Optional[str]:
        """Return the current input source as string."""
        return self.input.input_func

    @property
    def input_func_list(self) -> List[str]:
        """Return a list of available input sources as string."""
        return self.input.input_func_list

    @property
    def support_sound_mode(self) -> Optional[bool]:
        """Return True if sound mode is supported."""
        return self.soundmode.support_sound_mode

    @property
    def sound_mode(self) -> Optional[str]:
        """Return the matched current sound mode as a string."""
        return self.soundmode.sound_mode

    @property
    def sound_mode_list(self) -> List[str]:
        """Return a list of available sound modes as string."""
        return self.soundmode.sound_mode_list

    @property
    def sound_mode_map(self) -> Dict[str, str]:
        """Return a dict of available sound modes with their mapping values."""
        return self.soundmode.sound_mode_map

    @property
    def sound_mode_map_rev(self) -> Dict[str, str]:
        """Return a dict to map each sound_mode_raw to matching sound_mode."""
        return self.soundmode.sound_mode_map_rev

    @property
    def sound_mode_raw(self) -> Optional[str]:
        """Return the current sound mode as string as received from the AVR."""
        return self.soundmode.sound_mode_raw

    @property
    def image_url(self) -> Optional[str]:
        """Return image URL of current playing media when powered on."""
        return self.input.image_url

    @property
    def title(self) -> Optional[str]:
        """Return title of current playing media as string."""
        return self.input.title

    @property
    def artist(self) -> Optional[str]:
        """Return artist of current playing media as string."""
        return self.input.artist

    @property
    def album(self) -> Optional[str]:
        """Return album name of current playing media as string."""
        return self.input.album

    @property
    def band(self) -> Optional[str]:
        """Return band of current radio station as string."""
        return self.input.band

    @property
    def frequency(self) -> Optional[str]:
        """Return frequency of current radio station as string."""
        return self.input.frequency

    @property
    def station(self) -> Optional[str]:
        """Return current radio station as string."""
        return self.input.station

    @property
    def netaudio_func_list(self) -> List[str]:
        """Return list of network audio devices.

        Those devices should react to play, pause, next and previous
        track commands.
        """
        return self.input.netaudio_func_list

    @property
    def playing_func_list(self) -> List[str]:
        """Return list of playing devices.

        Those devices offer additional information about what they are playing
        (e.g. title, artist, album, band, frequency, station, image_url).
        """
        return self.input.playing_func_list

    @property
    def receiver_port(self) -> int:
        """Return the receiver's port."""
        if self._device.receiver is None:
            return None
        return self._device.receiver.port

    @property
    def receiver_type(self) -> Optional[str]:
        """Return the receiver's type."""
        if self._device.receiver is None:
            return None
        return self._device.receiver.type

    @property
    def telnet_available(self) -> bool:
        """Return True if telnet is connected and healthy."""
        return self._device.telnet_available

    @property
    def telnet_connected(self) -> bool:
        """Return True if telnet is connected."""
        return self._device.telnet_api.connected

    @property
    def telnet_healthy(self) -> bool:
        """Return True if telnet connection is healthy."""
        return self._device.telnet_api.healthy

    @property
    def show_all_inputs(self) -> Optional[bool]:
        """Indicate if all inputs are shown or just active one."""
        return self._show_all_inputs

    @property
    def support_tone_control(self) -> Optional[bool]:
        """Return True if tone control is supported."""
        return self.tonecontrol.support_tone_control

    @property
    def tone_control_status(self) -> Optional[bool]:
        """Return value of tone control status."""
        return self.tonecontrol.tone_control_status

    @property
    def tone_control_adjust(self) -> Optional[bool]:
        """Return value of tone control adjust."""
        return self.tonecontrol.tone_control_adjust

    @property
    def bass(self) -> Optional[int]:
        """Return value of bass."""
        return self.tonecontrol.bass

    @property
    def bass_level(self) -> Optional[str]:
        """Return level of bass."""
        return self.tonecontrol.bass_level

    @property
    def treble(self) -> Optional[int]:
        """Return value of treble."""
        return self.tonecontrol.treble

    @property
    def treble_level(self) -> Optional[str]:
        """Return level of treble."""
        return self.tonecontrol.treble_level

    @property
    def dynamic_eq(self) -> Optional[bool]:
        """Return value of Dynamic EQ."""
        return self.audyssey.dynamic_eq

    @property
    def reference_level_offset(self) -> Optional[str]:
        """Return value of Reference Level Offset."""
        return self.audyssey.reference_level_offset

    @property
    def reference_level_offset_setting_list(self) -> List[str]:
        """Return a list of available reference level offset settings."""
        return self.audyssey.reference_level_offset_setting_list

    @property
    def dynamic_volume(self) -> Optional[str]:
        """Return value of Dynamic Volume."""
        return self.audyssey.dynamic_volume

    @property
    def dynamic_volume_setting_list(self) -> List[str]:
        """Return a list of available Dynamic Volume settings."""
        return self.audyssey.dynamic_volume_setting_list

    @property
    def multi_eq(self) -> Optional[str]:
        """Return value of MultiEQ."""
        return self.audyssey.multi_eq

    @property
    def multi_eq_setting_list(self) -> List[str]:
        """Return a list of available MultiEQ settings."""
        return self.audyssey.multi_eq_setting_list

    ##########
    # Setter #
    ##########
    def set_async_client_getter(
        self, async_client_getter: Callable[[], httpx.AsyncClient]
    ) -> None:
        """
        Set a custom httpx.AsyncClient getter for this instance.

        The function provided must return an instance of httpx.AsyncClient.
        This is a non-blocking method.
        """
        if not callable(async_client_getter):
            raise AvrCommandError("Provided object is not callable")
        self._device.api.httpx_async_client.client_getter = async_client_getter

    async def async_dynamic_eq_off(self) -> None:
        """Turn DynamicEQ off."""
        await self.audyssey.async_dynamiceq_off()

    async def async_dynamic_eq_on(self) -> None:
        """Turn DynamicEQ on."""
        await self.audyssey.async_dynamiceq_on()

    async def async_toggle_dynamic_eq(self) -> None:
        """Toggle DynamicEQ."""
        await self.audyssey.async_toggle_dynamic_eq()

    async def async_set_multieq(self, value: str) -> None:
        """Set MultiEQ mode."""
        await self.audyssey.async_set_multieq(value)

    async def async_set_reflevoffset(self, value: str) -> None:
        """Set Reference Level Offset."""
        await self.audyssey.async_set_reflevoffset(value)

    async def async_set_dynamicvol(self, value: str) -> None:
        """Set Dynamic Volume."""
        await self.audyssey.async_set_dynamicvol(value)

    async def async_set_input_func(self, input_func: str) -> None:
        """
        Set input_func of device.

        Valid values depend on the device and should be taken from
        "input_func_list".
        """
        await self.input.async_set_input_func(input_func)

    async def async_set_sound_mode(self, sound_mode: str) -> None:
        """
        Set sound_mode of device.

        Valid values depend on the device and should be taken from
        "sound_mode_list".
        """
        await self.soundmode.async_set_sound_mode(sound_mode)

    async def async_toggle_play_pause(self) -> None:
        """Toggle play pause media player."""
        await self.input.async_toggle_play_pause()

    async def async_play(self) -> None:
        """Send play command to receiver command via HTTP post."""
        await self.input.async_play()

    async def async_pause(self) -> None:
        """Send pause command to receiver command via HTTP post."""
        await self.input.async_pause()

    async def async_previous_track(self) -> None:
        """Send previous track command to receiver command via HTTP post."""
        await self.input.async_previous_track()

    async def async_next_track(self) -> None:
        """Send next track command to receiver command via HTTP post."""
        await self.input.async_next_track()

    async def async_power_on(self) -> None:
        """Turn on receiver via HTTP get command."""
        await self._device.async_power_on()

    async def async_power_off(self) -> None:
        """Turn off receiver via HTTP get command."""
        await self._device.async_power_off()

    async def async_volume_up(self) -> None:
        """Volume up receiver via HTTP get command."""
        await self.vol.async_volume_up()

    async def async_volume_down(self) -> None:
        """Volume down receiver via HTTP get command."""
        await self.vol.async_volume_down()

    async def async_set_volume(self, volume: float) -> None:
        """
        Set receiver volume via HTTP get command.

        Volume is send in a format like -50.0.
        Minimum is -80.0, maximum at 18.0
        """
        await self.vol.async_set_volume(volume)

    async def async_mute(self, mute: bool) -> None:
        """Mute receiver via HTTP get command."""
        await self.vol.async_mute(mute)

    async def async_enable_tone_control(self) -> None:
        """Enable tone control to change settings like bass or treble."""
        await self.tonecontrol.async_enable_tone_control()

    async def async_disable_tone_control(self) -> None:
        """Disable tone control to change settings like bass or treble."""
        await self.tonecontrol.async_disable_tone_control()

    async def async_set_bass(self, value: int) -> None:
        """
        Set receiver bass.

        Minimum is 0, maximum at 12

        Note:
        Doesn't work, if Dynamic Equalizer is active.
        """
        await self.tonecontrol.async_set_bass(value)

    async def async_bass_up(self) -> None:
        """
        Increase level of Bass.

        Note:
        Doesn't work, if Dynamic Equalizer is active
        """
        await self.tonecontrol.async_bass_up()

    async def async_bass_down(self) -> None:
        """
        Decrease level of Bass.

        Note:
        Doesn't work, if Dynamic Equalizer is active
        """
        await self.tonecontrol.async_bass_down()

    async def async_set_treble(self, value: int) -> None:
        """
        Set receiver treble.

        Minimum is 0, maximum at 12

        Note:
        Doesn't work, if Dynamic Equalizer is active.
        """
        await self.tonecontrol.async_set_treble(value)

    async def async_treble_up(self) -> None:
        """
        Increase level of Treble.

        Note:
        Doesn't work, if Dynamic Equalizer is active
        """
        await self.tonecontrol.async_treble_up()

    async def async_treble_down(self) -> None:
        """
        Decrease level of Treble.

        Note:
        Doesn't work, if Dynamic Equalizer is active
        """
        await self.tonecontrol.async_treble_down()

    async def async_cursor_up(self) -> None:
        """Send cursor up to receiver via HTTP get command."""
        await self._device.async_cursor_up()

    async def async_cursor_down(self) -> None:
        """Send cursor down to receiver via HTTP get command."""
        await self._device.async_cursor_down()

    async def async_cursor_left(self) -> None:
        """Send cursor left to receiver via HTTP get command."""
        await self._device.async_cursor_left()

    async def async_cursor_right(self) -> None:
        """Send cursor right to receiver via HTTP get command."""
        await self._device.async_cursor_right()

    async def async_cursor_enter(self) -> None:
        """Send cursor enter to receiver via HTTP get command."""
        await self._device.async_cursor_enter()

    async def async_back(self) -> None:
        """Send back to receiver via HTTP get command."""
        await self._device.async_back()

    async def async_info(self) -> None:
        """Send info to receiver via HTTP get command."""
        await self._device.async_info()

    async def async_options(self) -> None:
        """Raise options menu to receiver via HTTP get command."""
        await self._device.async_options()

    async def async_settings_menu(self) -> None:
        """Raise settings menu to receiver via HTTP get command."""
        await self._device.async_settings_menu()
