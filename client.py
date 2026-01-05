import os
import socket
import pathlib
import time
ip = "10.0.0.116"
port = 4456
SIZE = 1024

def SendFile(thefile, ip, port):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ip, port))

        file = open(thefile, 'rb')
        filesize = os.path.getsize(thefile)
        filename = pathlib.Path(thefile)

        client.send(f"{filename}".encode())
        while True:
            data = client.recv(SIZE).decode()
            if data == "SENT":
                data = "wait"
                break
        client.send(str(filesize).encode())
        while True:
            data = client.recv(SIZE).decode()
            if data == "SENT":
                data = "wait"
                break

        data = file.read()
        client.sendall(data)
        while True:
            data = client.recv(SIZE).decode()
            if data == "SENT":
                data = "wait"
                break
        client.send(b"<END>")
        while True:
            data = client.recv(SIZE).decode()
            if data == "SENT":
                data = "wait"
                break
        print(f"File Sent : {thefile}")
        return True
    except Exception as e:
        print(f"Error Sending File: {e}")
        return False

if __name__ == "__main__":
    SendFile("inputs.txt", ip, port)
