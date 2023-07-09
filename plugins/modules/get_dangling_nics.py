#!/usr/bin/python
from dataclasses import asdict, dataclass
from typing import List

from ansible_collections.karlivory.zk.plugins.module_utils.model import VMNetwork
from ansible_collections.karlivory.zk.plugins.module_utils.utils import (
    ModuleResult,
    Utils,
)
from lxml import etree  # type: ignore


@dataclass
class ModuleArgs:
    dumpxml: str
    networks: List[VMNetwork]


@dataclass
class DanglingNic:
    mac: str
    nic_type: str
    nic_bus: int


@dataclass
class Output:
    nics: List[DanglingNic]


def bus_string_to_int(n: str) -> int:
    if n.startswith("0x"):
        return int(n, 16)
    return int(n)


def get_dangling_nics(args: ModuleArgs) -> ModuleResult:
    result = []
    # Parse the XML string
    root = etree.fromstring(args.dumpxml)  # pylint: disable=c-extension-no-member

    defined_bus_numbers = [n.nic_bus for n in args.networks]
    # Extract NIC info from the XML
    for interface in root.findall(".//devices/interface"):
        address = interface.find("address")
        assert address is not None, f"ERROR! interface {str(interface)} address is None"
        bus = address.get("bus")
        assert bus is not None, f"ERROR! interface {str(interface)} address.bus is None"
        bus = bus_string_to_int(bus)
        print(bus)
        if bus not in defined_bus_numbers:
            mac = interface.find("mac")
            assert mac is not None, f"ERROR! interface {str(interface)} mac is None"
            mac = mac.get("address")
            assert mac is not None, f"ERROR! interface {str(interface)} mac is None"
            nic_type = interface.get("type")
            print(mac)
            assert (
                nic_type is not None
            ), f"ERROR! interface {str(interface)} type is None"

            result.append(DanglingNic(mac=str(mac), nic_type=nic_type, nic_bus=bus))

    return ModuleResult(output=asdict(Output(nics=result)))


def main():
    Utils.run_module(ModuleArgs, get_dangling_nics)


if __name__ == "__main__":
    main()
