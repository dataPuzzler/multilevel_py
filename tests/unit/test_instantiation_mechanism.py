from multilevel_py.core import Clabject
from multilevel_py.clabject_prop import SimpleProp, MethodProp
from types import FunctionType
from multilevel_py.exceptions import UninitialisedPropException, UnduePropInstantiationException, UndefinedPropsException, \
    ConstraintViolationException, ChangeFinalPropException, NotAClabjectException, ClabjectDeclaredAsInstanceException
from multilevel_py.constraints import is_str_constraint, is_int_constraint, is_function_constraint, \
    prop_constraint_ml_instance_of_th_order_functional
import pytest
import math

# Underlying Schema of First Instantiation Hierarchy
# Meta_meta
#   Definitions <constraints>: <type> [= <prop_value>] <steps_to_instantiation>, <steps_from_instantiation>, [final]
#       a: is_str = "MetaMetaProp" 0,* final
#       b: is_str 1,1,final
#       c: is_int 1,*
#       d: is_function 2,*, final
#       e: is_str 3,0 final
#   State:
#       a = "MetaMetaProp"
# Meta_meta => Meta {b = "valid_string", c=123}
# Meta
#   State:
#       a = "MetaMetaProp"
#       b = "valid_string"
#       c = 123
# Meta => Cl_ss {d= lambda x: return "Hello "+ str(x)}
# Cl_ss
#     State:
#       a = "MetaMetaProp"
#       c = 123
#       d= lambda x: return "Hello "+ str(x)
# Cl_ss => inst_nce {e = "Finally reached Instance Level"}
# Inst_nce
#     State:
#       a = "MetaMetaProp"
#       c = 123
#       d= lambda x: return "Hello "+ str(x)
#       e = "Finally reached Instance Level"


@pytest.fixture(scope="module")
def build_Meta_meta():
    def builder():
        Meta_meta = Clabject(name="MetaMeta", parents=[], init_props={})  # > Level 3 via Prop e
        prop_a = SimpleProp(prop_name="a",
                            constraints=[is_str_constraint],
                            steps_to_instantiation=0,
                            steps_from_instantiation=math.inf,
                            is_final=True,
                            prop_value="MetaMetaProp")

        prop_b = SimpleProp(prop_name="b",
                            constraints=[is_str_constraint],
                            steps_to_instantiation=1,
                            steps_from_instantiation=0,
                            is_final=True)

        prob_c = SimpleProp(prop_name="c",
                            constraints=[is_int_constraint],
                            steps_to_instantiation=1,
                            steps_from_instantiation=math.inf,
                            is_final=False)

        prob_d = SimpleProp(prop_name="d",
                            constraints=[is_function_constraint],
                            steps_to_instantiation=2,
                            steps_from_instantiation=math.inf,
                            is_final=True)

        prob_e = SimpleProp(prop_name="e",
                            constraints=[is_str_constraint],
                            steps_to_instantiation=3,
                            steps_from_instantiation=math.inf,
                            is_final=True)

        Meta_meta.define_props([prop_a, prop_b, prob_c, prob_d, prob_e])
        return Meta_meta

    return builder


def test_prop_a_accessible_at_meta_meta_level(build_Meta_meta):
    Meta_meta = build_Meta_meta()
    assert Meta_meta.a == "MetaMetaProp"


@pytest.mark.parametrize(
    ("init_props", "expected_exception"), ([
        ({'b': 'valid_string'}, UninitialisedPropException),  # c is missing
        ({'c': 123}, UninitialisedPropException),  # b is missing
        ({'b': 123, 'c': 123}, ConstraintViolationException),  # b is not str
        ({'b': "valid_string", 'c': "valid_string"}, ConstraintViolationException),  # c is not int
        ({'b': 'valid_string', 'c': 123,'d': lambda x: x}, UnduePropInstantiationException),  # d only at next instant.
        ({'not_existing_prop': 2345}, UndefinedPropsException)
    ])
)
def test_invalid_meta_meta_instantiation(build_Meta_meta, init_props, expected_exception):
    with pytest.raises(expected_exception):
        Meta_meta = build_Meta_meta()
        Meta = Meta_meta(name="Meta", parents=[], init_props=init_props)


@pytest.mark.depends(name='valid_meta_meta')
def test_valid_meta_meta_instantiation(build_Meta_meta):
    Meta_meta = build_Meta_meta()
    Meta = Meta_meta(name="Meta", parents=[], init_props={'b': 'valid_string', 'c': 123})
    assert Meta.a == "MetaMetaProp"
    assert Meta.b == 'valid_string'
    assert Meta.c == 123
    assert Meta_meta.instances[0] == Meta


