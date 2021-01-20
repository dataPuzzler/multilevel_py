import pytest

from multilevel_py.constraints import prop_constraint_is_th_order_instance_of_clabject_set_functional, \
    prop_constraint_collection_member_functional, is_int_constraint, ClabjectStateConstraint
from multilevel_py.core import Clabject, create_clabject_prop
from multilevel_py.exceptions import ConstraintViolationException

MetaMeta = Clabject(name="Meta", parents=[], init_props={})
Meta = MetaMeta(name="Meta", parents=[], init_props={})
Meta_1 = MetaMeta(name="Meta_1", parents=[], init_props={})
Meta_2 = MetaMeta(name="Meta_2", parents=[], init_props={})
Cl_ss = Meta(name="Cl_ss", parents=[], init_props={})
Cl_ss_2 = Meta_2(name="Cl_ss_2", parents=[], init_props={})
inst_ce = Cl_ss(name="inst_ce", init_props={})


@pytest.mark.parametrize(
    "given_value", ([
        ("sdf"), (1234), (["a", "b"])
    ])
)
def test_higher_order_is_instance_of_in_clabject_set_constraint_invalid_value(given_value):
    constr = prop_constraint_is_th_order_instance_of_clabject_set_functional({Meta, Meta_1})
    constr(given_value)
    assert constr.violation_reason != ""


@pytest.mark.parametrize(
    "given_value, expected_return", ([
        (Cl_ss, True),
        (inst_ce, False),
        (Meta, False),
    ])
)
def test_higher_order_is_instance_of_in_clabject_set_constraint_valid_value(given_value, expected_return):
    constr = prop_constraint_is_th_order_instance_of_clabject_set_functional({Meta, Meta_1})
    assert constr(given_value) == expected_return


@pytest.fixture(scope="module")
def MetaTgtClab():
    return Clabject(name="MetaTgtClab", parents=[], init_props={})


@pytest.fixture(scope="module")
def MetaSrcClab(MetaTgtClab):
    _MetaSrcClab = Clabject(name="MetaSrcClab", parents=[], init_props={})
    snd_order_inst_of_meta_tgt = prop_constraint_is_th_order_instance_of_clabject_set_functional({MetaTgtClab}, order=2)
    int_arr_prop = create_clabject_prop(
        "int_arr", t=1, f="*", c=[],
        coll_desc=(2, 4, is_int_constraint))
    tgt_cls_arr_prop = create_clabject_prop(
        "tgt_arr", t=1, f="*", c=[],
        coll_desc=(1, 2, snd_order_inst_of_meta_tgt))
    _MetaSrcClab.define_props([int_arr_prop, tgt_cls_arr_prop])
    return _MetaSrcClab


@pytest.mark.parametrize(
    "given_value, expected_exception", ([
        ([12, "sdf"], ConstraintViolationException),  # invalid member
        ("sdf", ConstraintViolationException)       # no collection at all
    ])
)
def test_init_with_invalid_int_arr_prop(MetaSrcClab, given_value, expected_exception):
        with pytest.raises(expected_exception):
            SrcClab = MetaSrcClab(name="SrcClab", parents=[], init_props={"int_arr": given_value,
                                                                          "tgt_arr": []})


@pytest.mark.parametrize(
    "given_value, expected_violation_name", ([
        ("sdf", "is_collection"),  # no collection at all
       ([12, "sdfsd"], "check_is_of_int_on_collection_members"),  # invalid member

    ])
)
def test_init_with_with_invalid_int_arr_prop_violation_message(MetaSrcClab, given_value, expected_violation_name):
    try:
        SrcClab = MetaSrcClab(name="SrcClab", parents=[], init_props={"int_arr": given_value,
                                                                      "tgt_arr": []})
    except ConstraintViolationException as ex:
        int_arr_violated_constraints = [c.name for c in ex.violated_constraints["int_arr"]]
        assert expected_violation_name in int_arr_violated_constraints


def test_int_arr_multiplicity_not_checked_on_init_but_found_in_explicit_check(MetaSrcClab):
    try:

        SrcClab = MetaSrcClab(name="SrcClab", parents=[], init_props={"int_arr": [123],
                                                                      "tgt_arr": []})
    except ConstraintViolationException as ex:
        pytest.fail("Multiplicity Constraints should not be checked on init")

    constr_violations_names = [c.name for c in SrcClab.check_prop_constraints()["int_arr"]]

    assert "collection_multiplicity_between_2_and_4" in constr_violations_names


def test_tgt_arr_member_violation(MetaSrcClab, MetaTgtClab):
    try:
        TgtClab = MetaTgtClab(name="TgtClab", parents=[], init_props={})
        SrcClab = MetaSrcClab(name="SrcClab", parents=[], init_props={"int_arr": [123],
                                                                      "tgt_arr": [TgtClab]})
    except ConstraintViolationException as ex:
        constr_violation_names = [c.name for c in ex.violated_constraints["tgt_arr"]]
        [print(c.violation_reason) for c in ex.violated_constraints["tgt_arr"]]
        assert "check_2_order_instance_of_clabject_set_{'MetaTgtClab'}_on_collection_members" in constr_violation_names

@pytest.fixture(scope="module")
def clab_state_constr():
    def eval_state(current_clab):
        if (len(current_clab.int_arr) + len(current_clab.tgt_arr)) < 4:
            return "There must be in total at least four members in int_arr and tgt_arr"
        else:
            return ""
    clab_state_constr = ClabjectStateConstraint(name="AtLeastThreeArrMembers", eval_clabject_func=eval_state)
    return clab_state_constr



def test_invalid_src_clabject_state(MetaSrcClab, MetaTgtClab, clab_state_constr):
    # The following state constraint should be evaluated only on instance level
    state_constr_at_least_4_arr_members_prop = create_clabject_prop(
        n=clab_state_constr.name, t=2, f='*', c=[], i_sc=True, v=clab_state_constr)
    MetaSrcClab.define_props([state_constr_at_least_4_arr_members_prop])
    TgtClab = MetaTgtClab(name="TgtClab", parents=[], init_props={})
    inst_Tgt_Clab = TgtClab(name="inst_Tgt_Clab")

    SrcClab = MetaSrcClab(name="SrcClab", parents=[], init_props={"int_arr": [123],
                                                                  "tgt_arr": [inst_Tgt_Clab]})
    assert len(SrcClab.check_state_constraints()) == 0
    inst_Src_Clab = SrcClab(name="inst_src_clab", declare_as_instance=True)
    print(inst_Src_Clab.check_state_constraints())
    assert "AtLeastThreeArrMembers" in inst_Src_Clab.check_state_constraints().keys()