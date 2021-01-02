import pytest
from multilevel_py.core import Clabject, create_clabject_prop, is_clabect_or_empty_constr
from multilevel_py.constraints import is_str_constraint, is_int_constraint, ReInitPropConstr, EmptyValue
from multilevel_py.exceptions import UninitialisedPropException, \
    ConstraintViolationException, TypeSpecificConstraintRemovalException


@pytest.fixture(scope="module")
def build_Meta_meta():
    def builder():
        Meta_meta = Clabject(name="MetaMeta", parents=[], init_props={})
        prop_a = create_clabject_prop(n="a", t=1, f="*", i_f=False, c=[is_str_constraint])
        prob_b = create_clabject_prop(n="b", t=1, f="*", i_f=False, i_assoc=True)
        Meta_meta.define_props([prop_a, prob_b])
        return Meta_meta
    return builder


def test_reinit_type_spec_constr_removal_causes_exception(build_Meta_meta):
    Meta_meta = build_Meta_meta()
    Meta = Meta_meta(name="Meta", parents=[], init_props={"a": "valid_string", "b": EmptyValue})
    with pytest.raises(TypeSpecificConstraintRemovalException):
        Meta.require_re_init_on_next_step(prop_name="b",
                                          re_init_prop_constr=ReInitPropConstr(del_constr=[is_clabect_or_empty_constr]))


@pytest.fixture(scope="module")
def build_Meta(build_Meta_meta):
    def builder():
        Meta_meta = build_Meta_meta()
        Meta = Meta_meta(name="Meta", parents=[], init_props={"a": "valid_string", "b": EmptyValue})
        a_re_init_prop = ReInitPropConstr(del_constr=[is_str_constraint], add_constr=[is_int_constraint])
        Meta.require_re_init_on_next_step(prop_name="a", re_init_prop_constr=a_re_init_prop)
        return Meta
    return builder


@pytest.mark.parametrize(
    ("init_props", "expected_exception"), ([
        ({}, UninitialisedPropException),  # a must be reinitialised
        ({'a': 'a_str'}, ConstraintViolationException),  # a must be an int now
    ])
)
def test_invalid_re_init(build_Meta, init_props, expected_exception):
    with pytest.raises(expected_exception):
        Meta = build_Meta()
        Cls = Meta(name="Cls", parents=[], init_props=init_props)
        assert Cls

def test_valid_re_init(build_Meta):
    Meta =build_Meta()
    Cls = Meta(name="Cls", parents=[], init_props={"a": 123})
    assert [constr.name for constr in Cls.__ml_props__["a"].constraints] == ["is_of_int"]