@pytest.fixture(scope="module")
def build_Meta(build_Meta_meta):
    def builder():
        Meta_meta = build_Meta_meta()
        Meta = Meta_meta(name="Meta", parents=[], init_props={'b': 'valid_string', 'c':123})
        return Meta
    return builder


@pytest.mark.depends(on=['test_valid_meta_meta_instantiation'])
def test_valid_meta_props(build_Meta):
    Meta = build_Meta()
    assert Meta.a == "MetaMetaProp"
    assert Meta.b == 'valid_string'
    assert Meta.c == 123


@pytest.mark.depends(on=['test_valid_meta_meta_instantiation'])
def test_change_final_property_b_not_possible(build_Meta):
    with pytest.raises(ChangeFinalPropException):
        Meta = build_Meta()
        Meta.b = 123


@pytest.mark.depends(on=['test_valid_meta_meta_instantiation'])
def test_change_not_final_property_c_is_possible(build_Meta):
    Meta = build_Meta()
    Meta.c = 456
    assert Meta.c == 456


@pytest.mark.depends(on=['test_valid_meta_meta_instantiation'])
def test_change_undue_property_d_is_not_possible(build_Meta):
    Meta = build_Meta()
    with pytest.raises(UnduePropInstantiationException):
        Meta.d = 345


@pytest.mark.depends(on=['test_valid_meta_meta_instantiation'])
@pytest.mark.parametrize(
    ("init_props", "expected_exception"), ([
        ({'e': 'valid_string'}, UninitialisedPropException),  # d is missing
        ({'d': 123}, ConstraintViolationException),  # d is not function
        ({'d': lambda x: x, 'e': '123'}, UnduePropInstantiationException),  # e only at next instant.
        ({'not_existing_prop': 2345}, UndefinedPropsException)  # prop not defined at all
    ])
)
def test_invalid_meta_instantiation(build_Meta, init_props, expected_exception):
    with pytest.raises(expected_exception):
        Meta = build_Meta()
        Cl_s = Meta(name="Meta", parents=[], init_props=init_props)


@pytest.mark.depends(on=['test_valid_meta_meta_instantiation'])
def test_valid_meta_instantiation(build_Meta):
    Meta = build_Meta()
    Cl_ss = Meta(name="Cl_ss", parents=[], init_props={'d': lambda x: ("Hello " + str(x))})
    assert Cl_ss.d("World") == "Hello World"


@pytest.fixture(scope="module")
def build_Cl_ss(build_Meta):
    def builder():
        Meta = build_Meta()
        Cl_ss = Meta(name="Cl_ss", parents=[], init_props={'d': lambda x: ("Hello " + str(x))})
        return Cl_ss

    return builder


@pytest.mark.depends(on=['test_valid_meta_instantiation'])
def test_valid_Cl_ss_props(build_Cl_ss):
    Cl_ss = build_Cl_ss()
    assert Cl_ss.a == "MetaMetaProp"
    assert Cl_ss.c == 123
    assert isinstance(Cl_ss.d, FunctionType)
    assert Cl_ss.d("World") == "Hello World"


@pytest.mark.depends(on=['test_valid_meta_instantiation'])
def test_b_disappeared_in_Cl_ss_props(build_Cl_ss):
    Cl_ss = build_Cl_ss()
    with pytest.raises(UndefinedPropsException):
        print(Cl_ss.b)


@pytest.mark.depends(on=['test_valid_meta_instantiation'])
@pytest.mark.parametrize(
    ("init_props", "expected_exception"), ([
        ({}, UninitialisedPropException),  # e is missing
        ({'e': 123}, ConstraintViolationException),  # e is not string
        ({'not_existing_prop': 2345}, UndefinedPropsException)  # prop not defined at all
    ])
)
def test_invalid_cl_ss_instantiation(build_Cl_ss, init_props, expected_exception):
    with pytest.raises(expected_exception):
        Cl_ss = build_Cl_ss()
        inst_nce = Cl_ss(name="inst_nce", init_props=init_props, declare_as_instance=True)


