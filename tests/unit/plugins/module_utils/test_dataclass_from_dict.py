from dataclasses import dataclass
from typing import List, Optional

from ansible_collections.karlivory.zk.plugins.module_utils.utils import Utils


def test_flat_dataclass():
    d = {
        "name": "Mike",
        "age": 33,
    }

    @dataclass
    class ClassA:
        name: str
        age: int

    expected = ClassA(name="Mike", age=33)
    result = Utils.dataclass_from_dict(ClassA, d)
    assert result == expected


def test_list_simple():
    d = {
        "names": ["Mike", "Josh"],
    }

    @dataclass
    class ClassA:
        names: list[str]

    expected = ClassA(names=["Mike", "Josh"])
    result = Utils.dataclass_from_dict(ClassA, d)
    assert result == expected


def test_list_dataclass():
    d = {
        "elements": [
            {"name": "Mike"},
            {"name": "Josh"},
        ],
    }

    @dataclass
    class ClassB:
        name: str

    @dataclass
    class ClassA:
        elements: list[ClassB]

    expected = ClassA(
        elements=[
            ClassB(name="Mike"),
            ClassB(name="Josh"),
        ]
    )
    result = Utils.dataclass_from_dict(ClassA, d)
    assert result == expected


def test_optional():
    d = {
        "name": "Mike",
    }

    @dataclass
    class ClassA:
        name: str
        age: Optional[int]

    expected = ClassA(name="Mike", age=None)
    result = Utils.dataclass_from_dict(ClassA, d)
    assert result == expected


def test_optional_dict():
    d = {
        "name": "Mike",
    }

    @dataclass
    class ClassA:
        name: str
        other: Optional[dict]

    expected = ClassA(name="Mike", other=None)
    result = Utils.dataclass_from_dict(ClassA, d)
    assert result == expected


def test_optional_subclass():
    d = {"other": {"city": "foobar"}}

    @dataclass
    class ClassB:
        city: str

    @dataclass
    class ClassA:
        other: Optional[ClassB]

    expected = ClassA(other=ClassB(city="foobar"))
    result = Utils.dataclass_from_dict(ClassA, d)
    assert result == expected


def test_optional_subclass_none():
    d = {"name": "Mike", "elements": [{"city": "foo"}]}

    @dataclass
    class ClassC:
        city: str

    @dataclass
    class ClassB:
        city: str
        other: Optional[ClassC]

    @dataclass
    class ClassA:
        name: str
        elements: List[ClassB]

    expected = ClassA(name="Mike", elements=[ClassB(city="foo", other=None)])
    result = Utils.dataclass_from_dict(ClassA, d)
    assert result == expected


def test_nested_dataclass():
    d = {
        "name": "Mike",
        "age": 33,
        "address": {"city": "foo", "country": "bar"},
    }

    @dataclass
    class ClassB:
        city: str
        country: str

    @dataclass
    class ClassA:
        name: str
        age: int
        address: ClassB

    expected = ClassA(name="Mike", age=33, address=ClassB(city="foo", country="bar"))
    result = Utils.dataclass_from_dict(ClassA, d)
    assert result == expected


def test_comprehensive():
    d = {
        "name": "John",
        "age": 30,
        "address": {
            "city": "New York",
            "country": "USA",
            "coordinates": {"latitude": 40.7128, "longitude": -74.0060},
        },
        "contacts": [
            {"type": "email", "value": "john@example.com"},
            {"type": "phone", "value": "123-456-7890"},
        ],
        "metadata": {"is_verified": True, "ratings": [4.5, 4.8, 4.2]},
    }

    @dataclass
    class Coordinates:
        latitude: float
        longitude: float

    @dataclass
    class Address:
        city: str
        country: str
        coordinates: Coordinates

    @dataclass
    class Contact:
        type: str
        value: str

    @dataclass
    class Metadata:
        is_verified: bool
        ratings: List[float]
        other_contact: Optional[Contact]

    @dataclass
    class Person:
        name: str
        age: int
        address: Address
        contacts: List[Contact]
        metadata: Optional[Metadata]
        extra_info: Optional[dict]

    expected = Person(
        name="John",
        age=30,
        address=Address(
            city="New York",
            country="USA",
            coordinates=Coordinates(latitude=40.7128, longitude=-74.0060),
        ),
        contacts=[
            Contact(type="email", value="john@example.com"),
            Contact(type="phone", value="123-456-7890"),
        ],
        metadata=Metadata(
            is_verified=True, ratings=[4.5, 4.8, 4.2], other_contact=None
        ),
        extra_info=None,
    )

    result = Utils.dataclass_from_dict(Person, d)
    assert result == expected
