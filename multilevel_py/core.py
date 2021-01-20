import math
from copy import deepcopy
from typing import List, Callable, Any, Dict

from multilevel_py.clabject_prop import CollectionDescription, \
    BaseClabjectProp, SimpleProp, CollectionProp, MethodProp, StateConstraintProp, AssociationProp
from multilevel_py.constraints import create_violated_constraint_dict, ReInitPropConstr, PropValueConstraint
from multilevel_py.exceptions import UninitialisedPropException, ConstraintViolationException, \
    UndefinedPropsException, ChangeFinalPropException, UnduePropInstantiationException, \
    PropsAlreadyDefinedException, ReInitFinalPropException, \
    ReInitVanishingPropException, InconsistentCreateClabjectPropArgsException, ClabjectDeclaredAsInstanceException


def create_clabject_prop(n: str, t: int, f, c: List[Callable[[Any], bool]] = [],
                         i_f: bool = True,
                         i_m: bool = False,
                         i_sc: bool=False,
                         i_assoc: bool=False,
                         coll_desc: tuple = None, v=None, d=None):
    """
    Stable Interface for the creation of clabject properties, the suitable ClabjectProp class is chosen in dependence
    of the given attributes, see :meth:`clabject_prop.BaseClabjectProp.__init__`

    Args:
        n: shorthand for prop_name
        t: shorthand for steps_to_instantiation
        f: shorthand for steps_from_instantiation, integer or * (str) for remaining infinite may steps
        c: shorthand for constraints

        i_f: shorthand for is_final
        i_m: shorthand for is_method
        i_assoc: shorthand for is_association
        i_sc: shorthand for is_stateConstraint
        coll_desc: (min, max, member_constr) tuple that is translated to a CollectionDescription object
        v: shorthand for prop_value
        d: shorthand for default_value

    Returns:
        An obj which is an instance of a class that inherits from BaseClabjectProp
    """
    if sum([int(i_m), int(i_sc), int(bool(coll_desc)), int(i_assoc)]) > 1:
        raise InconsistentCreateClabjectPropArgsException(
            ex_msg="A Property can only be of one specific kind (Method, Association, Collection or StateConstraint)")

    f = math.inf if f == "*" else f
    c = [] if not len(c) else c
    coll_desc = CollectionDescription(min_max=(coll_desc[0], coll_desc[1]),
                                      member_value_constr=coll_desc[2]) if coll_desc else None

    if i_m:
        return MethodProp(
            prop_name=n,
            steps_to_instantiation=t,
            steps_from_instantiation=f,
            constraints=c,
            is_final=i_f,
            prop_value=v,
            default_value=d
        )

    elif i_assoc:
        return AssociationProp(
            prop_name=n,
            steps_to_instantiation=t,
            steps_from_instantiation=f,
            constraints=c,
            is_final=i_f,
            prop_value=v,
            default_value=d
        )

    elif i_sc:
        return StateConstraintProp(
            prop_name=n,
            steps_to_instantiation=t,
            steps_from_instantiation=f,
            constraints=c,
            is_final=i_f,
            prop_value=v,
            default_value=d
        )
    elif coll_desc is not None:
        return CollectionProp(
            prop_name=n,
            steps_to_instantiation=t,
            steps_from_instantiation=f,
            constraints=c,
            is_final=i_f,
            prop_value=v,
            default_value=d,
            collection_desc=coll_desc
        )
    else:
        return SimpleProp(
            prop_name=n,
            steps_to_instantiation=t,
            steps_from_instantiation=f,
            constraints=c,
            is_final=i_f,
            prop_value=v,
            default_value=d
        )


