"""
Measure one-way packet latencies using a hardware timer (here implemented as a
counter) accessible from both the client and the server.
"""

import measurement
import socket
import time
import pickle

class OneWayMeasurementTime(measurement.Measurement):

    description = """Measure one-way UDP packet latency time.
On your server host, run:
    $ ./quack2.py --server
On your client host(s), run:
    $ ./quack2.py --client <IP address of server host>
quack.py on your server host will spit out one file containing
the latencies of each packet received from the client.
"""

    def run_client(self, target_address, n_packets, payload_len,
            send_rate_kbytes_per_s):

        self.send_packets(target_address, n_packets, payload_len, send_rate_kbytes_per_s)

    @classmethod
    def pre_send(cls, n_packets, sock_out):
        """
        Let the server know how many packets to expect
        """
        sock_out.sendall(("%d" % n_packets).encode())

    @classmethod
    def get_packet_payload(cls, packet_n):
        """
        Return a packet payload consisting of:
        - The packet number
        - The timestamp of the packet
        """

        send_time_seconds = time.time()
        payload = pickle.dumps((packet_n, send_time_seconds))
        return payload

    def run_server(self, server_listen_port, payload_len):
        """
        Receive packets sent from the client. Calculate the latency for each
        packet by comparing the counter value from the packet (the counter value
        at time of transmission) to the current counter value.
        """
        sock_in = \
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock_in.bind(("0.0.0.0", server_listen_port))

        print("UDP server running...")

        timeout_seconds = 5
        sock_in.settimeout(timeout_seconds)

        packets = []
        try:
            data = sock_in.recv(payload_len)
            n_packets_expected = int(data)
            print("Expecting %d packets" % n_packets_expected)

            while len(packets) < n_packets_expected:
                data = sock_in.recv(payload_len)

                payload = data.rstrip("a")
                (packet_n, send_time) = pickle.loads(payload)
                recv_time = time.time()
                latency_us = (recv_time - send_time) * 1e6
                packets.append((packet_n, latency_us))

        except socket.timeout:
            print("Note: timed out waiting to receive packets")
            print("So far, had received %d packets" % len(packets))
        except KeyboardInterrupt:
            print("Interrupted")

        sock_in.close()

        print("Received %d packets" % len(packets))

        self.save_packet_latencies(packets, n_packets_expected, self.test_output_filename)
