from dataclasses import asdict

from ansible_collections.karlivory.zk.plugins.module_utils.model import (
    Disk, VMNetwork)
from ansible_collections.karlivory.zk.plugins.modules.compare_vm_state import (
    DanglingDisk, ModuleArgs, Output, VMXMLProcessor)


def test_no_update():
    memory_mb = 2000
    dumpxml = """
<domain type='kvm'>
  <name>testvm1</name>
  <currentMemory unit="KiB">2048000</currentMemory>
  <os>
    <boot dev="hd"/>
  </os>
</domain>
    """
    assert not VMXMLProcessor(dumpxml).get_update_memory(memory_mb)


def test_update():
    memory_mb = 3000
    dumpxml = """
<domain type='kvm'>
  <name>testvm1</name>
  <currentMemory unit="KiB">2048000</currentMemory>
  <os>
    <boot dev="hd"/>
  </os>
</domain>
    """
    assert VMXMLProcessor(dumpxml).get_update_memory(memory_mb)
