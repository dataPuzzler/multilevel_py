import pytest
import math
from multilevel_py.core import ClabjectPropDict
from multilevel_py.clabject_prop import SimpleProp


@pytest.fixture(scope="module")
def clabject_prop_dict():
    return ClabjectPropDict()


@pytest.fixture(scope="module")
def lev_3_prop():
    return SimpleProp(
        prop_name="duration",
        steps_to_instantiation=3,
        steps_from_instantiation=math.inf,
)


def test_clabject_prop_manager_getter_setter_valid_value(clabject_prop_dict, lev_3_prop):
    print(type(lev_3_prop))
    clabject_prop_dict[lev_3_prop.prop_name] = lev_3_prop
    prop = clabject_prop_dict[lev_3_prop.prop_name]
    print(clabject_prop_dict.keys())
    assert prop.prop_name == lev_3_prop.prop_name


def test_clabject_prop_manager_set_value_of_invalid_type(clabject_prop_dict):
    with pytest.raises(TypeError):
        clabject_prop_dict["duration"] = 234564


def test_clabject_prop_manager_set_value_inconsistent_with_key(clabject_prop_dict, lev_3_prop):
    with pytest.raises(ValueError):
        clabject_prop_dict["hello"] = lev_3_prop
