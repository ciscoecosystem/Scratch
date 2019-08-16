import subprocess
import os

def main():

    consumer = subprocess.Popen(["python", "-m", "code.app.app"])
    # connector = subprocess.Popen(["python", "-m", "snow-table-parser.aurora_snow_connector"])

    consumer.wait()
    # connector.wait()

if __name__ == '__main__':
    main()
