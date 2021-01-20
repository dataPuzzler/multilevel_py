import math
from collections import defaultdict
from collections.abc import Iterable
from datetime import time, date, timedelta, datetime
from inspect import signature
from types import FunctionType
from typing import Callable, Any, Union, Tuple, Collection, List
from multilevel_py.exceptions import InvalidInstantiationOrderException, \
    NotAClabjectException, InvalidPropValueConstraintException, TypeSpecificConstraintRemovalException


class BaseConstraint:
    """
    Abstract Base of all kind of clabject constraints
    """
    def __init__(self, name: str, violation_reason=""):
        self.name = name
        self.violation_reason = violation_reason


class PropValueConstraint(BaseConstraint):
    """
    A callable constraint imposed on the values of clabject props
    """
    def __init__(self, name: str, eval_value_func: Callable[[Any], str], eval_on_init: bool):
        """
        Args:
            name: the name of the constraint
            eval_value_func: an evaluation function, that returns an empty string for valid prop values and
                             a non empty string for prop values that violate the constraint
            eval_on_init: a value indicating whether the constr should be evaluated on (re) init
        """
        super(PropValueConstraint, self).__init__(name=name)
        self.eval_value_func = eval_value_func
        self.eval_on_init = eval_on_init
        self.type_specific = False

    def __call__(self, prop_value: Any) -> bool:
        self.violation_reason = ""
        if self.eval_value_func(prop_value):
            self.violation_reason = self.eval_value_func(prop_value)
            return False
        return True


class ClabjectStateConstraint(BaseConstraint):
    """
     A callable constraint that is evaluated on the current clabject state
    """
    def __init__(self, name: str, eval_clabject_func: Callable[[Any], str]):
        """
        Args:
            name: The name of the constraint
            eval_clabject_func: an evaluation func with of the following structure: Callable(current_clabject) -> str
        """
        super(ClabjectStateConstraint, self).__init__(name=name)
        self.eval_clabject_func = eval_clabject_func

    def __call__(self, current_clabject: Any) -> bool:
        self.violation_reason = ""
        if self.eval_clabject_func(current_clabject):
            self.violation_reason = self.eval_clabject_func(current_clabject)
            return False
        return True


def prop_constraint_py_isinstance_functional(expected_type, eval_on_init=True) -> PropValueConstraint:
    """
    Generate prop value constraints using Pythons traditional isinstance facility

    Args:
        expected_type: the expected type or class object
        eval_on_init: value indicating whether the constr should be evaluated on (re) init

    Returns:
        a parameterised, callable PropValueConstraint object
    """

    def eval_value_func(value) -> str:
        if not isinstance(value, expected_type):
            return "{VALUE} is not of the expected type {TYPE}".format(
                VALUE=str(value), TYPE=expected_type.__name__
            )
        else:
            return ""

    name = "is_of_{TYPE}".format(TYPE=expected_type.__name__)
    return PropValueConstraint(name=name, eval_value_func=eval_value_func, eval_on_init=eval_on_init)


is_str_constraint = prop_constraint_py_isinstance_functional(str)
is_int_constraint = prop_constraint_py_isinstance_functional(int)
is_float_constraint = prop_constraint_py_isinstance_functional(float)
is_bool_constraint = prop_constraint_py_isinstance_functional(bool)
is_function_constraint = prop_constraint_py_isinstance_functional(FunctionType)
is_date_constraint = prop_constraint_py_isinstance_functional(date)
is_time_constraint = prop_constraint_py_isinstance_functional(time)
is_datetime_constraint = prop_constraint_py_isinstance_functional(datetime)
is_timedelta_constraint = prop_constraint_py_isinstance_functional(timedelta)
is_set_constraint = prop_constraint_py_isinstance_functional(set)

Instantiation_order_type = Union[int, Tuple[int, int], None]


