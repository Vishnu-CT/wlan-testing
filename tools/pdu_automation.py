import os
import pprint
import time
import argparse
from typing import Sequence
from typing import Optional

try:
    import dlipower
except:
    print('Please wait we are installing DLI Power')
    os.system('pip install dlipower')


class setup:
    def __init__(self, hostname, user, password):
        self.hostname = hostname
        self.user = user
        self.password = password
        self.power_switch = dlipower.PowerSwitch(hostname=self.hostname, userid=self.user, password=self.password)


class switch_on(setup):
    def __init__(self, hostname, user, password, port=None):
        super().__init__(hostname, user, password)
        self.port = port
        # print(self.power_switch)
        if self.port != None:
            # String Manupulation
            self.power_switch[int(self.port)-1].state = "ON"
        else:
            for outlet in self.power_switch:
                outlet.state = 'ON'


class switch_off(setup):
    def __init__(self, hostname, user, password, port=None):
        super().__init__(hostname, user, password)
        self.port = port
        if self.port != None:
            self.power_switch[int(self.port)-1].state = "OFF"
        else:
            for outlet in self.power_switch:
                outlet.state = 'OFF'


def main(argv: Optional[Sequence[str]]=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Please provide host name eg: 192.168.200.65')
    parser.add_argument('--username', help='Please provide username eg: admin')
    parser.add_argument('--password', help='Please provide password eg: 1234')
    parser.add_argument('--action', help='Switches all Outlets in ON Mode eg: --on_all\n'
                                         'Switches all Outlets in OFF Mode eg: --off_all\n'
                                         'Cycle all Outlets in OFF Mode and then ON Mode eg: --cycle_all\n'
                                         'Switches the target Outlets in ON Mode eg: --on\n'
                                         'Switches the target Outlets in OFF Mode --off\n')
    parser.add_argument('--port', help='Please provide port name eg: --port lanforge')
    args = parser.parse_args(argv)
    dic = vars(args)
    # print(dic)
    if dic['action'] == 'on_all':
        set = setup(dic['host'], dic['username'], dic['password'])
        on = switch_on(dic['host'], dic['username'], dic['password'])
    elif dic['action'] == 'off_all':
        set = setup(dic['host'], dic['username'], dic['password'])
        off = switch_off(dic['host'], dic['username'], dic['password'])
    elif dic['action'] == 'on':
        set = setup(dic['host'], dic['username'], dic['password'])
        on = switch_on(dic['host'], dic['username'], dic['password'], dic['port'])
        # off = switch_on(dic['action'])
    elif dic['action'] == 'off':
        set = setup(dic['host'], dic['username'], dic['password'])
        on = switch_off(dic['host'], dic['username'], dic['password'], dic['port'])
        # off = switch_on(dic['action'])
    elif dic['action'] == 'cycle_all':
        set = setup(dic['host'], dic['username'], dic['password'])
        off = switch_off(dic['host'], dic['username'], dic['password'])
        on = switch_on(dic['host'], dic['username'], dic['password'])
    elif dic['action'] == 'cycle':
        set = setup(dic['host'], dic['username'], dic['password'])
        on = switch_off(dic['host'], dic['username'], dic['password'], dic['port'])
        off = switch_on(dic['host'], dic['username'], dic['password'], dic['port'])
    else:
        print('Command not found')


if __name__ == '__main__':
    main()

