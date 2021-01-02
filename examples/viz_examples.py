import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from configparser import ConfigParser
from collie_chain_initial_example import model_snippet as ms_1
from collie_extended_chain import model_snippet as ms_2
from collie_final_extended_chain import model_snippet as ms_3
from deadlift_chain import model_snippet as ms_4
from plan_chain_simple_element import model_snippet as ms_5
from plan_chain_composite_element import model_snippet as ms_6
from endurance_chain import model_snippet as ms_7
from strength_chain import model_snippet as ms_8

model_snippets = [ms_8]

from multilevel_py.viz import viz_classification_hierarchy


if __name__ == "__main__":
    config = ConfigParser()
    try:
        # custom output location via ini-file
        config.read(Path(__file__).parent.joinpath("viz_examples.ini"))

        font = config["Style"].get("font", fallback="arial")
        fontsize = config["Style"].get("fontsize", fallback="12")
        format = config["Format"].get("format", fallback="png")

        output_dir_str = config["Paths"].get("viz_output")
        output_dir = Path(output_dir_str)

    except Exception as e:
        print("Could not load a valid viz_examples.ini, use default values instead")
        # defaults
        output_dir = Path(__file__).parent.parent.joinpath("viz_output").resolve()
        font = "arial"
        fontsize = "12"
        format = "png"

    print("Start plotting into " + str(output_dir))
    for model_snippet in model_snippets:
        top_clabject, output_name, hidden_root = model_snippet()
        viz_classification_hierarchy(top_clabject,
                                     output_dir=output_dir, output_name=output_name, hidden_root=hidden_root,
                                     format=format, font=font, fontsize=fontsize, by_level=False)