def prop_constraint_ml_instance_of_th_order_functional(expected_clabject_type,
                                                       instantiation_order: Instantiation_order_type = None,
                                                       eval_on_init=True):
    """
    Generate prop value constraints using the instance_mechanism provided by the multilevel_py package

    Args:
        expected_clabject_type: the expected_clabject_type values are supposed to be instances of
        instantiation_order: the number of permissible instantiation steps between value and expected_clabject_type,
                             if None instances of any order are allowed,
                             if int only this exact number of instantiation steps is tolerated,
                             if (min, max) tuple the inclusive interval of integers between min and max is tolerated
        eval_on_init: value indicating whether the constr should be evaluated on (re) init

    Returns:
        a parameterised, callable PropValueConstraint object

    """
    from multilevel_py.core import is_clabject
    from multilevel_py.core import Clabject

    def check_int_avove_zero(value) -> bool:
        if not isinstance(value, int):
            return False
        elif value < 1:
            return False
        else:
            return True

    if instantiation_order is None:
        min_inst_steps = 1
        max_inst_steps = math.inf
        order_str = "any"

    elif isinstance(instantiation_order, int):
        if not check_int_avove_zero(instantiation_order):
            raise InvalidInstantiationOrderException(provided_instantiation_order=instantiation_order)
        else:
            min_inst_steps = instantiation_order
            max_inst_steps = instantiation_order
            order_str = str(instantiation_order)

    elif type(instantiation_order) is tuple:
        if not len(instantiation_order) == 2:
            raise InvalidInstantiationOrderException(provided_instantiation_order=instantiation_order)
        else:
            if not (check_int_avove_zero(instantiation_order[0]) and
                    check_int_avove_zero(instantiation_order[1])):
                raise InvalidInstantiationOrderException(provided_instantiation_order=instantiation_order)
            else:
                min_inst_steps = instantiation_order[0]
                max_inst_steps = instantiation_order[1]
                order_str = "_".join(["between", str(min_inst_steps), "and", str(max_inst_steps)])

    def eval_value_func(value) -> str:
        if not is_clabject(value):
            return str(NotAClabjectException(obj=value))
        inst_steps = 0
        current_clab = value

        while inst_steps < min_inst_steps:
            # check chain end or premature instance
            if current_clab == Clabject or current_clab == expected_clabject_type:
                return "Instantiation order of given clabject is to low."

            current_clab = current_clab.instance_of()
            inst_steps += 1

        # section of instantiation chain that is valid
        while current_clab != Clabject and inst_steps <= max_inst_steps:
            if current_clab == expected_clabject_type:
                return ""
            current_clab = current_clab.instance_of()
            inst_steps += 1

        return "Instantiation order of given clabject value is to high"

    name = "{ORDER}_order_ml_instance_of_{TYPE}".format(ORDER=order_str, TYPE=str(expected_clabject_type.__name__))
    return PropValueConstraint(name=name, eval_value_func=eval_value_func, eval_on_init=True)


def prop_constraint_is_th_order_instance_of_clabject_set_functional(expected_values: set, order: int = 1,
                                                                    eval_on_init=True):
    """
    Generates a PropValueConstraint that checks whether the given value is an (given) order instance of one of
    the specified clabjects

    Args:
        expected_values: a set of clabjects
        order: an integer, describing how often the instance_of operation should be applied
        eval_on_init: value indicating whether the constr should be evaluated on (re) init

    Returns:
        a parameterised, callable PropValueConstraint object

    """
    from multilevel_py.core import is_clabject

    def eval_value_func(value: Any):
        if not is_clabject(value):
            return str(NotAClabjectException(value))
        inst_order = order if order else 1
        while inst_order > 0:
            value = value.instance_of()
            inst_order = inst_order - 1
        if value in expected_values:
            return ""
        else:
            return "The given clabject value is not a {ORDER} order instance of any of the accepted clabjects".format(
                ORDER=order
            )

    name = "{ORDER}_order_instance_of_clabject_set_{CLABJECTS}".format(ORDER=order,
                                                                       CLABJECTS={c.__name__ for c in expected_values})

    return PropValueConstraint(name=name, eval_value_func=eval_value_func, eval_on_init=eval_on_init)


def prop_constraint_value_is_collection_functional(eval_on_init=True):
    """
    Generates a PropValueConstraint that checks whether the property value is a valid collection

    Args:
        eval_on_init: value indicating whether the constr should be evaluated on (re) init
    """
    def eval_func(value: Any) -> str:
        res = ""
        if not isinstance(value, Iterable) or isinstance(value, str):
            res = str(value) + "is not a collection"
        return res

    name = "is_collection"
    return PropValueConstraint(name=name, eval_value_func=eval_func, eval_on_init=eval_on_init)


