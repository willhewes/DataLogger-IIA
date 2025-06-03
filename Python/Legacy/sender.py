# arduino_simulator.py
import socket
import time
import random

HOST = 'localhost'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print("Arduino: waiting for connection...")
conn, addr = server.accept()
print("connected:", addr)

try:
    while True:
        temp = round(random.uniform(20.0, 30.0), 1)
        moisture = random.randint(300, 700)
        data = f"T:{temp} M:{moisture}\n"
        conn.sendall(data.encode('utf-8'))
        time.sleep(1)
except KeyboardInterrupt:
    print("END simulation")
finally:
    conn.close()
    server.close()
