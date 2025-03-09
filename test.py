import configparser
import os

config_path = "config.ini"

if not os.path.exists(config_path):
    print(f"Error: config.ini file not found in {os.getcwd()}")
else:
    config = configparser.ConfigParser()
    config.read(config_path)

    if 'email' in config:
        print("Email configuration loaded successfully.")
    else:
        print(" Error: Missing [email] section in config.ini")