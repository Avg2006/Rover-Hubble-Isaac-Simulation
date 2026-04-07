import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/avg/anveshak/Rover/Hubble/hubble_ws/install/master'
