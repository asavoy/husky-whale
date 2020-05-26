from typing import Union

from husky_whale import ast


def node_to_tree(n: ast.Node, _key="", _depth=0, _last=True, _base_prefix="") -> str:
    children = n.child_nodes()
    value_attrs = [
        f"{key}={repr(value)}"
        for key, value in n.as_dict().items()
        if key not in children.keys()
        and key not in ("preceding", "trailing")
        and value is not None
    ]
    value = f"{n.__class__.__name__}({', '.join(value_attrs)})"

    if _depth == 0:
        prefix = ""
    else:
        prefix = "└── " if _last else "├── "

    output = f"{_base_prefix}{prefix}{_key}{value}\n"

    for index, (child_key, child_node) in enumerate(children.items()):
        is_last_child = index == (len(children) - 1)
        if _depth == 0:
            parent_prefix = ""
        else:
            parent_prefix = "    " if _last else "│   "
        output += node_to_tree(
            child_node,
            _key=child_key + " = ",
            _depth=_depth + 1,
            _last=is_last_child,
            _base_prefix=_base_prefix + parent_prefix,
        )
    return output


def node_to_dict(n: ast.Node) -> Union[dict, str]:
    result = {}

    if hasattr(n, "literal"):
        return n.literal
    elif hasattr(n, "keyword"):
        return n.keyword
    elif hasattr(n, "column"):
        result["column"] = n.column
        if hasattr(n, "table") and getattr(n, "table", None):
            result["table"] = n.table
    elif hasattr(n, "table"):
        result["table"] = n.table
    elif hasattr(n, "function"):
        result["function"] = n.function.column
    elif hasattr(n, "alias"):
        result["alias"] = n.alias

    children = n.child_nodes()
    for child_key, child_node in children.items():
        result[child_key] = node_to_dict(child_node)
    return result
