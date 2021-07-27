"""
APNOS Library : Used to execute SSH Commands in AP Using Direct-AP-SSH/ Jumphost-Serial Console

Currently Having Methods:
    1. Get iwinfo
    2. AP Manager Satus
    3. Vif Config ssid's
    4. Vif State ssid's
    5. Get current Firmware

"""
import json

import paramiko
from scp import SCPClient
import os
import allure


class APNOS:

    def __init__(self, credentials=None, pwd=os.getcwd(), sdk="1.x"):
        allure.attach(name="APNOS LIbrary: ", body=str(credentials))
        self.serial = credentials['serial']
        self.owrt_args = "--prompt root@OpenAp -s serial --log stdout --user root --passwd openwifi"
        self.sdk = sdk
        if sdk == "2.x":
            self.owrt_args = "--prompt root@" + self.serial + " -s serial --log stdout --user root --passwd openwifi"
        if credentials is None:
            print("No credentials Given")
            exit()
        self.ip = credentials['ip']  # if mode=1, enter jumphost ip else ap ip address
        self.username = credentials['username']  # if mode=1, enter jumphost username else ap username
        self.password = credentials['password']  # if mode=1, enter jumphost password else ap password
        self.port = credentials['port']  # if mode=1, enter jumphost ssh port else ap ssh port
        self.mode = credentials['jumphost']  # 1 for jumphost, 0 for direct ssh
        if self.mode:
            self.tty = credentials['jumphost_tty']  # /dev/ttyAP1
            client = self.ssh_cli_connect()
            cmd = '[ -f ~/cicd-git/ ] && echo "True" || echo "False"'
            stdin, stdout, stderr = client.exec_command(cmd)
            output = str(stdout.read())
            print(output)
            if output.__contains__("False"):
                cmd = 'mkdir ~/cicd-git/'
                stdin, stdout, stderr = client.exec_command(cmd)
            cmd = '[ -f ~/cicd-git/openwrt_ctl.py ] && echo "True" || echo "False"'
            stdin, stdout, stderr = client.exec_command(cmd)
            output = str(stdout.read())
            if output.__contains__("False"):
                print("Copying openwrt_ctl serial control Script...")
                with SCPClient(client.get_transport()) as scp:
                    scp.put(pwd + '/openwrt_ctl.py', '~/cicd-git/openwrt_ctl.py')  # Copy my_file.txt to the server
            cmd = '[ -f ~/cicd-git/openwrt_ctl.py ] && echo "True" || echo "False"'
            stdin, stdout, stderr = client.exec_command(cmd)
            var = str(stdout.read())
            if var.__contains__("True"):
                allure.attach(name="openwrt_ctl Setup", body=str(var))
                print("APNOS Serial Setup OK")
            else:
                allure.attach(name="openwrt_ctl Setup", body=str(var))
                print("APNOS Serial Setup Fail")

    # Method to connect AP-CLI/ JUMPHOST-CLI
    def ssh_cli_connect(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("Connecting to jumphost: %s@%s:%s" % (
            self.username, self.ip, self.port))
        client.connect(self.ip, username=self.username, password=self.password,
                       port=self.port, timeout=10, allow_agent=False, banner_timeout=200)

        return client

    def reboot(self):
        client = self.ssh_cli_connect()

        cmd = "reboot"
        if self.mode:
            cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                  f"cmd --value \"{cmd}\" "
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read()
        client.close()
        allure.attach(name="AP Reboot", body=str(output))
        return output

    # Method to get the iwinfo status of AP using AP-CLI/ JUMPHOST-CLI

    def get_bssid_band_mapping(self):
        client = self.ssh_cli_connect()
        cmd = 'iwinfo'
        if self.mode:
            cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                  f"cmd --value \"{cmd}\" "
        stdin, stdout, stderr = client.exec_command(cmd)
        data = stdout.read()
        client.close()
        allure.attach(name="iwinfo Output Msg: ", body=str(data))
        allure.attach(name="iwinfo config Err Msg: ", body=str(stderr))
        data = str(data).replace(" ", "").split("\\r\\n")
        band_info = []
        for i in data:
            tmp = []
            if i.__contains__("AccessPoint"):
                bssid = i.replace("AccessPoint:", "")
                tmp.append(bssid.casefold())
            elif i.__contains__("MasterChannel"):
                if i.split(":")[2].__contains__("2.4"):
                    tmp.append("2G")
                else:
                    tmp.append("5G")
            else:
                tmp = []
            if tmp != []:
                band_info.append(tmp)
        bssi_band_mapping = {}
        for i in range(len(band_info)):
            if (i % 2) == 0:
                bssi_band_mapping[band_info[i][0]] = band_info[i + 1][0]
        return bssi_band_mapping

    # Method to get the vif_config of AP using AP-CLI/ JUMPHOST-CLI
    def get_vif_config(self):
        client = self.ssh_cli_connect()
        cmd = "/usr/opensync/bin/ovsh s Wifi_VIF_Config -c"
        if self.mode:
            cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                  f"cmd --value \"{cmd}\" "
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read()
        client.close()
        allure.attach(name="vif config Output Msg: ", body=str(output))
        allure.attach(name="vif config Err Msg: ", body=str(stderr))

        return output

    # Method to get the vif_state of AP using AP-CLI/ JUMPHOST-CLI
    def get_vif_state(self):
        client = self.ssh_cli_connect()
        cmd = "/usr/opensync/bin/ovsh s Wifi_VIF_State -c"
        if self.mode:
            cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                  f"cmd --value \"{cmd}\" "
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read()
        client.close()
        allure.attach(name="vif state Output Msg: ", body=str(output))
        allure.attach(name="vif state Err Msg: ", body=str(stderr))
        return output

    # Method to get the vif_config ssid's of AP using AP-CLI/ JUMPHOST-CLI
    def get_vif_config_ssids(self):
        stdout = self.get_vif_config()
        ssid_list = []
        for i in stdout.splitlines():
            ssid = str(i).replace(" ", "").split(".")
            if ssid[0].split(":")[0] == "b'ssid":
                ssid_list.append(ssid[0].split(":")[1].replace("'", ""))
        allure.attach(name="get_vif_config_ssids ", body=str(ssid_list))
        return ssid_list

    # Method to get the vif_state ssid's of AP using AP-CLI/ JUMPHOST-CLI
    def get_ssid_info(self):
        stdout = self.get_vif_state()
        ssid_info_list = []
        info = []
        for i in stdout.splitlines():
            ssid = str(i).replace(" ", "").split(".")
            # print(ssid)
            if ssid[0].split(":")[0] == "b'mac":
                mac_info_list = ssid[0].split(":")
                mac_info_list.pop(0)
                info.append(":".join(mac_info_list).replace("'", ""))
            if ssid[0].split(":")[0] == "b'security":
                security = ssid[0].split(":")[1].split(",")[2].replace("]", "").replace('"', "").replace("'", "")
                print(ssid[0].split(":")[1])
                if security != "OPEN":
                    if security == "WPA-PSK":
                        if ssid[0].split(":")[1].split(",")[6].__contains__("1"):
                            info.append("WPA")
                            security_key = ssid[0].split(":")[1].split(",")[4].replace('"', "").replace("]", "")
                        if ssid[0].split(":")[1].split(",")[6].__contains__("2"):
                            info.append("WPA2")
                            security_key = ssid[0].split(":")[1].split(",")[4].replace('"', "").replace("]", "")
                        if ssid[0].split(":")[1].split(",")[6].__contains__("mixed"):
                            info.append("WPA | WPA2")
                            security_key = ssid[0].split(":")[1].split(",")[4].replace('"', "").replace("]", "")
                    if security == "WPA-SAE":
                        if ssid[0].split(":")[1].split(",")[6].__contains__("3"):
                            info.append("WPA3_PERSONAL")
                            security_key = ssid[0].split(":")[1].split(",")[4].replace('"', "").replace("]", "")
                        if ssid[0].split(":")[1].split(",")[6].__contains__("mixed"):
                            info.append("WPA3_PERSONAL")
                            security_key = ssid[0].split(":")[1].split(",")[4].replace('"', "").replace("]", "")
                    if security == "WPA-EAP":
                        info.append("EAP-TTLS")
                        security_key = ssid[0].split(":")[1].split(",")[4].replace('"', "").replace("]", "")
                    if security == "WPA3-EAP":
                        info.append("EAP-TTLS")
                        security_key = ssid[0].split(":")[1].split(",")[4].replace('"', "").replace("]", "")
                    else:
                        security_key = ssid[0].split(":")[1].split(",")[4].replace('"', "").replace("]", "")
                    info.append(security_key)
                else:
                    info.append("OPEN")
            if ssid[0].split(":")[0] == "b'ssid":
                info.append(ssid[0].split(":")[1].replace("'", ""))
                ssid_info_list.append(info)
                info = []
        print(ssid_info_list)
        # allure.attach(name="get_vif_state_ssids ", body=str(ssid_list))
        return ssid_info_list

    # Get VIF State parameters
    def get_vif_state_ssids(self):
        stdout = self.get_vif_state()
        ssid_list = []
        for i in stdout.splitlines():
            ssid = str(i).replace(" ", "").split(".")
            if ssid[0].split(":")[0] == "b'ssid":
                ssid_list.append(ssid[0].split(":")[1].replace("'", ""))
        allure.attach(name="get_vif_state_ssids ", body=str(ssid_list))
        return ssid_list

    # Method to get the active firmware of AP using AP-CLI/ JUMPHOST-CLI
    def get_active_firmware(self):
        try:
            client = self.ssh_cli_connect()
            cmd = '/usr/opensync/bin/ovsh s AWLAN_Node -c | grep FW_IMAGE_ACTIVE'
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty}" \
                      f" --action cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read()
            # print(output)
            version_matrix = str(output.decode('utf-8').splitlines())
            version_matrix_split = version_matrix.partition('FW_IMAGE_ACTIVE","')[2]
            cli_active_fw = version_matrix_split.partition('"],[')[0]
            client.close()
        except Exception as e:
            print(e)
            allure.attach(name="get_active_firmware - Exception ", body=str(e))
            cli_active_fw = "Error"
        allure.attach(name="get_active_firmware ", body=str(cli_active_fw))
        return cli_active_fw

    # Method to get the manager state of AP using AP-CLI/ JUMPHOST-CLI
    def get_manager_state(self):
        try:
            client = self.ssh_cli_connect()
            cmd = '/usr/opensync/bin/ovsh s Manager -c | grep status'
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty}" \
                      f" --action cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read()
            status = str(output.decode('utf-8').splitlines())
            # print(output, stderr.read())
            client.close()
        except Exception as e:
            print(e)
            allure.attach(name="get_active_firmware - Exception ", body=str(e))
            status = "Error"
        allure.attach(name="get_active_firmware ", body=str(status))
        return status

    def get_serial_number(self):
        try:
            client = self.ssh_cli_connect()
            cmd = "node | grep serial_number"
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                      f"cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read()
            output = output.decode('utf-8').splitlines()
            allure.attach(name="get_serial_number output ", body=str(stderr))
            serial = output[1].replace(" ", "").split("|")[1]
            client.close()
        except Exception as e:
            print(e)
            allure.attach(name="get_serial_number - Exception ", body=str(e))
            serial = "Error"
        allure.attach(name="get_serial_number ", body=str(serial))
        return serial

    def get_redirector(self):
        try:
            client = self.ssh_cli_connect()
            cmd = "node | grep redirector_addr"
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                      f"cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read()
            print(output, stderr.read())
            status = output.decode('utf-8').splitlines()
            allure.attach(name="get_redirector output ", body=str(stderr))
            redirector = status[1].replace(" ", "").split("|")[1]
            client.close()
        except Exception as e:
            print(e)
            allure.attach(name="get_redirector - Exception ", body=str(e))
            redirector = "Error"
        allure.attach(name="get_redirector ", body=redirector)
        return redirector

    def run_generic_command(self, cmd=""):
        try:
            client = self.ssh_cli_connect()
            cmd = cmd
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                      f"cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read()
            print(output, stderr.read())
            status = output.decode('utf-8').splitlines()
            allure.attach(name="get_redirector output ", body=str(stderr))
            client.close()
        except Exception as e:
            print(e)
            allure.attach(name="get_redirector - Exception ", body=str(e))
            status = "Error"
        allure.attach(name="get_redirector ", body=status)
        return status

    def get_ucentral_status(self):
        try:
            client = self.ssh_cli_connect()
            cmd = "ubus call ucentral status"
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                      f"cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read()
            # print(output, stderr.read())
            connected = False
            if "connected" in output.decode('utf-8').splitlines()[2]:
                connected = True
            # connected = output.decode('utf-8').splitlines()[2]
            latest = output.decode('utf-8').splitlines()[3].split(":")[1].replace(" ", "").replace(",", "")
            active = output.decode('utf-8').splitlines()[4].split(":")[1].replace(" ", "").replace(",", "")
            client.close()
            allure.attach(name="ubus call ucentral status ", body=str(connected) + "\n" + latest + "\n" + active)
        except Exception as e:
            print(e)
            allure.attach(name="Exception ", body=str(e))
            connected, latest, active = "Error", "Error", "Error"
            allure.attach(name="ubus call ucentral status ", body=str(connected) + "\n" + latest + "\n" + active)
        return connected, latest, active

    def get_uc_latest_config(self):
        try:
            connected, latest, active = self.get_ucentral_status()
            client = self.ssh_cli_connect()
            cmd = "cat /etc/ucentral/ucentral.cfg." + latest
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                      f"cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode('utf-8').splitlines()[1]
            json_output = json.loads(output)  # , sort_keys=True)
            print(type(json_output))
            client.close()
        except Exception as e:
            json_output = {}
            print(e)
        return json_output

    def get_uc_active_config(self):
        try:
            connected, latest, active = self.get_ucentral_status()
            client = self.ssh_cli_connect()
            cmd = "cat /etc/ucentral/ucentral.cfg." + active
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                      f"cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode('utf-8').splitlines()[1]
            json_output = json.loads(output)  # , sort_keys=True)
            print(json_output)
            client.close()
        except Exception as e:
            json_output = {}
            print(e)
        return json_output

    def get_interface_details(self):
        r = self.get_wifi_status()
        print(r)
        wifi_info = {}
        if self.sdk == "1.x":
            for i in r:
                for j in r[i]["interfaces"]:
                    encryption = j["config"]["encryption"]
                    if encryption == "psk" or encryption == "psk2" or encryption == "psk-mixed" or \
                            encryption == "sae" or encryption == "sae-mixed":
                        wifi_info[j["ifname"]] = [j["config"]["ssid"], j["config"]["encryption"], j["config"]["key"]]
                    else:
                        wifi_info[j["ifname"]] = [j["config"]["ssid"], j["config"]["encryption"], ""]
            print(wifi_info)
            data = self.get_iwinfo()
            for i in wifi_info.keys():
                wifi_info[i].append(data[i])

            return wifi_info
        if self.sdk == "2.x":
            for i in r:
                for j in r[i]["interfaces"]:
                    encryption = j["config"]["encryption"]
                    if encryption == "psk" or encryption == "psk2" or encryption == "psk-mixed" or \
                       encryption == "sae" or encryption == "sae-mixed":
                        wifi_info[j["ifname"]] = [j["config"]["ssid"], j["config"]["encryption"], j["config"]["key"]]
                    else:
                        wifi_info[j["ifname"]] = [j["config"]["ssid"], j["config"]["encryption"], ""]
            data = self.get_iwinfo()
            print(wifi_info)
            print(data)
            for i in wifi_info.keys():
                wifi_info[i].append(data[i])
            return wifi_info

    def get_wifi_status(self):
        try:

            client = self.ssh_cli_connect()
            cmd = "wifi status"
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                      f"cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)

            output = stdout.read().decode('utf-8')
            data = output.split()
            data.pop(0)
            data.pop(0)
            data.pop(0)
            OUT = "".join(data)
            json_output = json.loads(OUT)
            client.close()
        except Exception as e:
            json_output = False
            print(e)
        return json_output

    def get_iwinfo(self):
        try:

            client = self.ssh_cli_connect()
            cmd = "iwinfo"
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                      f"cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().replace(b":~# iwinfo", b"").decode('utf-8')
            o = output.split()
            iwinfo_bssid_data = {}
            for i in range(len(o)):
                if o[i].__contains__("ESSID"):
                    if o[i + 9].__contains__("2.4"):
                        band = "2G"
                    else:
                        band = "5G"
                    iwinfo_bssid_data[o[i - 1]] = [o[i + 4], band]
            client.close()
        except Exception as e:
            iwinfo_bssid_data = False
            print(e)
        return iwinfo_bssid_data

    def logread(self):
        try:
            client = self.ssh_cli_connect()
            cmd = "logread"
            if self.mode:
                cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                      f"cmd --value \"{cmd}\" "
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read()
            status = output.decode('utf-8').splitlines()
            logread = status
            logs = ""
            for i in logread:
                logs = logs + i + "\n"
            client.close()
        except Exception as e:
            print(e)
            logs = ""
        return logs

    def get_vifc(self):
        client = self.ssh_cli_connect()
        cmd = "vifC"
        if self.mode:
            cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                  f"cmd --value \"{cmd}\" "
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read()
        client.close()
        allure.attach(name="vif state Output Msg: ", body=str(output))
        allure.attach(name="vif state Err Msg: ", body=str(stderr))
        return output

    def get_vifs(self):
        client = self.ssh_cli_connect()
        cmd = "vifS"
        if self.mode:
            cmd = f"cd ~/cicd-git/ && ./openwrt_ctl.py {self.owrt_args} -t {self.tty} --action " \
                  f"cmd --value \"{cmd}\" "
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read()
        client.close()
        allure.attach(name="vif state Output Msg: ", body=str(output))
        allure.attach(name="vif state Err Msg: ", body=str(stderr))
        return output

    def get_vlan(self):
        stdout = self.get_vifs()
        vlan_list = []
        for i in stdout.splitlines():
            vlan = str(i.strip()).replace("|", ".").split(".")
            try:
                if not vlan[0].find("b'vlan_id"):
                    vlan_list.append(vlan[1].strip())
            except:
                pass
        return vlan_list


if __name__ == '__main__':
    obj = {
        'model': 'ec420',
        'mode': 'wifi5',
        'serial': '001122090801',
        'jumphost': True,
        'ip': "10.28.3.100",
        'username': "lanforge",
        'password': "pumpkin77",
        'port': 22,
        'jumphost_tty': '/dev/ttyAP3',
        'version': "https://tip.jfrog.io/artifactory/tip-wlan-ap-firmware/uCentral/edgecore_eap102/20210625-edgecore_eap102-uCentral-trunk-4225122-upgrade.bin"
    }
    var = APNOS(credentials=obj, sdk="2.x")
    x = var.get_interface_details()
    print(x)
