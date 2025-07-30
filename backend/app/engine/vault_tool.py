from pathlib import Path
import os
from llama_index.core.tools import FunctionTool

def print_tree(p: Path, last=True, header='', exclude=['.git', '.DS_Store']):
    elbow = "└──"
    pipe = "│  "
    tee = "├──"
    blank = "   "
    result = [header + (elbow if last else tee) + p.name]
    if p.is_dir():
        children = list(p.iterdir())
        children = [c for c in children if c.name not in exclude]
        for i, c in enumerate(children):
            result.extend(print_tree(c, header=header + (blank if last else pipe), last=i == len(children) - 1, exclude=exclude))
    return result

def get_vault_tree() -> str:
    return "\n".join(print_tree(Path(os.environ["INPUT_FILES"])))

get_vault_tree_tool = FunctionTool.from_defaults(get_vault_tree)

if __name__ == "__main__":
    print(get_vault_tree())