class ClabjectPropDict(Dict[str, BaseClabjectProp]):
    """
    Responsible for updating the clabject props in the __ml_props__ attribute of a clabject
    """

    def __setitem__(self, key, value):
        if not isinstance(value, BaseClabjectProp):
            raise TypeError("Managed Items must be instances of  " + BaseClabjectProp.__name__)

        if value.prop_name != key:
            raise ValueError(
                "The given key {k} does not correspond to the Clabject.prop_name {n}".format(k=key, n=value))

        super(ClabjectPropDict, self).__setitem__(key, value)

    def next_prop_dict(self):
        """
         Create a deep copy of the ClabjectPropDict of the current clabject.
         Chosen on copy rather than reference semantic to enable independent state evolution

        Returns:
            a fresh ClabjectPropDict copy
        """
        new_clabject_prop_dict = ClabjectPropDict()
        for prop_name, prop_value in self.items():
            prop_value_copy = deepcopy(prop_value) if prop_value is not None else None
            new_clabject_prop_dict[prop_name] = prop_value_copy
        return new_clabject_prop_dict

    def define_props(self, new_props: List[BaseClabjectProp]) -> None:
        """
        Define props on the current clabject

        Args:
            new_props: a list of new properties

        Returns:
            Nothing, manipulates the objects state, i.e. the current __ml_props__

        """
        existing_prop_set = set(self.keys())
        intersection_set = existing_prop_set.intersection(new_props)
        if len(intersection_set):
            raise PropsAlreadyDefinedException(already_defined_props=intersection_set)
        else:
            for prop in new_props:
                self[prop.prop_name] = prop
                if prop.prop_value is not None and prop.steps_to_instantiation == 0:
                    violated_constraints = self.check_violated_prop_constraints(prop_name=prop.prop_name,
                                                                                potential_value=prop.prop_value)
                    if violated_constraints:
                        raise ConstraintViolationException(violated_constraints=violated_constraints)

    def apply_instantiation_step(self, init_props: dict, speed_adjustments: dict):
        """

        Implements deep instantiation mechanism

        Args:
            init_props: the props to be instantiated at this instantiation - step given as prop: value pairs inside a dictionary
            speed_adjustments: prop_name : integer, see :py:meth:`.adjust_instantiation_speed`

        Returns:
            A ClabjectPropDict object with initialised props and decremented instantiation counters if no Exception is
            raised
        """

        # Prepare Instantiation
        next_prop_dict = self.next_prop_dict()
        if speed_adjustments:
            next_prop_dict.adjust_instantiation_speed(speed_adjustments=speed_adjustments)

        next_prop_dict.__decrement_step_from_counters()
        next_prop_dict.__decrement_step_to_counters()
        next_prop_dict.__activate_re_init()

        provided_props_set = set(init_props.keys())
        clabject_props_set = set(next_prop_dict.keys())
        provided_but_not_defined_set = provided_props_set.difference(clabject_props_set)  # case 1
        defined_but_not_provided_set = clabject_props_set.difference(provided_props_set)  # case 2
        intersection_set = clabject_props_set.intersection(provided_props_set)  # case 3
        all_violated_constraints = create_violated_constraint_dict()

        # Handle Case 1 - throw exception
        if len(provided_but_not_defined_set):
            raise UndefinedPropsException(undefined_props=[provided_but_not_defined_set])

        # Handle Case 2: Ensure that all props that are due to be initialised are provided
        for prop_name in defined_but_not_provided_set:
            if next_prop_dict[prop_name].steps_to_instantiation == 0 and next_prop_dict[prop_name].prop_value is None:
                if next_prop_dict[prop_name].default_value is not None:
                    violated_constraints = next_prop_dict.check_violated_prop_constraints(prop_name, next_prop_dict[
                        prop_name].default_value)
                    if not violated_constraints:
                        next_prop_dict[prop_name].prop_value = next_prop_dict[prop_name].default_value
                    else:
                        all_violated_constraints.add_violations(violated_constraints)
                else:
                    raise UninitialisedPropException(prop_name=prop_name)

        # Handle Case 3:
        # a.) prop.steps_to_instantiation == 0 and existing value => try overwriting existing prop
        # b.) prop.steps_to_instantiation = 0 and no value => instantiate
        # c.) prop.steps_to_instantiation > 0 instantiation Error

        for prop_name in intersection_set:
            no_of_steps = next_prop_dict[prop_name].steps_to_instantiation
            value = next_prop_dict[prop_name].prop_value
            if no_of_steps == 0 and value is not None:
                if next_prop_dict[prop_name].is_final:
                    raise ChangeFinalPropException(prop_name=prop_name)
                else:
                    potential_new_value = init_props[prop_name]
                    violated_constraints = next_prop_dict.check_violated_prop_constraints(prop_name=prop_name,
                                                                                          potential_value=potential_new_value)
                    if not violated_constraints:
                        next_prop_dict[prop_name].prop_value = potential_new_value
                    else:
                        all_violated_constraints.add_violations(violations=violated_constraints)

            elif no_of_steps == 0 and value is None:
                potential_new_value = init_props[prop_name]
                violated_constraints = next_prop_dict.check_violated_prop_constraints(prop_name=prop_name,
                                                                                      potential_value=potential_new_value)
                if not violated_constraints:
                    next_prop_dict[prop_name].prop_value = potential_new_value
                else:
                    all_violated_constraints.add_violations(violations=violated_constraints)

            else:

                raise UnduePropInstantiationException(prop_name=prop_name,
                                                      later_steps_number=self[prop_name].steps_to_instantiation - 1)

        if all_violated_constraints:
            raise ConstraintViolationException(violated_constraints=all_violated_constraints)

        return next_prop_dict

    def __activate_re_init(self):
        for prop in self.values():
            if prop.re_init_prop_constr:
                for constr in prop.constraints:
                    if constr.name in [constr.name for constr in prop.re_init_prop_constr.del_constr]:
                        prop.constraints.remove(constr)
                prop.constraints = prop.constraints + prop.re_init_prop_constr.add_constr
                prop.prop_value = None
                prop.re_init_prop_constr = None

    def __decrement_step_to_counters(self):
        for prop in self.values():
            if prop.steps_to_instantiation > 0:
                prop.steps_to_instantiation += -1

    def __decrement_step_from_counters(self):
        to_be_dropped = []
        for prop in self.values():
            if prop.steps_to_instantiation == 0:
                if prop.steps_from_instantiation == 0:
                    to_be_dropped.append(prop.prop_name)
                else:
                    prop.steps_from_instantiation += -1

        for drop_prop in to_be_dropped:
            self.pop(drop_prop)

    def check_prop_in_keys(self, prop_name: str) -> None:
        if prop_name not in self.keys():
            raise UndefinedPropsException(undefined_props=set([prop_name]))

    def adjust_instantiation_speed(self, speed_adjustments: Dict[str, int]):
        """
        Adjust the number of instantiation steps for a property to become instantiated from the perspective
        of the current clabject

        Args:
            speed_adjustments: dict with structure <prop_name:str> => <speed_adj: int>: if integer < 0 acceleration of prop instantiation,
                             if the acceleration leads to number_to_instantiation_steps < 1, the effect is that the prop
                             has to be instantiated with the next instantiation step,
                             if integer > 0 the instantiation of property deferred by this number of steps

        Returns:
            Updates the State of the ClabjectPropDict
        """
        for prop_name, speed_adjustment in speed_adjustments.items():
            self.check_prop_in_keys(prop_name)
            adjusted_step_to_number = self[prop_name].steps_to_instantiation + speed_adjustment
            self[prop_name].steps_to_instantiation = max(1, adjusted_step_to_number)

    def add_prop_constraint(self, prop_name: str, constraint: PropValueConstraint) -> None:
        """
        Add a PropValueConstraint for an existing property

        Args:
            prop_name: the name of the prop the constraint is imposed on
            constraint: a PropValueConstraint Object

        Returns: Nothing, updates the state of ClabjectPropDict
        """
        from multilevel_py.constraints import PropValueConstraint
        assert isinstance(constraint, PropValueConstraint)

        self.check_prop_in_keys(prop_name)
        self[prop_name].constraints.append(constraint)

    def check_violated_prop_constraints(self, prop_name: str = None, potential_value=None, init_only=True):
        """
        Check the constraints for a specific prop or for all props if no prop_name is provided

        Args:
            prop_name: The property to check
            potential_value: the provided value due to be instantiated, if not provided the current prop_value is checked
            init_only: Evaluate only the constraints that have eval_on_init flag set

        Returns:
            ConstrViolationDict

        """
        all_violated_constraints = create_violated_constraint_dict()
        props_to_check = []
        if prop_name is not None:
            self.check_prop_in_keys(prop_name)
            props_to_check.append(prop_name)
        else:
            props_to_check = self.keys()

        for prop_name in props_to_check:
            if potential_value is None:
                potential_value = self[prop_name].prop_value

            constraints = self[prop_name].constraints
            if init_only:
                constraints = [c for c in constraints if hasattr(c, "eval_on_init") and c.eval_on_init]

            for constraint in constraints:
                if not constraint(potential_value):
                    all_violated_constraints[prop_name].append(constraint)

            potential_value = None

        return all_violated_constraints


