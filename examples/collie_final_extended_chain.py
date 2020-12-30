from pathlib import Path


def model_snippet():
    from multilevel_py.constraints import prop_constraint_ml_instance_of_th_order_functional, \
        prop_constraint_optional_value_functional as optional
    from multilevel_py.constraints import is_str_constraint, is_date_constraint
    from multilevel_py.core import create_clabject_prop, Clabject
    from datetime import date

    Breed = Clabject(name="Breed")

    coat_colour = create_clabject_prop(n="coat_colour", t=2, f=1, i_f=True, c=[is_str_constraint])
    year_of_birth = create_clabject_prop(n="year_of_birth", t=3, f='*', i_f=True, c=[is_date_constraint])
    father = create_clabject_prop(n="father", t=3, f='*', i_f=True, c=[])
    make_noise = create_clabject_prop(n="make_noise", t=1, f='*', i_f=False, i_m=True, c=[])

    Breed.define_props([make_noise, coat_colour, father, year_of_birth])

    def make_noise(obj) -> str:
        return "Wuff - I'm a Collie"

    Collie = Breed(name="Collie", init_props={"make_noise": make_noise})

    def make_noise(obj) -> str:
        return "Wuff I'm a Golden Retriever"

    GoldenRetriever = Breed(name="GoldenRetriever", speed_adjustments={"coat_colour": -1},
                            init_props={
                                "make_noise": make_noise,
                                "coat_colour": 'light golden to dark golden'
                            })

    # inspired by https://en.wikipedia.org/wiki/Rough_Collie
    SableRoughCollie = Collie(name="SableRoughCollie", init_props={"coat_colour": "sable-white"})

    father_constraint = prop_constraint_ml_instance_of_th_order_functional(SableRoughCollie, 1)
    SableRoughCollie.add_prop_constraint(constraint=optional(father_constraint), prop_name="father")

    def make_noise(obj) -> str:
        return "Wuff I'm called " + str(obj.__name__)

    sam = SableRoughCollie(name="Sam", declare_as_instance=True, init_props={
        "year_of_birth": date(year=1996, month=3, day=2),
        "father": None,
        "make_noise": make_noise})
    print(str(sam))
    lassie = SableRoughCollie(name="Lassie",
                              init_props={"year_of_birth": date(year=2002, month=2, day=20), "father": sam})

    print(str(lassie))
    derek = GoldenRetriever(name="Derek", speed_adjustments={"year_of_birth": -1, "father": -1},
                            init_props={"year_of_birth": date(year=2016, month=9, day=15),
                                        "father": None})
    print(Collie.make_noise())
    print(GoldenRetriever.make_noise())
    print(sam.make_noise())
    print(lassie.make_noise())
    print(derek.make_noise())

    viz_name = str(Path(__file__).stem)
    return Breed, viz_name
