"""
       Dual Band Performance Test : NAT Mode
       pytest -m "dual_band_test and nat"


"""

import os
import allure
import pytest

pytestmark = [pytest.mark.dual_band_test, pytest.mark.nat,
              pytest.mark.usefixtures("setup_test_run")]

setup_params_general = {
    "mode": "NAT",
    "ssid_modes": {
        "open": [{"ssid_name": "ssid_open_2g", "appliedRadios": ["is2dot4GHz"]},
                 {"ssid_name": "ssid_open_5g", "appliedRadios": ["is5GHzU", "is5GHz", "is5GHzL"]}]},
    "rf": {},
    "radius": False
}


@pytest.mark.dual_band_test
@pytest.mark.wifi5
@pytest.mark.wifi6
@pytest.mark.parametrize(
    'setup_profiles',
    [setup_params_general],
    indirect=True,
    scope="class"
)

@pytest.mark.usefixtures("setup_profiles")
class TestDualbandPerformanceNat(object):
    """
        pytest -m "dual_band_test and nat and open and twog  and fiveg"
    """

    @pytest.mark.open
    @pytest.mark.twog
    @pytest.mark.fiveg
    def test_client_open(self,get_vif_state,create_lanforge_chamberview_dut, lf_test,get_configuration):
        profile_data = setup_params_general["ssid_modes"]["open"]
        ssid_2G = profile_data[0]["ssid_name"]
        ssid_5G = profile_data[1]["ssid_name"]
        dut_name = create_lanforge_chamberview_dut
        mode = "NAT"
        vlan = 1
        if ssid_2G and ssid_5G not in get_vif_state:
            allure.attach(name="retest,vif state ssid not available:", body=str(get_vif_state))
            pytest.xfail("SSID's NOT AVAILABLE IN VIF STATE")

        dbpt_obj = lf_test.dualbandperformancetest(mode=mode,ssid_2G=ssid_2G,ssid_5G=ssid_5G,
                                   instance_name="dbp_instance_open_nat",
                                   vlan_id=vlan, dut_name=dut_name)
        report_name = dbpt_obj.report_name[0]['LAST']["response"].split(":::")[1].split("/")[-1]
        entries = os.listdir("../reports/" + report_name + '/')
        pdf = False
        for i in entries:
            if ".pdf" in i:
                pdf = i
        if pdf:
            allure.attach.file(source="../reports/" + report_name + "/" + pdf,
                               name=get_configuration["access_point"][0]["model"] + "_dualbandperfomance")

