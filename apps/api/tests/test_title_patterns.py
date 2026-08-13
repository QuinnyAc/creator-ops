from app.services.title_patterns import classify_title_patterns


def test_question_and_number_title_patterns() -> None:
    patterns = classify_title_patterns("为什么知识博主应该关注 3 个收藏指标？")

    assert "question" in patterns
    assert "number" in patterns
    assert "list" in patterns


def test_tutorial_title_pattern() -> None:
    patterns = classify_title_patterns("FastAPI 入门教程：从 0 到第一个 API")

    assert "tutorial" in patterns
    assert "number" in patterns
    assert "result" in patterns


def test_other_title_pattern() -> None:
    assert classify_title_patterns("创作者运营随想") == ["other"]
