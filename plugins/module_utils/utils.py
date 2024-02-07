from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from typing import (Any, Callable, Dict, List, Optional, Type, TypeVar, Union,
                    cast, get_args, get_origin)

from ansible.module_utils.basic import AnsibleModule


@dataclass
class ModuleResult:
    msg: Any = field(default_factory=dict)
    changed: bool = False
    failed: bool = False
    output: Any = field(default_factory=dict)


T = TypeVar("T")


class Utils:
    @staticmethod
    def dataclass_from_dict(dclass: Type[T], d: dict) -> T:
        ctor_args = {}
        for dataclass_field in fields(dclass):
            field_name = dataclass_field.name
            field_value = d.get(field_name, MISSING)

            if field_value is MISSING or field_value is None:
                if dataclass_field.default is not MISSING:
                    ctor_args[field_name] = dataclass_field.default
                elif dataclass_field.default_factory is not MISSING:
                    ctor_args[field_name] = dataclass_field.default_factory()
                else:
                    ctor_args[field_name] = None
                continue

            field_type = dataclass_field.type
            origin = get_origin(field_type)
            args = get_args(field_type)

            # list for Python 3.9 or newer
            if origin in (list, List):
                inner_type = args[0]
                ctor_args[field_name] = []
                for item in field_value:
                    if is_dataclass(inner_type):
                        ctor_args[field_name].append(
                            Utils.dataclass_from_dict(inner_type, item)
                        )
                    else:
                        ctor_args[field_name].append(item)
            elif origin in (Union, Optional):
                non_none_types = [arg for arg in args if arg is not type(None)]
                if non_none_types and is_dataclass(non_none_types[0]):
                    inner_type = non_none_types[0]
                    ctor_args[field_name] = Utils.dataclass_from_dict(
                        inner_type, field_value
                    )
                else:
                    ctor_args[field_name] = field_value
            else:
                ctor_args[field_name] = (
                    Utils.dataclass_from_dict(field_type, field_value)
                    if is_dataclass(field_type)
                    else field_value
                )
        return dclass(**ctor_args)

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
    def run_module(
        args_class: Type[T], run: Callable[[AnsibleModule, T], ModuleResult]
    ) -> None:
        argument_spec = Utils.dataclass_to_argument_spec(args_class)

        module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

        params_dict = cast(Dict[str, Any], module.params)
        args: T = Utils.dataclass_from_dict(args_class, params_dict)

        try:
            result = run(module, args)
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
                "type": (
                    field_type.__name__.lower()
                    if hasattr(field_type, "__name__")
                    else str(field_type).lower()
                ),
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
