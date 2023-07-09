from dataclasses import asdict

from ansible_collections.karlivory.zk.plugins.module_utils.model import VMNetwork
from ansible_collections.karlivory.zk.plugins.modules.get_dangling_nics import (
    DanglingNic,
    ModuleArgs,
    Output,
    get_dangling_nics,
)


# test with sample example_vars.yml file in project root dir
def test_get_dangling_nics_simple():
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
      <address type='pci' domain='0x0000' bus='0x0a' slot='0x00' function='0x0' />
    </interface>
    <interface type='bridge'>
      <mac address='52:54:00:00:93:8c' />
      <address type='pci' domain='0x0000' bus='0x08' slot='0x00' function='0x0' />
    </interface>
  </devices>
</domain>
    """
    expected_result = Output(
        nics=[DanglingNic(mac="52:54:00:00:93:8c", nic_type="bridge", nic_bus=8)]
    )
    result = get_dangling_nics(ModuleArgs(dumpxml, networks))
    print(result.output)

    assert result.output == asdict(expected_result)
