#!/usr/bin/python
from dataclasses import asdict

from ansible_collections.karlivory.zk.plugins.module_utils.model import (
    KVMHost, ZkKVMHost)
from ansible_collections.karlivory.zk.plugins.module_utils.utils import (
    ModuleResult, Utils)


def build_kvm_config(_, args: ZkKVMHost) -> ModuleResult:
    config = KVMHost.from_conf(args)

    return ModuleResult(output=asdict(config))


def main():
    Utils.run_module(ZkKVMHost, build_kvm_config)


if __name__ == "__main__":
    main()
