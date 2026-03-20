"""摄取/解析路径上的显式异常类型。"""


class HtmlParseError(Exception):
    """HTML 无法解析为职位快照（输入非法或缺少关键节点）。"""
