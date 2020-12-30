def model_snippet():
    from multilevel_py.constraints import is_str_constraint, is_float_constraint, \
        prop_constraint_ml_instance_of_th_order_functional
    from multilevel_py.core import create_clabject_prop, Clabject
    from multilevel_py.constraints import ReInitPropConstr
    from pathlib import Path

    # Simplified Root for illustration purposes
    DslRoot = Clabject(name="DSLRoot")

    # Mass Unit Hierarchy
    symbol_prop = create_clabject_prop(n='symbol', t=2, f='*', i_f=True, c=[is_str_constraint])
    MassUnit = DslRoot(name="MassUnit")
    MassUnit.define_props([symbol_prop])

    kilogram = MassUnit(name="Kilogram", speed_adjustments={'symbol': -1}, init_props={'symbol': 'kg'},
                        declare_as_instance=True)

    conversion_factor_prop = create_clabject_prop(n='conversion_factor', t=1, f='*', i_f=True, c=[is_float_constraint])
    is_mass_unit_constr = prop_constraint_ml_instance_of_th_order_functional(MassUnit, instantiation_order=1)
    base_unit_prop = create_clabject_prop(n='base_unit', t=0, f='*', v=kilogram, c=[is_mass_unit_constr])
    DerivedMassUnit = MassUnit(name="DerivedMassUnit")
    DerivedMassUnit.define_props([conversion_factor_prop, base_unit_prop])

    pound = DerivedMassUnit(name="Pound", init_props={"symbol": "lb", "conversion_factor": 0.45359},
                            declare_as_instance=True)

    # Weigh Load Hierarchy
    planned_value_prop = create_clabject_prop(n='planned_value', t=1, f='*', i_f=False, c=[is_float_constraint])
    actual_value_prop = create_clabject_prop(n='actual_value', t=2, f='*', i_f=True, c=[is_float_constraint])
    mass_unit_prop = create_clabject_prop(n='mass_unit', t=0, f='*', i_f=False, v=MassUnit)
    WeightLoad = DslRoot(name="WeightLoad")
    WeightLoad.define_props([planned_value_prop, actual_value_prop, mass_unit_prop])

    is_fst_or_snd_order_mass_unit_instance = prop_constraint_ml_instance_of_th_order_functional(MassUnit,
                                                                                                instantiation_order=(
                                                                                                    1, 2))
    re_init_constr = ReInitPropConstr(del_constr=[], add_constr=[is_fst_or_snd_order_mass_unit_instance])
    WeightLoad.require_re_init_on_next_step(prop_name="mass_unit", re_init_prop_constr=re_init_constr)

    ParameterisedWeightLoad = WeightLoad(name='ParameterisedWeightLoad',
                                         init_props={'planned_value': 180.0, 'mass_unit': pound})
    realisedWeightLoad = ParameterisedWeightLoad(name="RealisedWeightLoad", init_props={"actual_value": 182.5},
                                                 declare_as_instance=True)

    # Deadlift Hierarchy
    weight_load_prop = create_clabject_prop(n='weight_load', t=0, f='*', i_f=False, v=WeightLoad)
    Deadlift = DslRoot(name="Deadlift")
    Deadlift.define_props([weight_load_prop])

    is_weight_load_instance = prop_constraint_ml_instance_of_th_order_functional(WeightLoad, instantiation_order=1)
    re_init_constr = ReInitPropConstr(del_constr=[], add_constr=[is_weight_load_instance])
    Deadlift.require_re_init_on_next_step(prop_name="weight_load", re_init_prop_constr=re_init_constr)
    ParameterisedDeadlift = Deadlift(name="ParameterisedDeadlift", init_props={'weight_load': ParameterisedWeightLoad})

    is_param_weight_load_instance = prop_constraint_ml_instance_of_th_order_functional(ParameterisedWeightLoad,
                                                                                       instantiation_order=1)
    re_init_constr = ReInitPropConstr(del_constr=[is_weight_load_instance], add_constr=[is_param_weight_load_instance])
    ParameterisedDeadlift.require_re_init_on_next_step(prop_name="weight_load", re_init_prop_constr=re_init_constr)
    realisedDeadlift = ParameterisedDeadlift(name="RealisedDeadlift", init_props={"weight_load": realisedWeightLoad},
                                             declare_as_instance=True)

    viz_name = str(Path(__file__).stem)
    return DslRoot, viz_name
