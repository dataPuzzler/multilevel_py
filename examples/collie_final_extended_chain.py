from pathlib import Path


def model_snippet():
    from multilevel_py.constraints import prop_constraint_ml_instance_of_th_order_functional, \
        prop_constraint_optional_value_functional as optional
    from multilevel_py.constraints import is_str_constraint, is_date_constraint, \
         EmptyValue, ClabjectStateConstraint
    from multilevel_py.core import create_clabject_prop, Clabject
    from datetime import date

    Breed = Clabject(name="Breed")
    coat_colour = create_clabject_prop(
        n="coat_colour", t=2, f=1, i_f=True, c=[is_str_constraint])
    father = create_clabject_prop(
        n="father", t=3, f='*', i_f=True, i_assoc=True, c=[])
    make_noise = create_clabject_prop(
        n="make_noise", t=1, f='*', i_f=False, i_m=True, c=[])

    def eval_state(current_clab) -> str:
        res = ""
        if current_clab.father != EmptyValue and \
           current_clab.father.instance_of() != current_clab.instance_of():
            res = "If specified, father must be of the same breed as the current dog"
        return res

    clab_state_constr = ClabjectStateConstraint(
        name="FatherOfTheSameBreedType", eval_clabject_func=eval_state)
    father_sc = create_clabject_prop(
        n="father_sc", t=3, f='*', i_sc=True, c=[], d=clab_state_constr)

    Breed.define_props([make_noise, coat_colour, father, father_sc])

    def make_noise(obj) -> str:
        return "Wuff - I'm a Collie"

    Collie = Breed(name="Collie", init_props={"make_noise": make_noise})

    def make_noise(obj) -> str:
        return "Wuff I'm a Golden Retriever"


    GoldenRetriever = Breed(
        name="GoldenRetriever", 
        speed_adjustments={"coat_colour": -1},
        init_props={
        "make_noise": make_noise,
        "coat_colour": 'light to dark golden'})

    SableRoughCollie = Collie(
        name="SableRoughCollie", 
        init_props={"coat_colour": "sable-white"})

    def make_noise(obj) -> str:
        return "Wuff I'm called " + str(obj.__name__)

    sam = SableRoughCollie(name="Sam", init_props={
        "father": EmptyValue,
        "make_noise": make_noise}, 
        declare_as_instance=True)

    lassie = SableRoughCollie(
        name="Lassie",
        init_props={"father": sam},
        declare_as_instance=True)

    derek = GoldenRetriever(
        name="Derek", 
        speed_adjustments={"father": -1, "father_sc": -1},
        init_props={"father": sam},
        declare_as_instance=True)

    print(Collie.make_noise()) # > Wuff - I'm a Collie
    print(GoldenRetriever.make_noise()) # > Wuff I'm a Golden Retriever
    print(sam.make_noise()) # > Wuff I'm called Sam
    print(lassie.make_noise()) # > Wuff - I'm a Collie
    print(derek.make_noise()) # Wuff I'm a GoldenRetriever

    print(sam.check_state_constraints()) # > {}
    print(derek.check_state_constraints()) # > {'father_sc': 'If specified, father ...'}

    hidden_root = False
    viz_name = str(Path(__file__).stem)
    return Breed, viz_name, hidden_root
