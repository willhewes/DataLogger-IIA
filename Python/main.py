import subprocess

if __name__ == "__main__":
    # Prompt the user
    logging = input("For live data, press 1. For live plotting, press 2: ").strip()

    processes = []

    if logging == "1":
        processes.append(subprocess.Popen(["python", "Python/sender.py"]))
        processes.append(subprocess.Popen(["python", "Python/receiver.py"]))
    elif logging == "2":
        processes.append(subprocess.Popen(["python", "Python/sender.py"]))
        processes.append(subprocess.Popen(["python", "Python/serial_comms.py"]))
    else:
        print("No valid option selected.")
        exit()
