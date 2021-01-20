from typing import Set


class InconsistentCreateClabjectPropArgsException(Exception):
    def __init__(self, ex_msg):
        self.ex_msg = ex_msg

    def __str__(self):
        return self.ex_msg


class TypeSpecificConstraintRemovalException(Exception):
    def __init__(self, constr):
        self.ex_msg = "The constr {Constr} is type specific and thus can not be removed"

    def __str__(self):
        return self.ex_msg


class InvalidPropValueConstraintException(Exception):
    def __init__(self, constr):
        self.ex_msg = "The provided constr {CONSTR} not a PropValueConstraint object"

    def __str__(self):
        return self.ex_msg


class NotAClabjectException(Exception):
    def __init__(self, obj):
        self.ex_msg = "The provided obj {OBJ} not a clabject of the multilevel_py framework". \
            format(OBJ=obj)

    def __str__(self):
        return self.ex_msg


class ClabjectDeclaredAsInstanceException(Exception):
    def __init__(self, obj):
        self.ex_msg = "The provided clabject {CLAB} is declared " \
                      "as an instance and thus can't be instantiated further". \
            format(CLAB=obj.__name__
                   )

    def __str__(self):
        return self.ex_msg


class InvalidMultiplicityTupleException(Exception):
    def __init__(self, provided_tuple):
        self.ex_msg = "The provided multiplicity {MULT} is invalid." \
                      "It has to be a (min,max) tuple with 0 <= min <= max".format(MULT=provided_tuple)

    def __str__(self):
        return self.ex_msg


class InvalidInstantiationOrderException(Exception):
    def __init__(self, provided_instantiation_order):
        self.ex_msg = \
            "The provided instantiation Order {ORDER} is invalid. " \
            "It has to be either a single integer value > 0 or" \
            "a (min,max) tuple with 0 < min < max". \
                format(ORDER=str(provided_instantiation_order))

    def __str__(self):
        return self.ex_msg


class UndefinedPropsException(Exception):
    def __init__(self, undefined_props: Set[str]):
        ex_msg = "The following properties are not defined for the clabject: '{PROPS}'".format(
            PROPS=str(undefined_props)
        )
        super(UndefinedPropsException, self).__init__(self, ex_msg)


class PropsAlreadyDefinedException(Exception):
    def __init__(self, already_defined_props: Set[str]):
        ex_msg = "The following properties are already defined for the clabject: '{PROPS}'.".format(
            PROPS=str(already_defined_props)
        )
        super(PropsAlreadyDefinedException, self).__init__(self, ex_msg)


class ChangeFinalPropException(Exception):
    def __init__(self, prop_name: str):
        ex_mgs = "The Property '{PROP} is declared final and thus cannot be changed".format(
            PROP=prop_name
        )


class ReInitFinalPropException(Exception):
    def __init__(self, prop_name: str):
        ex_mgs = "The Property '{PROP} is declared final and thus cannot be re-initialised".format(
            PROP=prop_name
        )


class ReInitVanishingPropException(Exception):
    def __init__(self, prop_name: str):
        ex_mgs = "The Property '{PROP} will vanish with the next instantiation step and thus cannot be re-initialised".format(
            PROP=prop_name
        )


class UnduePropInstantiationException(Exception):
    def __init__(self, prop_name: str, later_steps_number: int):
        ex_msg = "Propery {PROP} is not due to be instantiated. It's has to be instantiated at {STEPS}.".format(
            PROP=prop_name,
            STEPS=str(later_steps_number)
        )
        super(UnduePropInstantiationException, self).__init__(self, ex_msg)


class UninitialisedPropException(Exception):
    def __init__(self, prop_name: str):
        ex_msg = "Property '{PROP}' has to be instantiated at this level.".format(PROP=prop_name)
        super(UninitialisedPropException, self).__init__(self, ex_msg)


class ConstraintViolationException(Exception):
    def __init__(self, violated_constraints: dict):
        """
        Args:
            violated_constraints: a nested dict of the following structure <constr_holder_name:str> => <violated_constraints: dict>
        """
        self.violated_constraints = violated_constraints

    def __str__(self):
        res_str = "\n"
        for constr_holder, violated_constraints in self.violated_constraints.items():
            for constraint in violated_constraints:
                res_str += "'{HOLDER}' violated '{CONSTR}' for reason '{REASON}'".format(HOLDER=constr_holder, CONSTR=constraint.name, REASON=constraint.violation_reason)
                res_str += "\n"
        return res_str
