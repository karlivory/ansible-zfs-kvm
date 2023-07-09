from dataclasses import MISSING, asdict, dataclass, field, fields, is_dataclass
from typing import (Any, Callable, Dict, List, Optional, Type, TypeVar, Union,
                    cast)

from ansible.module_utils.basic import AnsibleModule
from dacite import from_dict


@dataclass
class ModuleResult:
    msg: Any = field(default_factory=dict)
    changed: bool = False
    failed: bool = False
    output: Any = field(default_factory=dict)


T = TypeVar("T")


class Utils:
    @staticmethod
    def dict_merge(
        arg1: Optional[dict[str, Any]],
        arg2: Optional[dict[str, Any]],
    ) -> Optional[dict[str, Any]]:
        """
        Merge arg2 fields into arg1. arg2 None fields get ignored. Not a deep merge!
        """
        arg1_dict = arg1 if arg1 is not None else {}
        arg2_dict = arg2 if arg2 is not None else {}
        merged = {**arg1_dict, **arg2_dict}
        if merged == {}:
            return None
        return merged

    @staticmethod
    def dataclass_merge(
        arg1: Optional[T], arg2: Optional[T], data_class: Type[T]
    ) -> Optional[T]:
        """
        Merge arg2 fields into arg1. arg2 None fields get ignored. Not a deep merge!
        """
        arg1_dict = {}
        if arg1:
            assert is_dataclass(arg1)
            arg1_dict = asdict(arg1)
        arg2_dict = {}
        if arg2:
            assert is_dataclass(arg2)
            arg2_dict = asdict(arg2)
        arg2_dict = {k: v for k, v in arg2_dict.items() if v is not None}
        merged = {**arg1_dict, **arg2_dict}
        if merged == {}:
            return None
        return from_dict(data_class, data=merged)

    @staticmethod
    def run_module(args_class: Type[T], run: Callable[[T], ModuleResult]) -> None:
        argument_spec = Utils.dataclass_to_argument_spec(args_class)

        module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

        params_dict = cast(Dict[str, Any], module.params)
        args: T = from_dict(data_class=args_class, data=params_dict)

        try:
            result = run(args)
            if result.failed:
                module.fail_json(msg=result.msg, output=result.output)
            module.exit_json(
                changed=result.changed, msg=result.msg, output=result.output
            )
        except ValueError as e:
            module.fail_json(msg=str(e))

    @staticmethod
    def try_from_values(
        object_name: str, field_name: str, values: List[Optional[T]]
    ) -> T:
        for value in values:
            if value is not None:
                return value
        raise ValueError(
            f"ERROR! {object_name} -- unable to find value for {field_name}! All values are None."
        )

    # https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_documenting.html
    # Is there an official ansible library fn for something like this?
    @staticmethod
    def dataclass_to_argument_spec(dataclass_obj):
        def convert_field(dataclass_field):
            field_type = dataclass_field.type
            is_optional = False

            if hasattr(field_type, "__origin__") and field_type.__origin__ == Union:
                optional_types = field_type.__args__
                if len(optional_types) == 2 and type(None) in optional_types:
                    field_type = [t for t in optional_types if t != type(None)][0]
                    is_optional = True

            field_metadata = dataclass_field.metadata

            base_field_spec = {
                "type": field_type.__name__.lower()
                if hasattr(field_type, "__name__")
                else str(field_type).lower(),
                "required": dataclass_field.default is MISSING
                and dataclass_field.default_factory is MISSING
                and not is_optional,
            }

            if "choices" in field_metadata:
                base_field_spec["choices"] = field_metadata["choices"]

            if is_dataclass(field_type):
                return {
                    **base_field_spec,
                    "type": "dict",
                    "options": Utils.dataclass_to_argument_spec(field_type),
                }
            if hasattr(field_type, "__origin__") and issubclass(
                field_type.__origin__, List
            ):
                element_type = field_type.__args__[0]
                if is_dataclass(element_type):
                    return {
                        **base_field_spec,
                        "type": "list",
                        "elements": "dict",
                        "options": Utils.dataclass_to_argument_spec(element_type),
                    }
                return {
                    **base_field_spec,
                    "type": "list",
                    "elements": element_type.__name__.lower(),
                }
            return base_field_spec

        argument_spec = {
            field.name: convert_field(field) for field in fields(dataclass_obj)
        }
        return argument_spec
