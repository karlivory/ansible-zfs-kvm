#!/usr/bin/python
from dataclasses import asdict, dataclass
from typing import List

from ansible_collections.karlivory.zk.plugins.module_utils.model import Disk
from ansible_collections.karlivory.zk.plugins.module_utils.utils import (
    ModuleResult, Utils)
from lxml import etree  # type: ignore


@dataclass
class ModuleArgs:
    dumpxml: str
    disks: List[Disk]


@dataclass
class DanglingDisk:
    dev: str


@dataclass
class Output:
    disks: List[DanglingDisk]


def get_dangling_disks(_, args: ModuleArgs) -> ModuleResult:
    result = []
    # Parse the XML string
    root = etree.fromstring(args.dumpxml)  # pylint: disable=c-extension-no-member

    defined_disks = set(x.dev for x in args.disks)
    for disk in root.findall(".//devices/disk[@device='disk']/target"):
        dev = disk.get("dev")
        if dev and dev not in defined_disks:
            result.append(DanglingDisk(dev=dev))

    return ModuleResult(output=asdict(Output(disks=result)))


def main():
    Utils.run_module(ModuleArgs, get_dangling_disks)


if __name__ == "__main__":
    main()