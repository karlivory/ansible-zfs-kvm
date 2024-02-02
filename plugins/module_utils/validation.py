#!/usr/bin/python
import re
from dataclasses import dataclass, field
from typing import List

from ansible_collections.karlivory.zk.plugins.module_utils.model import KVMHost


@dataclass
class ValidationError:
    field_name: str
    error: str


@dataclass
class ValidationResult:
    fail: bool = False
    validation_errors: List[ValidationError] = field(default_factory=list)


class KVMHostValidator:
    @staticmethod
    def validate(kvm_host: KVMHost) -> ValidationResult:
        errors = []

        # validate the whole kvm config
        for vm in kvm_host.vms:
            vm_name_regex = r"^[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9]$"
            if not re.match(vm_name_regex, vm.name):
                errors.append(
                    ValidationError(
                        field_name="vm.name",
                        error=f'field value "{vm.name}" does not match regex {vm_name_regex}',
                    )
                )

        return ValidationResult(fail=len(errors) > 0, validation_errors=errors)
