from dataclasses import asdict

from ansible_collections.karlivory.zk.plugins.module_utils.model import (
    Disk, VMNetwork)
from ansible_collections.karlivory.zk.plugins.modules.compare_vm_state import (
    DanglingDisk, ModuleArgs, Output, VMXMLProcessor)


def test_no_disks_to_add():
    disks = [
        Disk(name="testvm1-root", size="10G", dev="vda", zfs=None),
        Disk(name="testvm1-data", size="10G", dev="vdb", zfs=None),
    ]
    dumpxml = """
<domain type='kvm'>
  <devices>
    <disk type='block' device='disk'>
      <driver name='qemu' type='raw' cache='none' io='native'/>
      <source dev='/dev/zvol/zroot/zk/testvm1-root' index='1'/>
      <backingStore/>
      <target dev='vda' bus='virtio'/>
      <alias name='virtio-disk0'/>
      <address type='pci' domain='0x0000' bus='0x01' slot='0x00' function='0x0'/>
    </disk>
    <disk type='block' device='disk'>
      <driver name='qemu' type='raw' cache='none' io='native'/>
      <source dev='/dev/zvol/zroot/zk/testvm1-data' index='3'/>
      <backingStore/>
      <target dev='vdb' bus='virtio'/>
      <alias name='virtio-disk1'/>
      <address type='pci' domain='0x0000' bus='0x06' slot='0x00' function='0x0'/>
    </disk>
  </devices>
</domain>
    """
    expected_result = []
    xml_processor = VMXMLProcessor(dumpxml)
    result = xml_processor.get_disks_to_add(disks)
    assert result == expected_result


def test_one_disk_to_add():
    disks = [
        Disk(name="testvm1-root", size="10G", dev="vda", zfs=None),
        Disk(name="testvm1-data", size="10G", dev="vdb", zfs=None),
    ]
    dumpxml = """
<domain type='kvm'>
  <devices>
    <disk type='block' device='disk'>
      <driver name='qemu' type='raw' cache='none' io='native'/>
      <source dev='/dev/zvol/zroot/zk/testvm2-root' index='1'/>
      <backingStore/>
      <target dev='vda' bus='virtio'/>
      <alias name='virtio-disk0'/>
      <address type='pci' domain='0x0000' bus='0x01' slot='0x00' function='0x0'/>
    </disk>
  </devices>
</domain>
    """
    expected_result = [disks[1]]
    xml_processor = VMXMLProcessor(dumpxml)
    result = xml_processor.get_disks_to_add(disks)
    assert result == expected_result
