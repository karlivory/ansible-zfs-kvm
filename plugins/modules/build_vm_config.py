#!/usr/bin/python
from dataclasses import asdict

from ansible_collections.karlivory.zk.plugins.module_utils.model import VM, ZkVM
from ansible_collections.karlivory.zk.plugins.module_utils.utils import (
    ModuleResult,
    Utils,
)


def build_vm_config(args: ZkVM) -> ModuleResult:
    config = VM.from_conf(args)

    return ModuleResult(output=asdict(config))


def main():
    Utils.run_module(ZkVM, build_vm_config)


if __name__ == "__main__":
    main()
