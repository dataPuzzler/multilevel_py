def model_snippet(sub_composite_hierarchy=False):
    from datetime import timedelta
    from math import inf
    from multilevel_py.constraints import prop_constraint_py_isinstance_functional, \
        prop_constraint_ml_instance_of_th_order_functional, \
        prop_constraint_is_th_order_instance_of_clabject_set_functional
    from multilevel_py.constraints import prop_constraint_collection_member_functional as as_member_constr
    from multilevel_py.constraints import is_str_constraint, is_timedelta_constraint
    from multilevel_py.core import Clabject, create_clabject_prop
    from multilevel_py.exceptions import ConstraintViolationException

    # Traditional Class (to be refined in the later development steps)
    class Exercise:
        def __init__(self, name: str):
            self.name = name

    TrainingPlanElement = Clabject(name="TraingPlanElement", init_props={})
    prop_part_name = create_clabject_prop(n="part_name", t=3, f='*', c=[is_str_constraint])
    prop_calc_plan_duration = create_clabject_prop(n="calc_plan_duration", t=1, f='*', i_m=True)

    TrainingPlanElement.define_props([prop_part_name, prop_calc_plan_duration])

    def calc_plan_duration_recursive(obj) -> timedelta:
        planned_train_time = timedelta()  # 0
        for child_plan in obj.child_plans:
            planned_train_time += child_plan.calc_plan_duration()
        return planned_train_time

    CompositePlanElement = TrainingPlanElement(
        name="CompositePlanElement",
        init_props={"calc_plan_duration": calc_plan_duration_recursive})

    def append_childs(obj, childs):
        for child in childs:
            # [child] to check member constraints
            violations = obj.check_prop_constraints(prop_name="child_plans", potential_value=[child], init_only=True)
            if violations:
                raise ConstraintViolationException(violated_constraints=violations)
            else:
                obj.child_plans.append(child)

    prop_child_plans = create_clabject_prop(
        n="child_plans", t=2, f='*', c=[], coll_desc=(1, inf, None), d=[])
    prop_append_child = create_clabject_prop(
        n="append_childs", t=2, f='*', i_m=True, c=[], v=append_childs)

    CompositePlanElement.define_props([prop_child_plans, prop_append_child])

    SimplePlanElement = TrainingPlanElement(
        name="SimplePlanElement", 
        speed_adjustments={"calc_plan_duration": 1})

    is_exercise = prop_constraint_py_isinstance_functional(Exercise, eval_on_init=True)
    prop_exercise = create_clabject_prop(n="exercise", t=2, f='*', c=[is_exercise])
    prop_exercise_duration = create_clabject_prop(n="exercise_duration", t=2, f='*', c=[is_timedelta_constraint])
    SimplePlanElement.define_props([prop_exercise, prop_exercise_duration])

    # M1 Section
    def calc_train_duration(obj):
        train_duration = obj.exercise_duration + obj.rest_duration
        return train_duration

    ExerciseSetPlanElement = SimplePlanElement(
        name="ExerciseSetPlanElement",
        init_props={"calc_plan_duration": calc_train_duration})

    prop_rest_duration = create_clabject_prop(
        n="rest_duration", t=1, f='*', c=[is_timedelta_constraint])

    ExerciseSetPlanElement.define_props([prop_rest_duration])

    def calc_train_duration(obj):
        return obj.exercise_duration

    ExerciseIntervalPlanElement = SimplePlanElement(
        name="ExerciseIntervalPlanElement", 
        init_props={"calc_plan_duration": calc_train_duration})

    if sub_composite_hierarchy:
        StressRestPatternPlanElement = CompositePlanElement(
            name="StressRestPatternPlanElement", init_props={},
            speed_adjustments={'part_name': 1, 'child_plans': 1})

        stress_rest_child_constraint = prop_constraint_is_th_order_instance_of_clabject_set_functional(
            {SimplePlanElement}, order=2, eval_on_init=True)
        StressRestPatternPlanElement.add_prop_constraint(
            prop_name="child_plans", constraint=as_member_constr(stress_rest_child_constraint))

        IntervalTrainingPlanElement = StressRestPatternPlanElement(
            name="IntervalTrainingPlanElement", init_props={})
        interval_childs = prop_constraint_is_th_order_instance_of_clabject_set_functional(
            expected_values={ExerciseIntervalPlanElement}, order=1)
        IntervalTrainingPlanElement.add_prop_constraint(
            prop_name="child_plans",
            constraint=as_member_constr(interval_childs))

        StationTrainingPlanElement = StressRestPatternPlanElement(
            name="StationTrainingPlanElement", init_props={})
        station_childs = prop_constraint_is_th_order_instance_of_clabject_set_functional(
            expected_values={ExerciseSetPlanElement}, order=1)
        StationTrainingPlanElement.add_prop_constraint(prop_name="child_plans",
                                                       constraint=as_member_constr(station_childs))

        TrainingSectionPlanElement = CompositePlanElement(
            name="TrainingSectionPlanElement", init_props={})
        section_childs = prop_constraint_is_th_order_instance_of_clabject_set_functional(
            expected_values={StressRestPatternPlanElement}, order=2)
        TrainingSectionPlanElement.add_prop_constraint(prop_name="child_plans",
                                                       constraint=as_member_constr(section_childs))

        return CompositePlanElement

    else:
        return TrainingPlanElement
