from inspect import signature as sig
from typing import Tuple, Union, List, Any
from abc import abstractmethod

from multilevel_py.constraints import PropValueConstraint, ReInitPropConstr
from multilevel_py.exceptions import InvalidMultiplicityTupleException, InvalidPropValueConstraintException


class BaseClabjectProp:
    """
    Base class of a ClabjectProp, i.e. an enhanced attribute that is capable of "deferred instantiation"
    """
    def __init__(self, prop_name: str,
                 steps_to_instantiation: int,
                 steps_from_instantiation: Union[int, float],
                 constraints: List[PropValueConstraint] = [],
                 is_final: bool = False,
                 prop_value: Any = None,
                 default_value: Any = None
                 ):
        """
        Args:
            prop_name: The name of the property, which must be unique for the given clabject

            steps_to_instantiation:  The number of steps until the property is instantiated, i.e. assigned with a value.
                                     A value of 1 means that the property has to be instantiated in the next instantiation step.

            steps_from_instantiation: The number of steps the property continues to exist down the intantiation chain after
                                      being instantiated. If set to 0 the property appears only at the clabject it was instantiated on.
                                      If set to math.inf it is visible for all direct and indirect instances down the instantiation hierarchy.

            constraints: A List of PropValueConstraints that restrict the space of acceptable property values. A value is only set or updated
                        if it passes through all constraints, otherwise a :class:`exceptions.ConstraintViolationException` is thrown

            is_final: Indicating whether the property can be changed after its first instantiation.

            prop_value: The value that is assigned to the property during an instantiation step. Can be any python object
                        including functions.

            default_value: optional default_value of the property, used at instantiation if no prop_value is provided
        """



        assert steps_to_instantiation >= 0
        assert steps_from_instantiation >= 0
        assert isinstance(constraints, list)
        from multilevel_py.constraints import PropValueConstraint
        for constr in constraints:
            if not isinstance(constr, PropValueConstraint):
                raise InvalidPropValueConstraintException(constr=constr)
        assert isinstance(is_final, bool)
        self.prop_name = prop_name
        self.steps_to_instantiation = steps_to_instantiation
        self.steps_from_instantiation = steps_from_instantiation
        self.constraints = constraints
        self.is_final = is_final
        self.prop_value = prop_value
        self.default_value = default_value
        self.re_init_prop_constr: ReInitPropConstr = None
        for ts_constr in self.type_specific_constraints():
            ts_constr.type_specific = True
            self.constraints.append(ts_constr)

    @abstractmethod
    def type_specific_constraints(self) -> List[PropValueConstraint]:
        """
        Declare type specific constraints that will be appended to self.constraints
        """
        pass

    @abstractmethod
    def get_viz_value_str(self) -> str:
        """

        Returns:
            a concrete syntax friendly string for the given prop value
        """
        pass


class SimpleProp(BaseClabjectProp):
    """
    A property of a Clabject, that is meant to hold a simple (single primitive) value
    """
    def __init__(self, prop_name: str,
                 steps_to_instantiation: int,
                 steps_from_instantiation: Union[int, float],
                 constraints: List[PropValueConstraint] = [],
                 is_final: bool = False,
                 prop_value: Any = None,
                 default_value: Any = None
                 ):

        super(SimpleProp, self).__init__(
            prop_name=prop_name,
            steps_to_instantiation=steps_to_instantiation,
            steps_from_instantiation=steps_from_instantiation,
            constraints=constraints,
            is_final=is_final,
            prop_value=prop_value,
            default_value=default_value
        )

    def type_specific_constraints(self):
        return []

    def get_viz_value_str(self):
        return str(self.prop_value)

class AssociationProp(BaseClabjectProp):
    """
    A Property of a clabjec that is meant to hold an associated clabject
    """
    def __init__(self, prop_name: str,
                 steps_to_instantiation: int,
                 steps_from_instantiation: Union[int, float],
                 constraints: List[PropValueConstraint] = [],
                 is_final: bool = False,
                 prop_value: Any = None,
                 default_value: Any = None
                 ):
        super(AssociationProp, self).__init__(
            prop_name=prop_name,
            steps_to_instantiation=steps_to_instantiation,
            steps_from_instantiation=steps_from_instantiation,
            constraints=constraints,
            is_final=is_final,
            prop_value=prop_value,
            default_value=default_value
        )
    def type_specific_constraints(self):
        from multilevel_py.core import is_clabect_or_empty_constr
        return [is_clabect_or_empty_constr]

    def get_viz_value_str(self):
        return "Associated Clabject: " + str(self.prop_value)


