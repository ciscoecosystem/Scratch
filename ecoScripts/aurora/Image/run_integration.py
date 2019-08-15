import subprocess
import os

def main():

    consumer = subprocess.Popen(["python", "-m", "app.app"])
    connector = subprocess.Popen(["python", "snow-table-parser/aurora_snow_connector.py"])

    consumer.wait()
    connector.wait()

if __name__ == '__main__':
    main()