@pytest.mark.depends(on=['test_valid_meta_instantiation'])
def test_valid_cl_ss_instantiation(build_Cl_ss):
    Cl_ss = build_Cl_ss()
    inst_nce = Cl_ss(name="inst_nce", init_props={'e': "Finally reached Instance Level"}, declare_as_instance=True)
    assert inst_nce.a == "MetaMetaProp"
    assert inst_nce.c == 123
    assert inst_nce.d("World") == "Hello World"
    assert inst_nce.e == "Finally reached Instance Level"


@pytest.fixture(scope="module")
def build_inst_nce(build_Cl_ss):
    def builder():
        Cl_ss = build_Cl_ss()
        inst_nce = Cl_ss(name="Instance",  init_props={'e': 'Finally reached Instance Level'}, declare_as_instance=True)
        return inst_nce

    return builder

# @pytest.mark.depends(on=['test_valid_cl_ss_instantiation'])
def test_instantiate_instance_raise_exception(build_inst_nce):
    with pytest.raises(ClabjectDeclaredAsInstanceException):
        inst_nce = build_inst_nce()
        inst_nce(name="further_instance", init_props={})


@pytest.mark.depends(on=['test_valid_cl_ss_instantiation'])
def test_instance_of_chain(build_Meta_meta, build_Meta, build_Cl_ss, build_inst_nce):
    inst_nce = build_inst_nce()
    Cl_ss = build_Cl_ss()
    Meta = build_Meta()
    Meta_meta = build_Meta_meta()

    # test homogenous use of instance_of
    assert inst_nce.instance_of() == Cl_ss
    assert Cl_ss.instance_of() == Meta
    assert Meta.instance_of() == Meta_meta
    assert Meta_meta.instance_of() == Clabject


# Underlying Schema of Second Instantiation Hierarchy
# Focus here: Multilevel Constraints + Behaviour of Methods on different levels
# MM_3 (In itself at Level 2, but due to M_2.z prop lifted to Level 3)
#   Definitions
#   <prop_name>: <constraints> [= <prop_value>] <steps_to_instantiation>, <steps_from_instantiation>, [final], [method]
#       o : 2ndOrderInstance_of_Meta_meta = Cl_ss 0,2, final
#       i :int 1,*
#       m :function 1,*, final, method

#   State:
#       o = Cl_ss


# MM_3 => M_2A {i = 333, m = lambda obj, x : obj.i = obj.i * x}
# M_2A
#    Definitions
#       z: AnyOrderInstance_of_Meta_meta, 2,*, final
#   State After Init:
#       o = Cl_ss
#       i = 333
#       m = lambda obj, x : obj.i = obj.i * x
# State After calling M_2.m(x=3)
#       o = Cl_ss
#       i = 999
#       m = lambda obj, x : obj.i = obj.i * x

# M_2A => C_1 {i=100}
# C_1
# State After Init
#       o = Cl_ss
#       i = 100
#       m = lambda obj,x : obj.i = obj.i * x

# State After calling C_1.m(x=10)
#       o = Cl_ss
#       i = 1000
#       m = lambda obj, x : obj.i = obj.i * x


# C_1 => i_0 { z=inst_nce }
# i_0
#     State After Init:
#       i = 100
#       m = lambda obj,x : obj.i = obj.i * x
#       z = inst_nce

@pytest.fixture(scope="module")
def build_MM_3(build_Meta_meta, build_Cl_ss):
    Meta_meta = build_Meta_meta()
    Cl_ss = build_Cl_ss()

    def builder(prop_o=Cl_ss):
        MM_3 = Clabject(name="MM_3", parents=[], init_props={})
        snd_order_instance_of_meta_meta_constraint = prop_constraint_ml_instance_of_th_order_functional(Meta_meta, 2)

        prop_o = SimpleProp(prop_name="o",
                            constraints=[snd_order_instance_of_meta_meta_constraint],
                            steps_to_instantiation=0,
                            steps_from_instantiation=2,
                            is_final=True,
                            prop_value=prop_o)

        prop_i = SimpleProp(prop_name="i",
                            constraints=[is_int_constraint],
                            steps_to_instantiation=1,
                            steps_from_instantiation=math.inf,
                            is_final=False)

        prob_m = MethodProp(prop_name="m",
                              constraints=[is_function_constraint],
                              steps_to_instantiation=1,
                              steps_from_instantiation=math.inf,
                              is_final=True)

        MM_3.define_props([prop_o, prop_i, prob_m])
        return MM_3

    return builder


