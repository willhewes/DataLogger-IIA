# gui_test.py
import socket
import tkinter as tk
import threading

HOST = 'localhost'
PORT = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# GUI
root = tk.Tk()
root.title("Environment Monitoring - Simulation")

temperature_label = tk.Label(root, text="Temperature: -- °C", font=("Arial", 16))
temperature_label.pack(pady=10)

moisture_label = tk.Label(root, text="Soil: --", font=("Arial", 16))
moisture_label.pack(pady=10)

def read_socket():
    buffer = ""
    while True:
        try:
            data = client.recv(1024).decode('utf-8')
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if line.startswith("T:"):
                    parts = line.strip().split()
                    temp_str = parts[0][2:]
                    moisture_str = parts[1][2:]
                    temperature_label.config(text=f"Temperature: {temp_str} °C")
                    moisture_label.config(text=f"Soil mositure: {moisture_str}")
        except Exception as e:
            print("Error:", e)
            break

threading.Thread(target=read_socket, daemon=True).start()
root.mainloop()
