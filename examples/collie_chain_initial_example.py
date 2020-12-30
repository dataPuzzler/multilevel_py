def model_snippet():
    from pathlib import Path
    from multilevel_py.constraints import is_int_constraint, is_str_constraint
    from multilevel_py.core import create_clabject_prop, Clabject

    Breed = Clabject(name="Breed")
    yearReg = create_clabject_prop(n="yearReg", t=1, f=0, i_f=True, c=[is_int_constraint])
    age = create_clabject_prop(n="age", t=2, f=0, i_f=True, c=[is_int_constraint])
    Breed.define_props([yearReg, age])

    Collie = Breed(name="Collie", init_props={"yearReg": 1888})

    lassie = Collie(name="Lassie", init_props={"age": 7}, declare_as_instance=True)

    viz_name = str(Path(__file__).stem)
    return Breed, viz_name