def test_build_mm3_with_invalid_prop_o_as_given_value_is_no_member_of_inst_chain(build_MM_3):
    with pytest.raises(ConstraintViolationException):
        MM_3 = build_MM_3(prop_o=34)


def test_build_mm3_with_invalid_prop_o_fails_due_to_too_many_instant_steps(build_MM_3, build_inst_nce):
    with pytest.raises(ConstraintViolationException):
        inst_ce = build_inst_nce()
        MM_3 = build_MM_3(prop_o=inst_ce)


def test_build_mm3_with_invalid_prop_o_fails_due_to_too_few_instant_steps(build_MM_3, build_Meta):
    with pytest.raises(ConstraintViolationException):
        Meta = build_Meta()
        MM_3 = build_MM_3(prop_o=Meta)


def test_build_valid_mm3(build_MM_3):
    MM_3 = build_MM_3()
    assert MM_3.o.__name__ == "Cl_ss"



@pytest.mark.depends(on=['test_build_valid_mm3'])
@pytest.mark.parametrize(
    ("init_props", "expected_exception"), ([
        ({}, UninitialisedPropException),  # i, m are missing
        ({'i': 123,  'm': lambda: print("no params")}, ConstraintViolationException),  # method def requires params
        ({'not_existing_prop': 2345}, UndefinedPropsException)  # prop not defined at all
    ])
)
def test_build_m2_with_invalid_props_fails(build_MM_3, init_props, expected_exception):
    with pytest.raises(expected_exception):
        MM3 = build_MM_3()
        M2_A = MM3(name="M2_A", parents=[], init_props=init_props)


def test_build_m2_a_with_valid_props_shows_expected_behaviour(build_Meta_meta, build_MM_3):
    Meta_meta = build_Meta_meta()
    MM_3 = build_MM_3()
    def manipulate_i_by_factor_x(obj, x):
        obj.i = obj.i * x

    M2_A = MM_3(name="M2_A", parents=[],
                init_props={'i': 333, 'm': manipulate_i_by_factor_x})

    assert type(M2_A).__name__ == "MetaClabject"
    assert M2_A.i == 333
    M2_A.m(x=3)
    assert M2_A.i == 999

    any_order_instance_of_Meta_meta_constraint = prop_constraint_ml_instance_of_th_order_functional(Meta_meta)
    z_prop = SimpleProp(prop_name="z",
                        steps_to_instantiation=2,
                        steps_from_instantiation=math.inf,
                        constraints=[any_order_instance_of_Meta_meta_constraint],
                        is_final=True)
    M2_A.define_props([z_prop])
    assert M2_A.__ml_props__['z'] is not None


@pytest.fixture(scope="module")
def build_M2_A(build_MM_3, build_Meta_meta):
    def builder():
        MM_3 = build_MM_3()

        def manipulate_i_by_factor_x(obj, x):
            obj.i = obj.i * x
        M2_A = MM_3(name="M2_A", parents=[], init_props={'i': 333, 'm': manipulate_i_by_factor_x})
        Meta_meta = build_Meta_meta()
        any_order_instance_of_Meta_meta_constraint = prop_constraint_ml_instance_of_th_order_functional(Meta_meta)
        z_prop = SimpleProp(prop_name="z",
                            steps_to_instantiation=2,
                            steps_from_instantiation=math.inf,
                            constraints=[any_order_instance_of_Meta_meta_constraint],
                            is_final=True)
        M2_A.define_props([z_prop])

        return M2_A

    return builder


@pytest.mark.depends(on=['test_build_m2_a_with_valid_props_shows_expected_behaviour'])
@pytest.mark.parametrize(
    ("init_props", "expected_exception"), ([
        ({'z': 123}, UnduePropInstantiationException),
        ({'i': 'sdf'}, ConstraintViolationException)
    ]))
def test_build_c1_with_invalid_props_fails(build_M2_A, init_props, expected_exception):
    with pytest.raises(expected_exception):
        M2_A = build_M2_A()
        C1 = M2_A(name="C1", parents=[], init_props=init_props)


def test_build_c1_with_valid_props_shows_expected_behaviour(build_M2_A):
    M2_A = build_M2_A()
    C1 = M2_A(name="C1", parents=[], init_props={"i": 100})
    assert C1.i == 100
    assert M2_A.i == 333  # parent clabject's state is not affected
    C1.m(x=10)
    assert C1.i == 1000
    assert M2_A.i == 333
    assert type(C1).__name__ == "MetaClabject"


