#!/usr/bin/env python

"""
Measure one-way UDP packet latency between two hosts.
Latency is calculated using the system clock.

One host runs the script in client mode.
Client mode simply sends packets to the designated target address.

The other host runs the script in server mode.
Server mode receives packets from all the transmitting clients and saves them
to a separate file. The file contains a plain text list of
packet number/round-trip latency (in milliseconds) tuples for each packet
received, one per line. The first line of the file specifies the number of
packets sent, enabling calculation of the number of packets that got lost along
the way.
"""

import common
import onewaymeasurementtime

common.main(onewaymeasurementtime.OneWayMeasurementTime)
