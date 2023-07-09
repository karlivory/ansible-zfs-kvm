from dataclasses import dataclass, field
from typing import List, Optional

from ansible_collections.karlivory.zk.plugins.module_utils.utils import Utils


def test_flat_dataclass():
    @dataclass
    class ClassA:
        name: str
        age: int

    result = Utils.dataclass_to_argument_spec(ClassA)
    expected = {
        "name": {"type": "str", "required": True},
        "age": {"type": "int", "required": True},
    }
    assert result == expected


def test_nested_dataclass():
    @dataclass
    class ClassB:
        city: str
        country: str

    @dataclass
    class ClassA:
        name: str
        age: int
        address: ClassB

    result = Utils.dataclass_to_argument_spec(ClassA)
    expected = {
        "name": {"type": "str", "required": True},
        "age": {"type": "int", "required": True},
        "address": {
            "type": "dict",
            "options": {
                "city": {"type": "str", "required": True},
                "country": {"type": "str", "required": True},
            },
            "required": True,
        },
    }
    assert result == expected


def test_dataclass_with_optional_field():
    @dataclass
    class A:
        name: str
        address: Optional[str] = None

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "name": {"type": "str", "required": True},
        "address": {"type": "str", "required": False},
    }
    assert result == expected


def test_nested_list():
    @dataclass
    class B:
        name: str

    @dataclass
    class A:
        name: str
        sublist: List[B] = field(default_factory=list)

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "name": {"type": "str", "required": True},
        "sublist": {
            "type": "list",
            "elements": "dict",
            "options": {
                "name": {"type": "str", "required": True},
            },
            "required": False,
        },
    }
    assert result == expected


def test_nested_optional_list():
    @dataclass
    class B:
        name: str

    @dataclass
    class A:
        name: str
        sublist: Optional[List[B]] = field(default_factory=list)

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "name": {"type": "str", "required": True},
        "sublist": {
            "type": "list",
            "elements": "dict",
            "options": {
                "name": {"type": "str", "required": True},
            },
            "required": False,
        },
    }
    assert result == expected


def test_nested_list_with_optional_field():
    @dataclass
    class B:
        name: str
        age: Optional[int] = None

    @dataclass
    class A:
        name: str
        sublist: List[B] = field(default_factory=list)

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "name": {"type": "str", "required": True},
        "sublist": {
            "type": "list",
            "elements": "dict",
            "options": {
                "name": {"type": "str", "required": True},
                "age": {"type": "int", "required": False},
            },
            "required": False,
        },
    }
    assert result == expected


def test_multiple_nested_dataclasses():
    @dataclass
    class C:
        country: str

    @dataclass
    class B:
        city: str
        location: C

    @dataclass
    class A:
        name: str
        address: B

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "name": {"type": "str", "required": True},
        "address": {
            "type": "dict",
            "options": {
                "city": {"type": "str", "required": True},
                "location": {
                    "type": "dict",
                    "options": {
                        "country": {"type": "str", "required": True},
                    },
                    "required": True,
                },
            },
            "required": True,
        },
    }
    assert result == expected


def test_dataclass_with_default_value():
    @dataclass
    class A:
        name: str
        age: int = 30

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "name": {"type": "str", "required": True},
        "age": {"type": "int", "required": False},
    }
    assert result == expected


def test_nested_dataclass_with_default_value():
    @dataclass
    class B:
        city: str
        country: str = "USA"

    @dataclass
    class A:
        name: str
        age: int
        address: B

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "name": {"type": "str", "required": True},
        "age": {"type": "int", "required": True},
        "address": {
            "type": "dict",
            "options": {
                "city": {"type": "str", "required": True},
                "country": {"type": "str", "required": False},
            },
            "required": True,
        },
    }
    assert result == expected


def test_dataclass_with_choices():
    @dataclass
    class A:
        name: str
        gender: str = field(metadata={"choices": ["male", "female", "other"]})

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "name": {"type": "str", "required": True},
        "gender": {
            "type": "str",
            "required": True,
            "choices": ["male", "female", "other"],
        },
    }
    assert result == expected


def test_dataclass_with_optional_choices():
    @dataclass
    class A:
        name: str
        gender: Optional[str] = field(metadata={"choices": ["male", "female", "other"]})

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "name": {"type": "str", "required": True},
        "gender": {
            "type": "str",
            "required": False,
            "choices": ["male", "female", "other"],
        },
    }
    assert result == expected


def test_list_with_default_factory_should_not_be_required():
    @dataclass
    class C:
        title: str

    @dataclass
    class A:
        items: List[C] = field(default_factory=list)

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "items": {
            "type": "list",
            "elements": "dict",
            "required": False,
            "options": {"title": {"required": True, "type": "str"}},
        },
    }
    assert result == expected


def test_comprehensive_dataclass_1():
    @dataclass
    class D:
        country: str
        state: Optional[str] = None

    @dataclass
    class C:
        title: str
        description: Optional[str] = None
        tags: Optional[List[str]] = field(default_factory=list)

    @dataclass
    class B:
        city: str
        location: Optional[D] = None
        items: List[C] = field(default_factory=list)

    @dataclass
    class A:
        name: str
        address: B
        age: Optional[int] = None

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "name": {"type": "str", "required": True},
        "address": {
            "type": "dict",
            "required": True,
            "options": {
                "city": {"type": "str", "required": True},
                "location": {
                    "type": "dict",
                    "required": False,
                    "options": {
                        "country": {"type": "str", "required": True},
                        "state": {"type": "str", "required": False},
                    },
                },
                "items": {
                    "type": "list",
                    "required": False,
                    "elements": "dict",
                    "options": {
                        "title": {"type": "str", "required": True},
                        "description": {"type": "str", "required": False},
                        "tags": {
                            "type": "list",
                            "elements": "str",
                            "required": False,
                        },
                    },
                },
            },
        },
        "age": {"type": "int", "required": False},
    }
    assert result == expected


def test_comprehensive_dataclass_2():
    @dataclass
    class D:
        title: str
        description: Optional[str] = None

    @dataclass
    class C:
        start_time: str
        end_time: str
        sessions: List[D]

    @dataclass
    class B:
        name: str
        events: List[C]

    @dataclass
    class A:
        organizer: str
        activities: List[B]
        location: Optional[str] = None

    result = Utils.dataclass_to_argument_spec(A)
    expected = {
        "organizer": {"type": "str", "required": True},
        "location": {"type": "str", "required": False},
        "activities": {
            "type": "list",
            "elements": "dict",
            "required": True,
            "options": {
                "name": {"type": "str", "required": True},
                "events": {
                    "type": "list",
                    "required": True,
                    "elements": "dict",
                    "options": {
                        "start_time": {"type": "str", "required": True},
                        "end_time": {"type": "str", "required": True},
                        "sessions": {
                            "type": "list",
                            "required": True,
                            "elements": "dict",
                            "options": {
                                "title": {"type": "str", "required": True},
                                "description": {"type": "str", "required": False},
                            },
                        },
                    },
                },
            },
        },
    }
    assert result == expected