@pytest.fixture(scope="module")
def build_C1(build_M2_A):
    def builder():
        M2_A = build_M2_A()
        C1 = M2_A(name="C1", parents=[], init_props={"i": 100})
        return C1
    return builder


@pytest.mark.depends(on=['test_build_c1_with_valid_props_shows_expected_behaviour'])
@pytest.mark.parametrize(
    ("init_props", "expected_exception"), ([
        ({}, UninitialisedPropException),  # prop z is missing
        ({'z': 123}, ConstraintViolationException)  # wrong type, not member of instance chain at all
    ]))
def test_build_i_0_with_invalid_props_fails(build_C1, init_props, expected_exception):
    with pytest.raises(expected_exception):
        C1 = build_C1()
        i_0 = C1(name="i_o", init_props=init_props)


def test_build_i_0_with_valid_prop(build_C1, build_inst_nce):
    C1 = build_C1()
    inst_nce = build_inst_nce()
    i_0 = C1(name="i_0", init_props={'z': inst_nce})
    assert i_0.i == 100
    assert i_0.z.e == "Finally reached Instance Level"


# Focus Deferred Instantiation
def test_build_M_2B_after_speed_adjustment_on_MM_3(build_MM_3):
    MM_3 = build_MM_3()
    MM_3.adjust_instantiation_speed(speed_adjustments={"m": 1})
    assert MM_3.__ml_props__["m"].steps_to_instantiation == 2
    M2_B = MM_3(name="M2_B", parents=[], init_props={"i": 333})
    assert M2_B.__ml_props__["m"].steps_to_instantiation == 1
    assert M2_B.i == 333
    with pytest.raises(UnduePropInstantiationException):
        M2_B = MM_3(name="M2_B", parents=[], init_props={"i": 333, "m": lambda: print("to early")})

# Focus Accelerated Instantiation
# Meta_meta => Meta {adjustspeed{e=-2}, b = "valid_string", c=123, e="Accelerated e Instantiation"}
def test_build_Meta_B_after_speed_adustment_on_Meta_meta(build_Meta_meta):
    Meta_meta = build_Meta_meta()
    Meta_meta.adjust_instantiation_speed(speed_adjustments={"e": -2})
    assert Meta_meta.__ml_props__["e"].steps_to_instantiation == 1
    Meta = Meta_meta(name="Meta", parents=[], init_props={'b': 'valid_string','c': 123,'e': 'now earlier'})

    assert Meta.e == 'now earlier'
    with pytest.raises(UninitialisedPropException):
        Meta = Meta_meta(name="Meta", parents=[], init_props={'b': 'valid_string','c': 123})


# Focus Inheritance, Methods that should be applicable to classes/ clabjects must be defined as classmethods
# At instance Level also usual methods can be called
class TraditionalClass:
    @classmethod
    def get_probA(cls):
        return cls.a

    @classmethod
    def get_propB(cls):
        return cls.b

    @classmethod
    def update_propC(cls, new_value: int):
        cls.c = new_value

    @classmethod
    def get_probC(cls):
        return cls.c


class AnotherParentClass:
    @classmethod
    def get_probE(cls):
        return cls.e

    @classmethod
    def multiply_c(cls, x: int):
        cls.c = cls.c * x

def test_build_Meta_C_with_inheritance(build_Meta_meta):
    Meta_meta = build_Meta_meta()
    Meta = Meta_meta(name="Meta", parents=[TraditionalClass], init_props={'b': "valid_string", 'c': 123})
    assert Meta.get_probA() == "MetaMetaProp"
    assert Meta.get_propB() == "valid_string"
    assert Meta.get_probC() == 123
    Meta.update_propC(333)
    assert Meta.get_probC() == 333
    Cl_ss = Meta(name="Cl_ss", parents=[AnotherParentClass], init_props={'d': lambda x: ("Hello " + str(x))})
    assert Cl_ss.get_probC() == 333
    Cl_ss.multiply_c(3)
    assert Cl_ss.get_probC() == 999

    assert Meta.get_probC() == 333
    assert Cl_ss.get_probA() == "MetaMetaProp"
    with pytest.raises(UndefinedPropsException):
        Cl_ss.get_probB()  # Prob B has vanished
    inst_ce = Cl_ss(name="inst_ce",  init_props= {'e': 'Finally reached instance level'})
    assert inst_ce.get_probA() == "MetaMetaProp"
    assert inst_ce.get_probC() == 999
    assert inst_ce.get_probE() == "Finally reached instance level"

