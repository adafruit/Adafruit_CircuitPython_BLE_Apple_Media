# The MIT License (MIT)
#
# Copyright (c) 2020 Scott Shawcroft for Adafruit Industries LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_ble_apple_media`
================================================================================

Support for the Apple Media Service which provides media playback info and control.

Documented by Apple here:
https://developer.apple.com/library/archive/documentation/CoreBluetooth/Reference/AppleMediaService_Reference/Introduction/Introduction.html#//apple_ref/doc/uid/TP40014716-CH2-SW1

"""
import struct
import time

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic, ComplexCharacteristic
from adafruit_ble.uuid import VendorUUID
from adafruit_ble.services import Service

import _bleio

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Apple_Media.git"


class _RemoteCommand(ComplexCharacteristic):
    """Endpoint for sending commands to a media player. The value read will list all available

       commands."""
    uuid = VendorUUID("9B3C81D8-57B1-4A8A-B8DF-0E56F7CA51C2")

    def __init__(self):
        super().__init__(properties=Characteristic.WRITE_NO_RESPONSE | Characteristic.NOTIFY,
                         read_perm=Attribute.OPEN, write_perm=Attribute.OPEN,
                         max_length=13,
                         fixed_length=False)

    def bind(self, service):
        """Binds the characteristic to the given Service."""
        bound_characteristic = super().bind(service)
        return _bleio.PacketBuffer(bound_characteristic,
                                   buffer_size=1)

class _EntityUpdate(ComplexCharacteristic):
    """UTF-8 Encoded string characteristic."""
    uuid = VendorUUID("2F7CABCE-808D-411F-9A0C-BB92BA96C102")

    def __init__(self):
        super().__init__(properties=Characteristic.WRITE | Characteristic.NOTIFY,
                         read_perm=Attribute.OPEN, write_perm=Attribute.OPEN,
                         max_length=128,
                         fixed_length=False)


    def bind(self, service):
        """Binds the characteristic to the given Service."""
        bound_characteristic = super().bind(service)
        return _bleio.PacketBuffer(bound_characteristic,
                                   buffer_size=8)

class _EntityAttribute(Characteristic):
    """UTF-8 Encoded string characteristic."""
    uuid = VendorUUID("C6B2F38C-23AB-46D8-A6AB-A3A870BBD5D7")

    def __init__(self):
        super().__init__(properties=Characteristic.WRITE | Characteristic.READ,
                         read_perm=Attribute.OPEN, write_perm=Attribute.OPEN,
                         fixed_length=False)

class _MediaAttribute:
    def __init__(self, entity_id, attribute_id):
        self.key = (entity_id, attribute_id)

    def _update(self, obj):
        if not obj._buffer:
            obj._buffer = bytearray(128)
        len = obj._entity_update.readinto(obj._buffer)
        if len > 0:
            if len < 4:
                raise RuntimeError("packet too short")
            entity_id, attribute_id, flags = struct.unpack_from("<BBB", obj._buffer)
            value = str(obj._buffer[3:len], "utf-8")
            obj._attribute_cache[(entity_id, attribute_id)] = value

    def __get__(self, obj, cls):
        self._update(obj)
        if self.key not in obj._attribute_cache:
            siblings = [self.key[1]]
            for k in obj._attribute_cache:
                if k[0] == self.key[0] and k[1] not in siblings:
                    siblings.append(k[1])
            buf = struct.pack("<B" + "B"*len(siblings), self.key[0], *siblings)
            obj._entity_update.write(buf)
            obj._attribute_cache[self.key] = None
            time.sleep(0.05)
            self._update(obj)
        return obj._attribute_cache[self.key]

class _MediaAttributePlaybackState:
    def __init__(self, playback_value):
        self._playback_value = playback_value

    def __get__(self, obj, cls):
        info = obj._playback_info
        if info:
            return int(info.split(",")[0]) == self._playback_value
        return False

class _MediaAttributePlaybackInfo:
    def __init__(self, position):
        self._position = position

    def __get__(self, obj, cls):
        info = obj._playback_info
        if info:
            return float(info.split(",")[self._position])
        return 0

class UnsupportedCommand(Exception):
    pass

class AppleMediaService(Service):
    """View and control currently playing media. Unimplemented."""
    uuid = VendorUUID("89D3502B-0F36-433A-8EF4-C502AD55F8DC")

    _remote_command = _RemoteCommand()
    _entity_update = _EntityUpdate()
    _entity_attribute = _EntityAttribute()

    player_name = _MediaAttribute(0, 0)
    _playback_info = _MediaAttribute(0, 1)
    paused = _MediaAttributePlaybackState(0)
    playing = _MediaAttributePlaybackState(1)
    rewinding = _MediaAttributePlaybackState(2)
    fast_forwarding = _MediaAttributePlaybackState(3)
    playback_rate = _MediaAttributePlaybackInfo(1)
    elapsed_time = _MediaAttributePlaybackInfo(2)
    volume = _MediaAttribute(0, 2)

    queue_index = _MediaAttribute(1, 0)
    queue_length = _MediaAttribute(1, 1)
    shuffle_mode = _MediaAttribute(1, 2)
    repeat_mode = _MediaAttribute(1, 3)

    artist = _MediaAttribute(2, 0)
    album = _MediaAttribute(2, 1)
    title = _MediaAttribute(2, 2)
    duration = _MediaAttribute(2, 3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._buffer = None
        self._cmd = None
        self._register_buffer = None
        self._attribute_cache = {}
        self._supported_commands = []
        self._command_buffer = None

    def _send_command(self, command_id):
        if not self._command_buffer:
            self._command_buffer = bytearray(13)
        i = self._remote_command.readinto(self._command_buffer)
        if i > 0:
            self._supported_commands = list(self._command_buffer[:i])
        if command_id not in self._supported_commands:
            if not self._supported_commands:
                return
            raise UnsupportedCommand()
        if not self._cmd:
            self._cmd = bytearray(1)
        self._cmd[0] = command_id
        self._remote_command.write(self._cmd)

    def play(self):
        self._send_command(0)

    def pause(self):
        self._send_command(1)

    def toggle_play_pause(self):
        self._send_command(2)

    def next_track(self):
        self._send_command(3)

    def previous_track(self):
        self._send_command(4)

    def volume_up(self):
        self._send_command(5)

    def volume_down(self):
        self._send_command(6)

    def advance_repeat_mode(self):
        self._send_command(7)

    def advance_shuffle_mode(self):
        self._send_command(8)

    def skip_forward(self):
        self._send_command(9)

    def skip_backward(self):
        self._send_command(10)

    def like_track(self):
        self._send_command(11)

    def dislike_track(self):
        self._send_command(12)

    def bookmark_track(self):
        self._send_command(13)
