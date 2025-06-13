import subprocess
import sys

if __name__ == "__main__":
    logging = input("For live data, press 1. For live plotting, press 2: ").strip()

    processes = []

    try:
        if logging == "1":
            processes.append(subprocess.Popen(["python", "Python/Legacy/sender.py"]))
            processes.append(subprocess.Popen(["python", "Python/Legacy/receiver.py"]))
        elif logging == "2":
            processes.append(subprocess.Popen(["python", "Python/Legacy/sender.py"]))
            processes.append(subprocess.Popen(["python", "Python/Legacy/plot.py"]))
        else:
            print("No valid option selected.")
            sys.exit(0)

        # Wait for the first one to finish
        while True:
            for p in processes:
                if p.poll() is not None:  # Process has ended
                    raise KeyboardInterrupt
    except KeyboardInterrupt:
        print("\nShutting down...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        sys.exit(0)