is_collection_constraint = prop_constraint_value_is_collection_functional(eval_on_init=True)


def prop_constraint_collection_member_functional(
        member_constr_func: PropValueConstraint,
        filter_func: Callable[[Collection], Collection] = None, eval_on_init=True):
    """
    Generates a PropValueConstraint that is applied on (selected) members of a collection prop value

    Args:
        member_constr_func: A PropValueConstraint that each collection member must satisfy
        filter_func: A filter function that takes the whole collection and returns only the members,
                     the member_constr_func should be checked on
        eval_on_init: value indicating whether the constr should be evaluated on (re) init

    Returns:
        a parameterised, callable PropValueConstraint object

    """

    def eval_func(collection_value):
        res_str = ""
        eval_collection = filter_func(collection_value) if filter_func else collection_value
        for member in eval_collection:
            if not member_constr_func(member):
                res_str += "Member {MEMBER} failed for reason: {REASON}".format(
                    MEMBER=str(member),
                    REASON=member_constr_func.violation_reason)
                res_str += "\n"
        return res_str

    name = "_".join(["check", member_constr_func.name, "on_collection_members"])
    return PropValueConstraint(name=name, eval_value_func=eval_func, eval_on_init=eval_on_init)


def prop_constraint_collection_multiplicity_functional(min_member_number: int, max_member_number: int,
                                                       eval_on_init=False):
    def eval_func(collection_value) -> str:
        res_str = ""
        if not hasattr(collection_value, "__len__"):
            res_str += "The given value {VALUE} is no collection".format(VALUE=str(collection_value))

        if not min_member_number <= len(collection_value) <= max_member_number:
            res_str += "The collection holds {N} members".format(N=len(collection_value))
        return res_str

    name = "collection_multiplicity_between_{MIN}_and_{MAX}".format(MIN=min_member_number,
                                                                               MAX=max_member_number)
    return PropValueConstraint(name=name, eval_value_func=eval_func, eval_on_init=eval_on_init)


def prop_value_can_be_bound_as_method_functional(eval_on_init=True):
    """
    Args:
        eval_on_init: value indicating whether the constr should be evaluated on (re) init

    Returns:
         a PropValueConstraint that determines whether the provided value can serve as method
    """
    def eval_func(value) -> str:
        res_str = ""
        if not isinstance(value, FunctionType):
            res_str = "The given value is not a function"
        else:
            sig = signature(value)

            # Methods must take obj. they bind to as first param
            if len(sig.parameters) == 0:
                res_str = "The given signature of the given function takes no parameters"
            return res_str

    name = "can_be_method_constraint"
    return PropValueConstraint(name=name, eval_value_func=eval_func, eval_on_init=eval_on_init)


value_can_be_bound_as_method_constraint = prop_value_can_be_bound_as_method_functional(eval_on_init=True)


def prop_constraint_or_functional(constraint_a: PropValueConstraint, constraint_b: PropValueConstraint):
    """
    Args:
        constraint_a: the fst constraint
        constraint_b: the snd constraint

    Returns:
        a combined PropValueConstraint, in which at least one of constraint_a and constraint_b must be fulfilled
    """

    def eval_func(value):
        constraint_a(value)
        constraint_b(value)
        res = ""
        if constraint_a.violation_reason and constraint_b.violation_reason:
            res += constraint_a.violation_reason
            res += constraint_b.violation_reason
        return res

    name = constraint_a.name + "_OR_" + constraint_b.name
    eval_on_init = constraint_a.eval_on_init and constraint_b.eval_on_init  # conservative
    return PropValueConstraint(name=name, eval_value_func=eval_func, eval_on_init=eval_on_init)


