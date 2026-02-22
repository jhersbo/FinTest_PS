"""
Unit tests for app/core/models/entity.py and app/core/utils/serializable.py

Concrete subclasses of Entity / FindableEntity / View are defined locally
to avoid any DB dependency — these tests cover pure Python behaviour only.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, BIGINT

from app.core.models.entity import Entity, FindableEntity, View
from app.core.utils.serializable import Serializable, _serialize


# ---------------------------------------------------------------------------
# Lightweight concrete subclasses (no DB connection required)
# ---------------------------------------------------------------------------

class SampleView(View):
    __tablename__ = "sample_view"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)


class SampleEntity(Entity):
    __tablename__ = "sample_entity"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String)


class SampleFindable(FindableEntity):
    __tablename__ = "sample_findable"
    name: Mapped[str] = mapped_column(String)


# ---------------------------------------------------------------------------
# Helper to instantiate without DB.
# SQLAlchemy's DeclarativeBase __init__ accepts keyword args for mapped
# columns; no DB connection is required to construct ORM objects.
# ---------------------------------------------------------------------------

def _make_view(id:int=1, name:str="test") -> SampleView:
    return SampleView(id=id, name=name)


def _make_entity(id:int=1, label:str="hello") -> SampleEntity:
    return SampleEntity(id=id, label=label)


def _make_findable(gid:int=100, name:str="findable") -> SampleFindable:
    return SampleFindable(gid=gid, name=name)


# ---------------------------------------------------------------------------
# _serialize helper
# ---------------------------------------------------------------------------

class TestSerialize:
    def test_date_to_iso(self):
        assert _serialize(date(2024, 1, 15)) == "2024-01-15"

    def test_datetime_to_iso(self):
        dt = datetime(2024, 6, 1, 12, 30, 0)
        assert _serialize(dt) == "2024-06-01T12:30:00"

    def test_decimal_to_float(self):
        assert _serialize(Decimal("3.14")) == pytest.approx(3.14)

    def test_string_passthrough(self):
        assert _serialize("hello") == "hello"

    def test_int_passthrough(self):
        assert _serialize(42) == 42

    def test_none_passthrough(self):
        assert _serialize(None) is None


# ---------------------------------------------------------------------------
# Serializable mixin (to_dict / to_json)
# ---------------------------------------------------------------------------

class TestSerializableMixin:
    def test_to_dict_returns_public_attrs(self):
        obj = _make_view(id=5, name="foo")
        d = obj.to_dict()
        assert d["id"] == 5
        assert d["name"] == "foo"

    def test_to_dict_excludes_underscore_attrs(self):
        obj = _make_view()
        obj._private = "hidden"
        d = obj.to_dict()
        assert "_private" not in d

    def test_to_dict_excludes_s_id(self):
        obj = _make_view()
        # SQLAlchemy sets s_id-style internal keys; simulate
        obj.s_id_foo = "internal"
        d = obj.to_dict()
        assert "s_id_foo" not in d

    def test_to_json_serializes_dates(self):
        # Use Serializable directly — no SQLAlchemy machinery needed
        obj = Serializable()
        obj.__dict__["id"] = 1
        obj.__dict__["name"] = "dated"
        obj.__dict__["created"] = date(2024, 3, 1)
        j = obj.to_json()
        assert j["created"] == "2024-03-01"

    def test_to_json_serializes_decimals(self):
        obj = Serializable()
        obj.__dict__["id"] = 1
        obj.__dict__["name"] = "decimal"
        obj.__dict__["price"] = Decimal("99.99")
        j = obj.to_json()
        assert j["price"] == pytest.approx(99.99)

    def test_to_json_leaves_strings_unchanged(self):
        obj = _make_view(name="unchanged")
        j = obj.to_json()
        assert j["name"] == "unchanged"


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class TestView:
    def test_equals_same_data(self):
        a = _make_view(id=1, name="x")
        b = _make_view(id=1, name="x")
        assert a.equals(b) is True

    def test_equals_different_data(self):
        a = _make_view(id=1, name="x")
        b = _make_view(id=2, name="y")
        assert a.equals(b) is False

    def test_equals_none_returns_false(self):
        a = _make_view()
        assert a.equals(None) is False

    def test_is_view_flag(self):
        assert SampleView.__is_view__ is True

    def test_repr_contains_tablename(self):
        obj = _make_view()
        assert "sample_view" in repr(obj)


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------

class TestEntity:
    def test_equals_same_data(self):
        a = _make_entity(id=1, label="a")
        b = _make_entity(id=1, label="a")
        assert a.equals(b) is True

    def test_equals_different_label(self):
        a = _make_entity(id=1, label="a")
        b = _make_entity(id=1, label="b")
        assert a.equals(b) is False

    def test_equals_none_returns_false(self):
        a = _make_entity()
        assert a.equals(None) is False

    def test_repr_contains_tablename(self):
        obj = _make_entity()
        assert "sample_entity" in repr(obj)

    def test_to_dict_keys(self):
        obj = _make_entity(id=7, label="test")
        d = obj.to_dict()
        assert "id" in d
        assert "label" in d


# ---------------------------------------------------------------------------
# FindableEntity
# ---------------------------------------------------------------------------

class TestFindableEntity:
    def test_equals_same_data(self):
        a = _make_findable(gid=1, name="foo")
        b = _make_findable(gid=1, name="foo")
        assert a.equals(b) is True

    def test_equals_different_gid(self):
        a = _make_findable(gid=1, name="foo")
        b = _make_findable(gid=2, name="foo")
        assert a.equals(b) is False

    def test_equals_none_returns_false(self):
        a = _make_findable()
        assert a.equals(None) is False

    def test_get_name_format(self):
        obj = _make_findable()
        name = obj.get_name()
        # should be fully-qualified: module.ClassName
        assert "SampleFindable" in name
        assert "." in name

    def test_repr_contains_tablename(self):
        obj = _make_findable()
        assert "sample_findable" in repr(obj)

    def test_to_dict_includes_gid(self):
        obj = _make_findable(gid=42)
        assert obj.to_dict()["gid"] == 42
