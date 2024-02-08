#!/usr/bin/python
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from typing import List

from ansible_collections.karlivory.zk.plugins.module_utils.model import (
    VM, Disk, VMNetwork)
from ansible_collections.karlivory.zk.plugins.module_utils.utils import (
    ModuleResult, Utils)


class InvalidUpdateException(Exception):
    pass


@dataclass
class ModuleArgs:
    dumpxml: str
    vm: VM


@dataclass
class DanglingDisk:
    dev: str


@dataclass
class DanglingNic:
    mac: str
    nic_type: str
    nic_bus: int


@dataclass
class Output:
    disks_to_add: List[Disk]
    nics_to_add: List[VMNetwork]
    dangling_disks: List[DanglingDisk]
    dangling_nics: List[DanglingNic]
    update_memory: bool
    update_vcpus: bool


def bus_string_to_int(n: str) -> int:
    if n.startswith("0x"):
        return int(n, 16)
    return int(n)


class VMXMLProcessor:
    def __init__(self, dumpxml: str):
        self.root = ET.fromstring(dumpxml)

    def get_dangling_disks(self, disks: List[Disk]) -> List[DanglingDisk]:
        result = []
        defined_disks = set(x.dev for x in disks)
        for disk in self.root.findall(".//devices/disk[@device='disk']/target"):
            dev = disk.get("dev")
            if dev and dev not in defined_disks:
                result.append(DanglingDisk(dev=dev))
        return result

    def get_dangling_nics(self, networks: List[VMNetwork]) -> List[DanglingNic]:
        result = []
        defined_bus_numbers = [n.nic_bus for n in networks]
        for interface in self.root.findall(".//devices/interface"):
            address = interface.find("address")
            assert (
                address is not None
            ), f"ERROR! interface {str(interface)} address is None"
            bus = address.get("bus")
            assert (
                bus is not None
            ), f"ERROR! interface {str(interface)} address.bus is None"
            bus = bus_string_to_int(bus)
            if bus not in defined_bus_numbers:
                mac = interface.find("mac")
                assert mac is not None, f"ERROR! interface {str(interface)} mac is None"
                mac = mac.get("address")
                assert mac is not None, f"ERROR! interface {str(interface)} mac is None"
                nic_type = interface.get("type")
                assert (
                    nic_type is not None
                ), f"ERROR! interface {str(interface)} type is None"
                result.append(DanglingNic(mac=str(mac), nic_type=nic_type, nic_bus=bus))
        return result

    def get_disks_to_add(self, disks: List[Disk]) -> List[Disk]:
        result = []
        targets = set()
        for disk in self.root.findall(".//devices/disk[@device='disk']/target"):
            dev = disk.get("dev")
            if dev:
                targets.add(dev)
        for disk in disks:
            if disk.dev not in targets:
                result.append(disk)
        return result

    def get_nics_to_add(self, networks: List[VMNetwork]) -> List[VMNetwork]:
        result = []
        targets = set()
        for network in self.root.findall(".//devices/interface/address"):
            bus = network.get("bus")
            if bus:
                targets.add(bus_string_to_int(bus))
        for network in networks:
            if network.nic_bus not in targets:
                result.append(network)
        return result

    def get_update_memory(self, memory_mb: int) -> bool:
        current_memory_kib = self.root.find(".//currentMemory")
        assert current_memory_kib is not None
        assert current_memory_kib.text is not None
        current_memory_mb = int(current_memory_kib.text) / 1024
        return current_memory_mb != memory_mb

    def get_update_vcpus(self, vcpus: int) -> bool:
        current_vcpus = self.root.find(".//vcpu")
        assert current_vcpus is not None
        assert current_vcpus.text is not None
        current_vcpus = int(current_vcpus.text)
        return current_vcpus != vcpus


def compare_vm_state(_, args: ModuleArgs) -> ModuleResult:
    xml_processor = VMXMLProcessor(args.dumpxml)
    output = Output(
        dangling_disks=xml_processor.get_dangling_disks(args.vm.disks),
        dangling_nics=xml_processor.get_dangling_nics(args.vm.networks),
        disks_to_add=xml_processor.get_disks_to_add(args.vm.disks),
        nics_to_add=xml_processor.get_nics_to_add(args.vm.networks),
        update_memory=xml_processor.get_update_memory(args.vm.memory_mb),
        update_vcpus=xml_processor.get_update_vcpus(args.vm.vcpus),
    )
    return ModuleResult(output=asdict(output))


def main():
    Utils.run_module(ModuleArgs, compare_vm_state)


if __name__ == "__main__":
    main()
