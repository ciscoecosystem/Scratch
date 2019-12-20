import subprocess
import os
import json
import requests
from shlex import split
from pigeon import Pigeon

pigeon = Pigeon()


def main():
    pigeon.sendInfoMessage("Starting integration")

    
    subprocess.Popen(["sh", "install_avro.sh"]).wait()

    
    consumer = subprocess.Popen(["python", "-m", "integration.app"])   
    consumer.wait()
        


if __name__ == '__main__':
    main()
