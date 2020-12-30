def model_snippet():
	from pathlib import Path
	from plan_chain_common import model_snippet
	top_clabject = model_snippet(sub_composite_hierarchy=False)
	viz_name = str(Path(__file__).stem)
	return top_clabject, viz_name
