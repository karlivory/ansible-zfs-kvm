from dataclasses import asdict

from ansible_collections.karlivory.zk.plugins.module_utils.model import (
    Disk, VMNetwork)
from ansible_collections.karlivory.zk.plugins.modules.compare_vm_state import (
    DanglingNic, ModuleArgs, Output, VMXMLProcessor)


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
<domain type='kvm'>
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
    xml_processor = VMXMLProcessor(dumpxml)
    expected_result = []
    result = xml_processor.get_dangling_nics(networks)
    assert result == expected_result


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
<domain type='kvm'>
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
    expected_result = [
        DanglingNic(mac="52:54:00:00:93:8c", nic_type="bridge", nic_bus=8)
    ]
    xml_processor = VMXMLProcessor(dumpxml)
    result = xml_processor.get_dangling_nics(networks)
    assert result == expected_result
