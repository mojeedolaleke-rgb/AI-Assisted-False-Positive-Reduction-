# TEST FILE: Command Injection (CWE-78)
import os
import subprocess

def scan_host(host):
    # VULNERABLE: user input in os.system
    os.system("ping " + host)

def get_files(directory):
    # VULNERABLE: shell=True with user input
    result = subprocess.run("ls " + directory, shell=True, capture_output=True)
    return result.stdout
