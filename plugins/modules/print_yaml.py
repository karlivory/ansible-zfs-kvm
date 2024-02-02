#!/usr/bin/python
from dataclasses import dataclass
from typing import Any

import yaml
from ansible_collections.karlivory.zk.plugins.module_utils.utils import (
    ModuleResult, Utils)


# https://github.com/yaml/pyyaml/issues/234#issuecomment-786026671
# https://stackoverflow.com/questions/25108581/python-yaml-dump-bad-indentation/39681672#39681672
class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


@dataclass
class ModuleArgs:
    data: dict[str, Any]


def print_yaml(_, args: ModuleArgs) -> ModuleResult:
    output = yaml.dump(args.data, Dumper=MyDumper, default_flow_style=False)
    return ModuleResult(output=output)


def main():
    Utils.run_module(ModuleArgs, print_yaml)


if __name__ == "__main__":
    main()
