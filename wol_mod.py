import socket
import struct

def wake(mac: str):

    clean_mac = mac.replace(":", "").replace(".", "").replace("-", "")

    if len(clean_mac) != 12:
        return False

    data = ''.join(['FFFFFFFFFFFF', clean_mac * 20])
    send_data = b''

    for i in range(0, len(data), 2):
        send_data = b''.join([send_data, struct.pack('B', int(data[i: i + 2], 16))])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(send_data, ('<broadcast>', 7))
    return True
