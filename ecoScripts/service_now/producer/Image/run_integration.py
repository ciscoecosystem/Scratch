import subprocess
import os
import json
import requests
from shlex import split
from pigeon import Pigeon

pigeon = Pigeon()


def main():
    pigeon.sendInfoMessage("Starting Service now-kafka integration")




    
    connector = subprocess.Popen(["python", "-m", "integration.aurora_snow_connector"])
    connector.wait()


if __name__ == '__main__':
    main()
