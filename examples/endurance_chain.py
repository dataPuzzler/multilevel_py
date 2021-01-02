def model_snippet():
    from multilevel_py.constraints import is_str_constraint
    from multilevel_py.core import create_clabject_prop, Clabject
    from pathlib import Path

    Exercise = Clabject(name="Exercise")
    prop_exercise_name = create_clabject_prop(n="exercise_name", t=1, f='*', i_f=True, c=[is_str_constraint])
    Exercise.define_props([prop_exercise_name])

    EnduranceExercise = Exercise(name="EnduranceExercise", speed_adjustments={"exercise_name": 1})
    prop_motor_kind = create_clabject_prop(n="motor_kind", t=0, f='*', i_f=True, c=[is_str_constraint], v="endurance")
    EnduranceExercise.define_props([prop_motor_kind])

    def define_energy_supply(clabject, prop_value):
        prop_energy_supply = create_clabject_prop(n="endurance_scope", t=0, f='*', i_f=True, c=[is_str_constraint], v=prop_value)
        clabject.define_props([prop_energy_supply])

    AerobicEnduranceExercise = EnduranceExercise(name="AerobicEnduranceExercise", speed_adjustments={"exercise_name": 1})
    define_energy_supply(AerobicEnduranceExercise, "aerobic")

    AnaerobicEnduranceExercise = EnduranceExercise(name="AnaeronicEnduranceExercise", speed_adjustments={"exercise_name": 1})

    KiteSurfing = Exercise(name="KiteSurfing", init_props={"exercise_name": "KiteSurfing"})
    cycling = AerobicEnduranceExercise(name="Cycling", init_props={"exercise_name": "Cycling"})

    hidden_root = False
    viz_name = str(Path(__file__).stem)
    return Exercise, viz_name, hidden_root
