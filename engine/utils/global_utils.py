import re
from typing import Any, Dict

from engine.utils.ini_parser import ParamUtils


def read_xml_args(line: str) -> Dict[str, Any]:
    """
    read a line formatted as `a = "value a" b='value b'` etc. and returns a :obj:`dictionary` with
    `{'a': value a, 'b': value b}`

    Args:
        line (str): the line to parse

    Returns:
        a :obj:`dict`
    """
    return {k[0].strip(): ParamUtils.smart_cast(k[1].strip()) for k in
            re.findall(r"(\w*\s*)=\s*['\"]([^'\"]*)['\"]", line)}
