def model_snippet():
    from pathlib import Path
    from multilevel_py.constraints import is_int_constraint, is_str_constraint, is_date_constraint
    from multilevel_py.core import create_clabject_prop, Clabject
    from datetime import date

    Breed = Clabject(name="Breed")
    year_reg = create_clabject_prop(
        n="year_reg", t=1, f=1, i_f=False, c=[is_int_constraint])
    coat_colour = create_clabject_prop(
        n="coat_colour", t=2, f='*', i_f=True, c=[is_str_constraint])
    year_of_birth = create_clabject_prop(
        n="year_of_birth", t=3, f='*', i_f=True, c=[is_date_constraint])
    Breed.define_props([year_reg, coat_colour, year_of_birth])
    
    Collie = Breed(name="Collie", init_props={"year_reg": 1888})
    SableRoughCollie = Collie(name="SableRoughCollie", 
        init_props={"coat_colour": "sable-white"})
    SableRoughCollie.year_reg = 1902

    TriColourRoughCollie = Collie(name="TriColourRoughCollie", 
        init_props={"coat_colour": "black-edged-in-tan"})

    lassie = SableRoughCollie(name="Lassie",
        init_props={"year_of_birth": date(year=2002, month=2, day=20)},
        declare_as_instance=True)

    viz_name = str(Path(__file__).stem)
    return Breed, viz_name
