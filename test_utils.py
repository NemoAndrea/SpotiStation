from prettytable import PrettyTable

def print_progress(devices, clear=False):
    tab = PrettyTable(["Device", "Instructions", "Progress", "OK?"])
    
    for device in devices:
        devicestate = list(device.values())
        if devicestate[3]:
            devicestate[3]="OK!"
        else:
            devicestate[3]=""
        tab.add_row(devicestate)
    if clear:
        clear_line(n=len(devices)+4)
    print(tab)

def clear_line(n=1):
    LINE_UP = '\033[1A'
    LINE_CLEAR = '\x1b[2K'
    for i in range(n):
        print(LINE_UP, end=LINE_CLEAR)
