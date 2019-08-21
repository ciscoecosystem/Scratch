import subprocess
import os

from pigeon import Pigeon

pigeon = Pigeon()

def main():
    pigeon.sendInfoMessage("Starting integration")
    consumer = subprocess.Popen(["python", "-m", "code.app.app"])
    connector = subprocess.Popen(["python", "-m", "code.snow-table-parser.aurora_snow_connector"])

    consumer.wait()
    connector.wait()

if __name__ == '__main__':
    main()
