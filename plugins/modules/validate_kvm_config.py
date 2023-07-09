#!/usr/bin/python
from dataclasses import asdict, dataclass

from ansible_collections.karlivory.zk.plugins.module_utils.model import KVMHost
from ansible_collections.karlivory.zk.plugins.module_utils.utils import (
    ModuleResult,
    Utils,
)
from ansible_collections.karlivory.zk.plugins.module_utils.validation import (
    KVMHostValidator,
)


@dataclass
class ModuleArgs:
    to_validate: KVMHost


def validate_kvm_config(args: ModuleArgs) -> ModuleResult:
    result = KVMHostValidator.validate(args.to_validate)

    return ModuleResult(output=asdict(result), failed=result.fail)


def main():
    Utils.run_module(ModuleArgs, validate_kvm_config)


if __name__ == "__main__":
    main()
