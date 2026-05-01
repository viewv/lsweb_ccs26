# Changes 2023 by Thomas Helbrecht
from __future__ import print_function
import json
from generator import generate_exploit_for_finding
from examples.EXAMPLE1 import EXAMPLE1
from pprint import pprint
from config import CONFIG

def main():
    # Start exploit generation from passed finding
    filearg = open(CONFIG.finding, 'r')
    file = filearg.read()
    finding = json.loads(file)
    exploits = generate_exploit_for_finding(finding)
    # Convert generated exploits to json
    json_object = json.dumps(exploits, separators=(',', ':')) 
    # Output json for consumation by backend
    print("[result]" + json_object)
if __name__ == '__main__':
    main()