def bind(instance, func, as_name=None):
    """
    Bind a function to an object, i.e. make it a method of the object

    Args:
        instance: The object to which the function should be bound
        func: The function to be bound, should accept the instance as first argument, i.e. "self
        as_name: An optional new alias for the function

    Returns:
        the bound method object
    """
    if as_name is None:
        as_name = func.__name__
    bound_method = func.__get__(instance, instance.__class__)
    setattr(instance, as_name, bound_method)
    return bound_method


class MetaClabject(type):
    """
    The python metaclass that defines the behaviour of clabjects
    """

    def get_framework_attrs(cls):
        """
        Returns:
            all framework attributes of clabjects, that are not as domain related ClabjectProps managed by the internal ClabjectDict
        """
        return ["__ml_props__", "__domain_meta__", "__name__",
                "__slots__", "constraints", "re_init_prop_constr",
                "declared_instance_flag", "speed_adjustments", "viz_props_collapse"]

    def instance_of(cls):
        """
        Returns:
            The 'ontological' meta clabject of the current clabject. The term ontological should indicate that
            this relation is related to the respective target domain abstraction.
        """

        domain_meta = getattr(cls, "__domain_meta__")
        return domain_meta if domain_meta else cls.__metaclass__

    def __str__(cls):
        if cls.declared_instance_flag:
            return cls.__name__[0].lower() + cls.__name__[1:]
        return cls.__name__

    def viz_name_str(cls):
        # necessary to call str(cls) from jinja template
        return str(cls)

    def __hash__(cls):
        return super(MetaClabject, cls).__hash__()

    def __eq__(cls, other):
        # Assumption: Each Clabject has a unique name, need for refinement here in later dev stages
        if hasattr(cls, "__name__") and hasattr(other, "__name__"):
            return cls.__name__ == other.__name__
        else:
            return False

    def __getattr__(cls, item):
        # Avoid Recursion
        framework_props = cls.get_framework_attrs()
        if item not in framework_props:
            if item not in cls.__ml_props__:
                raise UndefinedPropsException(undefined_props=set([item]))
            else:
                return cls.__ml_props__[item].prop_value

    def __setattr__(cls, key, value):
        # Avoid Recursion
        all_violated_constraints = create_violated_constraint_dict()
        framework_props = cls.get_framework_attrs()
        if key in framework_props:
            super(MetaClabject, cls).__setattr__(key, value)

        # xxxbind_ as convention for bound methods (should bot be set to ml_props_dict)
        elif isinstance(key, str) and key.startswith("xxxbind_"):
            key = key.split("_", 1)[1]
            super(MetaClabject, cls).__setattr__(key, value)

        else:
            if key not in cls.__ml_props__:
                raise UndefinedPropsException(undefined_props=set([key]))
            else:
                step_to_inst = cls.__ml_props__[key].steps_to_instantiation
                if step_to_inst > 0:
                    raise UnduePropInstantiationException(prop_name=key, later_steps_number=step_to_inst)
                elif cls.__ml_props__[key].is_final:
                    raise ChangeFinalPropException(prop_name=key)
                else:
                    violated_constraints = cls.__ml_props__.check_violated_prop_constraints(prop_name=key,
                                                                                             potential_value=value)
                    if not violated_constraints:
                        cls.__ml_props__[key].prop_value = value
                    else:
                        all_violated_constraints.add_violations(violations=violated_constraints)
                        raise ConstraintViolationException(violated_constraints=all_violated_constraints)

    def __new__(cls, name, bases, attr_dict):
        for b in bases:
            # Disallow inheritance from Clabjects
            if isinstance(b, MetaClabject) and b != ClabjectParent:
                raise TypeError(
                    "Clabject {c} is not allowed as a BaseClass that can be inherited from.".format(c=b.__name__))
        print("Create new Class constructed by MetaClabject : " + name)
        attr_dict["instances"] = []
        return super(MetaClabject, cls).__new__(cls, name, bases, attr_dict)

    def _instantiate(cls, name=None, parents: list = None, init_props: dict = dict(),
                     declare_as_instance=False, speed_adjustment: dict = {}):

        new_bases = list(cls.__bases__)
        if parents:
            for c in parents:
                if c not in new_bases:
                    new_bases.append(c)
        attr_dict = cls.__dict__.copy()

        # Reset Framework props
        attr_dict["__domain_meta__"] = cls
        attr_dict["speed_adjustments"] = {}
        attr_dict["declared_instance_flag"] = declare_as_instance
        attr_dict["viz_props_collapse"] = False

        # Handle Next Props
        if cls.__name__ == 'Clabject':
            # Begin of instantiation hierarchy
            attr_dict["__ml_props__"] = ClabjectPropDict()
            next_meta_cls = MetaClabject
        else:
            assert hasattr(cls, "__ml_props__")

            attr_dict["__ml_props__"] = cls.__ml_props__.apply_instantiation_step(
                init_props=init_props, speed_adjustments=speed_adjustment)

        # next Clabject
        new_cls = MetaClabject(name, tuple(new_bases), attr_dict)

        # Bind Methods - use xxxbind_ convention to avoid that __setattr__ tries to write value in __ml_props__
        for prop_name, prop in attr_dict["__ml_props__"].items():
            if isinstance(prop, MethodProp) and prop.prop_value is not None:
                if prop_name in init_props:
                    setattr(prop.prop_value, "__impl_origin__", name)
                bind_key = ("_").join(["xxxbind", prop_name])
                bind(new_cls, prop.prop_value, bind_key)

        # Origin "Clabject" need not know about all of its usages
        if not cls.__name__ == "Clabject":
            cls.instances.append(new_cls)

        if len(speed_adjustment) > 0:
            update_dic = {name: speed_adjustment}
            cls.speed_adjustments.update(update_dic)
        return new_cls

    def __call__(cls, name=None, parents: list = [], init_props: dict = dict(),
                 speed_adjustments=dict(), declare_as_instance=False):
        """
        Call a clabject to trigger it's further instantiation

        Args:
            name: The name of the next clabject
            parents: a list of base classes from which the next clabject should inherit
            init_props: a dict of prop_name: prop_value pairs that should be initialised on the next clabject
            speed_adjustments: a dict of prop_name: int paris that accelerate/ slow down the instantiation speed, see
            also :py:meth:`ClabjectPropDict.adjust_instantiation_speed`
            declare_as_instance: Declare the next clabject as an instance which prevents further instantiation

        Returns: a new clabject instance of the current clabject

        """

        if cls.declared_instance_flag:
            raise ClabjectDeclaredAsInstanceException(obj=cls)

        return cls._instantiate(name=name,
                                parents=parents,
                                init_props=init_props,
                                speed_adjustment=speed_adjustments,
                                declare_as_instance=declare_as_instance)

    def define_props(cls, new_props=List[BaseClabjectProp]):
        """
        Delegates to :py:meth:`ClabjectPropDict.define_props`
        """
        assert hasattr(cls, "__ml_props__")
        for prop in new_props:
            if isinstance(prop, MethodProp) and prop.prop_value is not None:
                setattr(prop.prop_value, "__impl_origin__", cls.__name__)

        cls.__ml_props__.define_props(new_props=new_props)

    def add_prop_constraint(cls, constraint, prop_name: str = None) -> None:
        """
        Delegates to :py:meth:`ClabjectPropDict.add_prop_constraint`
        """
        cls.__ml_props__.add_prop_constraint(prop_name=prop_name, constraint=constraint)

    def check_prop_constraints(cls, prop_name: str = None, potential_value=None, init_only=False):
        """
        Delegates to :py:meth:`ClabjectPropDict.check_violated_prop_constraints`
        """
        return cls.__ml_props__.check_violated_prop_constraints(prop_name=prop_name,
                                                                potential_value=potential_value,
                                                                init_only=init_only)

    def adjust_instantiation_speed(cls, speed_adjustments: Dict[str, int]):
        """
        Delegates to :py:meth:`ClabjectPropDict.adjust_instantiation_speed`
        """
        assert hasattr(cls, "__ml_props__")
        cls.__ml_props__.adjust_instantiation_speed(speed_adjustments=speed_adjustments)

    def check_state_constraints(cls) -> dict:
        """
        Checks all 'active', i.e. instantiated ClabjectStateProps on the current clabject

        Returns:
            a dictionary with the structure <prop_name> => <violation_reason>
        """
        all_violated_constr = {}
        for prop_name, prop in cls.__ml_props__.items():
            if isinstance(prop, StateConstraintProp) and \
                    prop.steps_to_instantiation == 0 and \
                    not prop.prop_value(current_clabject=cls):
                all_violated_constr[prop_name] = prop.prop_value.violation_reason
        return all_violated_constr

    def require_re_init_on_next_step(cls, prop_name: str = None, re_init_prop_constr: ReInitPropConstr = None) -> None:
        """
        Require that a given property gets re-reinitialised on the next instantiation step

        Args:
            prop_name: the prop name
            re_init_prop_constr: an instance of ReInitPropConstr

        Returns:
            Nothing, updates the state of the internal __ml_props__ and thus changes the semantics of
            the next instantiation
        """
        assert hasattr(cls, "__ml_props__")
        if cls.__ml_props__[prop_name].is_final:
            raise ReInitFinalPropException(prop_name=prop_name)
        if cls.__ml_props__[prop_name].steps_from_instantiation < 1:
            raise ReInitVanishingPropException(prop_name=prop_name)

        cls.__ml_props__[prop_name].re_init_prop_constr = re_init_prop_constr