class CollectionDescription:
    """
    Defines a collection property in terms of multiplicity and collection member constraints
    """

    def __init__(self, min_max: Tuple[int, int] = (), member_value_constr=None):
        """
        Args:
            min_max: A tuple with defining the min and max number of collection members (inclusive logic)
            member_value_constr: A PropValueConstraint that is applied on all collection members
        """
        self.min_max = min_max
        self.member_value_constr = member_value_constr


class CollectionProp(BaseClabjectProp):
    """
    A property of a clabject that is meant to hold a collection, i.e. a multi-value property of a Clabject
    """

    def __init__(self, prop_name: str,
                 steps_to_instantiation: int,
                 steps_from_instantiation: Union[int, float],
                 constraints: List[PropValueConstraint] = [],
                 is_final: bool = False,
                 prop_value: Any = None,
                 default_value: Any = None,
                 collection_desc: CollectionDescription = None,
                 ):
        assert isinstance(collection_desc, CollectionDescription)
        self.collection_desc = collection_desc
        self.collection_member_constr = None

        super(CollectionProp, self).__init__(
            prop_name=prop_name,
            steps_to_instantiation=steps_to_instantiation,
            steps_from_instantiation=steps_from_instantiation,
            constraints=constraints,
            is_final=is_final,
            prop_value=prop_value,
            default_value=default_value
        )

        if collection_desc.min_max:
            if not (len(collection_desc.min_max) == 2 and (
                    0 <= collection_desc.min_max[0] <= collection_desc.min_max[1])):
                raise InvalidMultiplicityTupleException(provided_tuple=collection_desc)

        self.collection_desc = collection_desc
        self.collection_member_constr = None

    def type_specific_constraints(self):
        _constraints = []
        if self.collection_desc is not None:
            from multilevel_py.constraints import is_collection_constraint
            _constraints.append(is_collection_constraint)

            if self.collection_desc.min_max:
                from multilevel_py.constraints import prop_constraint_collection_multiplicity_functional
                mult_constr = prop_constraint_collection_multiplicity_functional(
                    min_member_number=self.collection_desc.min_max[0],
                    max_member_number=self.collection_desc.min_max[1],
                    eval_on_init=False
                )
                _constraints.append(mult_constr)

            if self.collection_desc.member_value_constr:
                from multilevel_py.constraints import prop_constraint_collection_member_functional
                self.collection_member_constr = prop_constraint_collection_member_functional(
                    member_constr_func=self.collection_desc.member_value_constr,
                    eval_on_init=True)
                _constraints.append(self.collection_member_constr)
            return _constraints

    def get_viz_value_str(self):
        return str(self.prop_value)


class MethodProp(BaseClabjectProp):
    """
    A property of a clabject that is meant to hold a method object
    """
    def __init__(self, prop_name: str,
                 steps_to_instantiation: int,
                 steps_from_instantiation: Union[int, float],
                 constraints: List[PropValueConstraint] = [],
                 is_final: bool = False,
                 prop_value: Any = None,
                 default_value: Any = None
                 ):

        super(MethodProp, self).__init__(
            prop_name=prop_name,
            steps_to_instantiation=steps_to_instantiation,
            steps_from_instantiation=steps_from_instantiation,
            constraints=constraints,
            is_final=is_final,
            prop_value=prop_value,
            default_value=default_value
        )

    def type_specific_constraints(self):
        from multilevel_py.constraints import value_can_be_bound_as_method_constraint
        return [value_can_be_bound_as_method_constraint]

    def get_viz_value_str(self):
        res_str = str(self.prop_value)
        if hasattr(self.prop_value, "__impl_origin__"):
            res_str = "Impl. from " + self.prop_value.__impl_origin__ + ": " + \
                      self.prop_value.__name__ + str(sig(self.prop_value))

        return res_str


class StateConstraintProp(BaseClabjectProp):
    """
    A property of a Clabject, that is meant to hold a StateConstraint
    """
    def __init__(self, prop_name: str,
                 steps_to_instantiation: int,
                 steps_from_instantiation: Union[int, float],
                 constraints: List[PropValueConstraint] = [],
                 is_final: bool = False,
                 prop_value: Any = None,
                 default_value: Any = None
                 ):

        super(StateConstraintProp, self).__init__(
            prop_name=prop_name,
            steps_to_instantiation=steps_to_instantiation,
            steps_from_instantiation=steps_from_instantiation,
            constraints=constraints,
            is_final=is_final,
            prop_value=prop_value,
            default_value=default_value
        )

    def type_specific_constraints(self):
        from .constraints import prop_constraint_py_isinstance_functional
        from .constraints import ClabjectStateConstraint
        is_clabject_state_constraint = prop_constraint_py_isinstance_functional(ClabjectStateConstraint, True)
        return [is_clabject_state_constraint]

    def get_viz_value_str(self):
        res_str = "StateConstraint: " + str(self.prop_value.name)
        return res_str
