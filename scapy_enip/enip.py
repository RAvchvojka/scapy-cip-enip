# Copyright (c) 2022, Vojtěch Chvojka, Rockwell Automation, inc.
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

from struct import pack

from scapy.all import Packet, LEShortEnumField, LEShortField, LEIntField, LEIntEnumField, \
    LongField, TCP, bind_layers, UDP

from scapy_enip.enip_constants import commands, statuses
from scapy_cip_enip_common.test_utils import AssertRaises


ETHERNET_INDUSTRIAL_PROTO_PORT_NO = 44818


class Enip(Packet):
    """Ethernet/IP packet"""
    name = "Ethernet Industrial Protocol"
    fields_desc = [
        LEShortEnumField("command_id", 0, enum=commands),
        LEShortField("length", None),
        LEIntField("session", 0),
        LEIntEnumField("status", 0, enum=statuses),
        LongField("sender_context", 0),
        LEIntField("options", 0),
    ]

    def extract_padding(self, p):
        return p[:self.length], p[self.length:]

    def post_build(self, p, pay):
        if self.length is None and pay:
            p = p[:2] + pack("<H", len(pay)) + p[4:]
        return p + pay


def run_tests(verbose: bool = True):
    # Dissection test
    original_data = b'\x6f\x00\x16\x00\x10\x20\x30\x40\x00\x00\x00\x00\x01\x02' \
                    b'\x03\x04\x05\x06\x07\x08\x00\x00\x00\x00'
    pkt = Enip(original_data)
    if verbose:
        print(repr(pkt))
    assert(pkt.command_id == 0x006f)
    assert(pkt.length == 0x16)
    assert(pkt.session == 0x40302010)
    assert(pkt.status == 0)
    assert(pkt.sender_context == 0x0102030405060708)
    assert(pkt.options == 0)
    assert(pkt.build() == original_data)

    # Build tests
    raw_data = Enip(command_id="Nop", status="InvalidCommand").build()
    assert(raw_data[0] == 0)
    assert(raw_data[8] == 1)

    raw_data = Enip(command_id="ListServices", status="InsufficientMemory").build()
    assert(raw_data[0] == 4)
    assert(raw_data[8] == 2)

    raw_data = Enip(command_id="ListIdentity", status="IncorrectData").build()
    assert(raw_data[0] == 0x63)
    assert(raw_data[8] == 3)

    raw_data = Enip(command_id="ListInterfaces", status="InvalidSessionHandle").build()
    assert(raw_data[0] == 0x64)
    assert(raw_data[8] == 0x64)

    raw_data = Enip(command_id="RegisterSession", status="InvalidLength").build()
    assert(raw_data[0] == 0x65)
    assert(raw_data[8] == 0x65)

    raw_data = Enip(command_id="UnRegisterSession", status="UnsupportedProtocolVersion").build()
    assert(raw_data[0] == 0x66)
    assert(raw_data[8] == 0x69)

    raw_data = Enip(command_id="SendRRData", status="CipServiceNotAllowed").build()
    assert(raw_data[0] == 0x6F)
    assert(raw_data[8] == 0x6A)

    raw_data = Enip(command_id="SendUnitData").build()
    assert(raw_data[0] == 0x70)

    raw_data = Enip(command_id="StartDtls").build()
    assert(raw_data[0] == 0xC8)

    with AssertRaises(KeyError):
        Enip(command_id="UndefinedCommandConstant")

    with AssertRaises(KeyError):
        Enip(status="UndefinedStatusConstant")


bind_layers(TCP, Enip, dport=ETHERNET_INDUSTRIAL_PROTO_PORT_NO)
bind_layers(TCP, Enip, sport=ETHERNET_INDUSTRIAL_PROTO_PORT_NO)
bind_layers(UDP, Enip, dport=ETHERNET_INDUSTRIAL_PROTO_PORT_NO)
bind_layers(UDP, Enip, sport=ETHERNET_INDUSTRIAL_PROTO_PORT_NO)


if __name__ == '__main__':
    run_tests()