class ClabjectParent(metaclass=MetaClabject):
    """
    Implementation Detail to set, use :py:class:Clabject``instead to start instantiation chains
    """
    __domain_meta__ = None
    __ml_props__ = {}
    speed_adjustments = {}


class Clabject(ClabjectParent):
    """
    The origin clabject, i.e. a class that holds state and has the ability to create further clabjects on instantiation.
    Call this clabject to begin a new instantiation chain.
    """
    pass


def is_clabject(obj: Any) -> bool:
    """
    Determine whether a given object is a clabject

    Args:
        obj: the object to check

    Returns:
        a boolean value that indicates whether the predicate is fulfilled for the given obj
    """
    return type(obj) == MetaClabject


def _built_is_clabject_or_empty_constraint(eval_on_init=True):
    """
    Built a prop value constraint that checks whether the given value is a multilevel clabject - to avoid a cyclic
    dependency between core and constraint modules

    Args:
        eval_on_init: value indicating whether the constr should be evaluated on (re) init
    Returns:
        a parameterised, callable PropValueConstraint object
    """
    from multilevel_py.constraints import prop_constraint_optional_value_functional as optional

    def eval_value_func(value: Any):
        if not is_clabject(value):
            return "The given value is not a clabject"
        else:
            return ""

    return optional(PropValueConstraint(name="is_a_clabject", eval_value_func=eval_value_func, eval_on_init=eval_on_init))


is_clabect_or_empty_constr = _built_is_clabject_or_empty_constraint(True)