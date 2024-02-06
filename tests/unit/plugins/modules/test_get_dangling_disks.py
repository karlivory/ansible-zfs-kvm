from dataclasses import asdict

from ansible_collections.karlivory.zk.plugins.module_utils.model import Disk
from ansible_collections.karlivory.zk.plugins.modules.get_dangling_disks import (
    DanglingDisk, ModuleArgs, Output, get_dangling_disks)


def test_no_dangling_disks():
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
    expected_result = Output(disks=[])
    result = get_dangling_disks(None, ModuleArgs(dumpxml, disks))
    assert result.output == asdict(expected_result)


def test_one_dangling_disk():
    disks = [
        Disk(name="testvm2-root", size="10G", dev="vda", zfs=None),
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
    <disk type='block' device='disk'>
      <driver name='qemu' type='raw' cache='none' io='native'/>
      <source dev='/dev/zvol/zroot/zk/testvm2-data' index='3'/>
      <backingStore/>
      <target dev='vdb' bus='virtio'/>
      <alias name='virtio-disk1'/>
      <address type='pci' domain='0x0000' bus='0x06' slot='0x00' function='0x0'/>
    </disk>
  </devices>
</domain>
    """
    expected_result = Output(disks=[DanglingDisk(dev="vdb")])
    result = get_dangling_disks(None, ModuleArgs(dumpxml, disks))
    assert result.output == asdict(expected_result)
