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

    def run_server(self, server_listen_port, recv_buffer_size):
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

        n_packets_expected = -1

        packets = []
        try:

            while len(packets) < n_packets_expected:
                data = sock_in.recv(recv_buffer_size)
                if not data:
                    break

                if n_packets_expected == -1:
                    n_packets_expected = int(data)
                    print("Expecting %d packets" % n_packets_expected)


        except KeyboardInterrupt:

        all_hosts_expected_n_packets = {}
        packet_n_latency_tuples = {}

        first_packet = True

        try:
            while not self.all_clients_all_packets_received(packet_n_latency_tuples, all_hosts_expected_n_packets):
                data = sock_in.recv(recv_buffer_size)
                if not data:
                    break
                data = data.decode()

                if first_packet:
                    timeout_seconds = 15
                    sock_in.settimeout(timeout_seconds)
                first_packet = False

                if len(data) < 128:
                    (host_id, expected_n_packets) = [int(x) for x in data.split(' ')]
                    print("Expecting %d packets from host %d" % (expected_n_packets, host_id))
                    packet_n_latency_tuples[host_id] = []
                    all_hosts_expected_n_packets[host_id] = expected_n_packets
                else:
                    counter_value_recv = logi_pi_timer.read_counter()
                    payload = data.rstrip('a')
                    (packet_n, counter_value_send, host_id) = \
                        [int(x) for x in payload.split(' ')]

                    delta = logi_pi_timer.counter_delta(counter_value_recv, counter_value_send)
                    latency_us = logi_pi_timer.counter_delta_to_us(delta)
                    packet_n_latency_tuples[host_id].append((packet_n, latency_us))
        except socket.timeout:
            print("Note: timed out waiting to receive packets")

        sock_in.close()

        for host_id in packet_n_latency_tuples.keys():
            print("Received %d packets from host %d" % (len(packet_n_latency_tuples[host_id]), host_id))

        for host_id in packet_n_latency_tuples.keys():
            host_filename = self.test_output_filename + '_' + str(host_id)
            self.save_packet_latencies(packet_n_latency_tuples[host_id], all_hosts_expected_n_packets[host_id], host_filename)


    @staticmethod
    def all_clients_all_packets_received(packets, expected_n_packets):
        """
        Decide whether or not we've received all the packets we're expecting
        from all of the hosts that are sending packets.
        """
        if len(packets) == 0:
            return False

        all_received = True
        for host_id in packets:
            if len(packets[host_id]) != expected_n_packets[host_id]:
                all_received = False
        return all_received
