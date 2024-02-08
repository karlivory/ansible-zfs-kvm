from dataclasses import asdict

from ansible_collections.karlivory.zk.plugins.module_utils.model import (
    Disk, VMNetwork)
from ansible_collections.karlivory.zk.plugins.modules.compare_vm_state import (
    DanglingDisk, ModuleArgs, Output, VMXMLProcessor)


def test_no_update():
    vcpus = 1
    dumpxml = """
<domain type='kvm'>
  <name>testvm1</name>
  <vcpu>1</vcpu>
  <cpu mode="host-passthrough" check="none" migratable="on"/>
  <os>
    <boot dev="hd"/>
  </os>
</domain>
    """
    assert not VMXMLProcessor(dumpxml).get_update_vcpus(vcpus)


def test_update():
    vcpus = 2
    dumpxml = """
<domain type='kvm'>
  <name>testvm1</name>
  <vcpu>1</vcpu>
  <cpu mode="host-passthrough" check="none" migratable="on"/>
  <os>
    <boot dev="hd"/>
  </os>
</domain>
    """
    assert VMXMLProcessor(dumpxml).get_update_vcpus(vcpus)
