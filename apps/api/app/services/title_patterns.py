import re

PATTERN_LABELS = {
    "question": "疑问型",
    "number": "数字型",
    "list": "清单型",
    "tutorial": "教程型",
    "result": "结果型",
    "other": "其他",
}

RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "question",
        re.compile(r"[?？]|(?:为什么|为何|怎么|如何)|\b(?:what|why|how)\b", re.IGNORECASE),
    ),
    (
        "number",
        re.compile(r"\d+|[一二三四五六七八九十百]+\s*(?:个|条|种|步|招|点)"),
    ),
    (
        "list",
        re.compile(
            r"清单|合集|盘点|大全|(?:\d+|[一二三四五六七八九十]+)\s*(?:个|条|种|步|招|点)|tips|ways|things|checklist",
            re.IGNORECASE,
        ),
    ),
    (
        "tutorial",
        re.compile(r"教程|指南|入门|攻略|手把手|how\s+to|guide|tutorial", re.IGNORECASE),
    ),
    (
        "result",
        re.compile(
            r"提升|增长|涨粉|提高|翻倍|\d+(?:\.\d+)?%|从.+到|increase|grow|growth|from.+to",
            re.IGNORECASE,
        ),
    ),
]


def classify_title_patterns(title: str) -> list[str]:
    normalized = title.strip()
    if not normalized:
        return ["other"]

    matched = [key for key, pattern in RULES if pattern.search(normalized)]
    return matched or ["other"]
