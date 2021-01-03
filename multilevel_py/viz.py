from pathlib import Path
from math import floor

from graphviz import Digraph
from multilevel_py.core import is_clabject
from multilevel_py.exceptions import NotAClabjectException


def _get_template_dir_path():
    return Path(__file__).parent.joinpath("viz_templates")


def _check_clabject(clabject):
    if not is_clabject(clabject):
        raise NotAClabjectException(obj=clabject)


def determine_level_recursive(clabject) -> int:
    """
    Args:
        clabject: a clabject obj., i.e. a class of the :class:`core.MetaClabject` python metaclass

    Returns:
        The level of the clabject, i.e. the maximum number of instantiation steps of al instantiation chains
        that originate from the given clabject
    """
    max = 0
    if clabject.instances is None or len(clabject.instances) == 0:
        return max
    else:
        for instance in clabject.instances:
            inst_level = determine_level_recursive(instance) + 1
            if inst_level > max:
                max = inst_level
        return max


def _create_node(dot: Digraph, clabject, font, fontsize):
    from jinja2 import Template
    template_dir_path = _get_template_dir_path()
    with template_dir_path.joinpath("clabject.jinja2.html").open() as file_:
        template = Template(file_.read())
    nodelabel = "<" + template.render(clabject=clabject) + ">"
    dot.node(clabject.__name__, label=nodelabel, font=font, fontsize=fontsize)


def _create_instantiate_relation(dot: Digraph, parent_clabject, instance_clabject, fontsize):
    inst_name = instance_clabject.__name__
    label = ""

    if inst_name in parent_clabject.speed_adjustments:
        res = {}
        for speed_adj_key, speed_adj_value in parent_clabject.speed_adjustments[inst_name].items():
            if speed_adj_value > 0:
                res[speed_adj_key] = "+" + str(speed_adj_value)
            else:
                res[speed_adj_key] = str(speed_adj_value)
        # parent_clabject.speed_adjustments[inst_name] = res
        label = str(res)
        # print("The inst. lable font size is " + str(floor(int(fontsize) * 1.3)))
    dot.edge(parent_clabject.__name__, inst_name, 
        label=label, style="dashed", fontsize=str(floor(int(fontsize) * 1.2)))


def _create_node_recursive(dot: Digraph, clabject, font, fontsize, hidden_root=False):
    """
    Depth First Recursion along the instantiation into relations
    """
    if not hidden_root:
        _create_node(dot, clabject, font, fontsize)

    if clabject.instances is not None:
        for instance in clabject.instances:
            if not hidden_root:
                _create_instantiate_relation(dot, clabject, instance, fontsize)
            _create_node_recursive(dot, instance, font, fontsize)


def _create_level_recursive(dot: Digraph,
                            prev_queue: list, current_queue: list, hierarchy_name: str, current_level: int,
                            font:str, fontsize: str):
    """
    Breath First Recursion, level by level
    """
    next_queue = []
    next_level = current_level - 1
    level_label = hierarchy_name + "_" + str(current_level)
    level_name = "cluster_" + level_label
    with dot.subgraph(name=level_name, graph_attr={'label': level_label}) as lev:
        for clabject in current_queue:
            _create_node(lev, clabject, font, fontsize)
            if clabject.instances is not None and len(clabject.instances) > 0:
                next_queue = next_queue + clabject.instances

    for clabject in prev_queue:
        if clabject.instances is not None:
            for instance in clabject.instances:
                _create_instantiate_relation(dot, clabject, instance, fontsize)

    if len(next_queue) > 0 and next_level >= 0:
        _create_level_recursive(dot, prev_queue=current_queue, current_queue=next_queue,
                                hierarchy_name=hierarchy_name, current_level=next_level,
                                font=font, fontsize=fontsize)


def viz_classification_hierarchy(start_clabject,
                                 output_dir: Path = None,
                                 output_name: str = None,
                                 render=True,
                                 by_level=False,
                                 hidden_root=False,
                                 show_hierarchy_name=False,
                                 format="png",
                                 font="arial",
                                 fontsize="12",
                                 ):
    """

    Args:
        start_clabject: a clabject obj., i.e. a class of the :class:`core.MetaClabject` python metaclass
        output_dir: a Path obj. that represents the desired output viz directory
        output_name: the name of the generated plot
        render: boolean value indicating whether the final dot object should be rendered into output dir
        by_level: use an breadth-first recursion, i.e. level by level through the given classification hierarchy
        hidden_root: boolean value indicating whether the start_clabject should be rendered
        show_hierarchy_name: boolean value indicating whether the plot should include the hierarchy name (name of start_clabject)
        format: a str specifying the given desired output format ("pdf", "png", "svg", "jpg")
        font: a str specifying the desired font-family
        fontsize: a str specifying the desired font-size (as integer value)

    Returns:
        a dot object constructed by traversing the classification hierarchy

    """

    _check_clabject(start_clabject)

    digraph_name = "cluster_" + start_clabject.__name__

    hierarchy_name = str(start_clabject.__name__) + "_Hierarchy"
    label_name = hierarchy_name if show_hierarchy_name else ""

    dot = Digraph(name=digraph_name, comment="Visualization of Instantiation Hierarchy",
                  graph_attr={'splines': 'polyline',
                              'rankdir': 'LR',
                              'labelloc': 't',
                              'fontname': 'arial',
                              'label': label_name,
                              'fontsize': '10'},
                  node_attr={'shape': 'plaintext'}, engine="dot")
    if by_level:
        start_level = determine_level_recursive(start_clabject)
        _create_level_recursive(dot, prev_queue=[], current_queue=[start_clabject], hierarchy_name=hierarchy_name,
                                current_level=start_level, font=font, fontsize=fontsize)
    else:
        _create_node_recursive(dot, start_clabject, font, fontsize, hidden_root=hidden_root)

    if render:
        assert output_dir is not None
        assert output_name is not None
        output_file = output_dir.joinpath(output_name)
        dot.render(output_file, format=format, view=True, cleanup=True)
    return dot