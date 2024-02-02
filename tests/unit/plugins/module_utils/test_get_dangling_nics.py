from dataclasses import asdict

from ansible_collections.karlivory.zk.plugins.module_utils.model import \
    VMNetwork
from ansible_collections.karlivory.zk.plugins.modules.get_dangling_nics import (
    DanglingNic, ModuleArgs, Output, get_dangling_nics)


def test_no_dangling_nics():
    networks = [
        VMNetwork(
            name="A",
            subnet="0.0.0.0/0",
            netplan={},
            nic_bus=3,
            nic_type="bridge",
            nic_device_model="virtio",
            nic_source="virbr0",
        ),
        VMNetwork(
            name="B",
            subnet="0.0.0.0/0",
            netplan={},
            nic_bus=4,
            nic_type="bridge",
            nic_device_model="virtio",
            nic_source="virbr1",
        ),
    ]
    dumpxml = """
<domain type='kvm' id='2'>
  <devices>
    <interface type='bridge'>
      <mac address='52:54:00:ba:58:d3' />
      <address type='pci' domain='0x0000' bus='3' slot='0x00' function='0x0' />
    </interface>
    <interface type='bridge'>
      <mac address='52:54:00:00:93:8c' />
      <address type='pci' domain='0x0000' bus='4' slot='0x00' function='0x0' />
    </interface>
  </devices>
</domain>
    """
    expected_result = Output(nics=[])
    result = get_dangling_nics(ModuleArgs(dumpxml, networks))

    assert result.output == asdict(expected_result)


def test_one_dangling_nic():
    networks = [
        VMNetwork(
            name="A",
            subnet="0.0.0.0/0",
            netplan={},
            nic_bus=10,
            nic_type="bridge",
            nic_device_model="virtio",
            nic_source="virbr0",
        )
    ]
    dumpxml = """
<domain type='kvm' id='2'>
  <devices>
    <interface type='bridge'>
      <mac address='52:54:00:ba:58:d3' />
      <address type='pci' domain='0x0000' bus='10' slot='0x00' function='0x0' />
    </interface>
    <interface type='bridge'>
      <mac address='52:54:00:00:93:8c' />
      <address type='pci' domain='0x0000' bus='8' slot='0x00' function='0x0' />
    </interface>
  </devices>
</domain>
    """
    expected_result = Output(
        nics=[DanglingNic(mac="52:54:00:00:93:8c", nic_type="bridge", nic_bus=8)]
    )
    result = get_dangling_nics(ModuleArgs(dumpxml, networks))

    assert result.output == asdict(expected_result)
