def model_snippet():
    from multilevel_py.constraints import is_str_constraint
    from multilevel_py.core import create_clabject_prop, Clabject
    from pathlib import Path

    Exercise = Clabject(name="Exercise")
    prop_exercise_name = create_clabject_prop(n="exercise_name", t=1, f='*', i_f=True, c=[is_str_constraint])
    Exercise.define_props([prop_exercise_name])

    StrengthExercise = Exercise(name="StrengthExercise", speed_adjustments={"exercise_name": 1})
    prop_motor_kind = create_clabject_prop(n="motor_kind", t=0, f='*', i_f=True, c=[], v="strength")
    StrengthExercise.define_props([prop_motor_kind])

    def define_contraction_form(clabject, prop_value):
        prop_contraction_form = create_clabject_prop(n="contraction_form", t=0, f='*', i_f=True, c=[], v=prop_value)
        clabject.define_props([prop_contraction_form])

    StaticStrengthExercise = StrengthExercise(name="StaticStrengthExercise", speed_adjustments={"exercise_name": 1})
    define_contraction_form(StaticStrengthExercise, "static")

    DynamicStrengthExercise = StrengthExercise(name="DynamicStrengthExercise", speed_adjustments={"exercise_name": 1})
    define_contraction_form(StaticStrengthExercise, "dynamic")

    def define_contraction_phase(clabject, prop_value):
        prop_contraction_phase = create_clabject_prop(n="contraction_phase", t=0, f='*', i_f=True, c=[], v=prop_value)
        clabject.define_props([prop_contraction_phase])

    ConcentricStrengthExercise = DynamicStrengthExercise(name="ConcentricStrengthExercise", speed_adjustments={"exercise_name": 1})

    define_contraction_phase(ConcentricStrengthExercise, "concentric")

    ExcentricStrengthExercise = DynamicStrengthExercise(name="ExcentricStrengthExercise", speed_adjustments={"exercise_name": 1})

    define_contraction_phase(ExcentricStrengthExercise, "excentric")

    Benchpress = DynamicStrengthExercise(name="Benchpress", init_props={"exercise_name": "Benchpress"})

    ExcentricBenchpress = ExcentricStrengthExercise(name="ExcentricBenchpress",
                                                    init_props={"exercise_name": "ExcentricBenchpress"})

    ConcentricDeadlift = ConcentricStrengthExercise(name="ConcentricDeadlift", init_props={
        "exercise_name": "ConcentricDeadlift"})

    viz_name = str(Path(__file__).stem)
    return Exercise, viz_name