def prop_constraint_and_functional(constraint_a: PropValueConstraint, constraint_b: PropValueConstraint,
                                   eval_on_init=False):
    """
    Args:
        constraint_a: the fst constraint
        constraint_b: the snd constraint
        eval_on_init: (bool) value indicating whether the constr should be evaluated on (re) init

    Returns:
        a combined PropValue Constraint, in which both constraint_a, constraint_b must be fulfilled

    """

    def eval_func(value):
        constraint_a(value)
        constraint_b(value)
        res = ""
        if constraint_a.violation_reason or constraint_b.violation_reason:
            res += constraint_a.violation_reason
            res += constraint_b.violation_reason
        return res

    name = constraint_a.name + "_And_" + constraint_b.name
    eval_on_init = eval_on_init
    return PropValueConstraint(name=name, eval_value_func=eval_func, eval_on_init=eval_on_init)


class _EmptyValueClass(object):

    def __str__(self):
        return "EmptyValue"


EmptyValue = _EmptyValueClass()


def prop_constraint_optional_value_functional(constraint: PropValueConstraint):
    """
    Args:
        constraint: a PropValueConstraint

    Returns:
        a relaxed constraint of the given PropValueConstraint by tolerating also values of None as valid init value
    """

    def eval_func(value):
        if value == EmptyValue:
            return ""
        else:
            constraint(value)
            if constraint.violation_reason:
                return constraint.violation_reason + " or an EmptyValue"
            else:
                return ""

    name = constraint.name + "_OR_Empty"
    eval_on_init = constraint.eval_on_init
    return PropValueConstraint(name=name, eval_value_func=eval_func, eval_on_init=eval_on_init)


def eval_negative_value_func(value) -> str:
    if value < 0:
        return "The value must not be < 0"
    else:
        return ""


is_not_negative_constraint = PropValueConstraint(name="is_not_negative_constraint",
                                                 eval_value_func=eval_negative_value_func, eval_on_init=True)

is_not_negative_int_constraint = prop_constraint_and_functional(is_not_negative_constraint, is_int_constraint)


def prop_constraint_value_in_set_functional(expected_set: set, eval_on_init=True):
    """
    Generate PropValueConstraint that evaluates whether the given value is in the expected set

    Args:
        expected_set: a set of permitted values
        eval_on_init: (bool) value indicating whether the constr should be evaluated on (re) init

    Returns: a callable prop_constr instance

    """
    def eval_func(value):
        if value in expected_set:
            return ""
        else:
            return "The Value {VAL} is not in the expected set {SET}".format(VAL=value, SET=expected_set)
            return constraint.violation_reason

    return PropValueConstraint(name="is_in_set_constr", eval_value_func=eval_func, eval_on_init=eval_on_init)


class ConstrViolationDictFactory(defaultdict):
    """
    call ConstrViolationsFactory(list) to create dict like objects
    """

    def add_violations(self, violations: dict) -> None:
        """
        Args:
            violations: a dict with structure <prop_name: str> => <violation_reason: str>

        Returns:
            Nothing, updates the violationDict object

        """
        for constr_holder, constr in violations.items():
            if isinstance(constr, list):
                for c in constr:
                    self[constr_holder].append(c)
            else:
                self[constr_holder].append(constr)


def create_violated_constraint_dict():
    """
    Returns:
        an empty constraint_violation dict
    """
    from multilevel_py.constraints import ConstrViolationDictFactory
    all_violated_constraints = ConstrViolationDictFactory(list)
    return all_violated_constraints


class ReInitPropConstr:
    def __init__(self,
                 del_constr: List[PropValueConstraint] = [],
                 add_constr: List[PropValueConstraint] = []):
        """
        Forces the reinitialisation of a property value under updated constraints, if set on a clabject via
        :meth:`multilevel_py.core.MetaClabject.require_re_init_on_next_step`

        Args:
            del_constr: list of constraints to remove for the next re instantiation of the prop
            add_constr: list of constraints to validate for the next instantiation step
        """
        for constr in add_constr:
            if not isinstance(constr, PropValueConstraint):
                raise InvalidPropValueConstraintException(constr=constr)
        for constr in del_constr:
            if not isinstance(constr, PropValueConstraint):
                raise InvalidPropValueConstraintException(constr=constr)
            if constr.type_specific:
                raise TypeSpecificConstraintRemovalException(constr=constr)

        self.del_constr = del_constr
        self.add_constr = add_constr

    def __bool__(self):
        return True
