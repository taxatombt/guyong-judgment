# -*- coding: utf-8 -*-
"""
test_adversarial.py
python test_adversarial.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adversarial import (
    generate_objections,
    validate_decision,
    format_adversarial_report,
    quick_validate,
)


def test_generate_objections_returns_list():
    obj = generate_objections("要不要辞职创�?)
    assert isinstance(obj, list)
    assert len(obj) >= 10, f"expected >=10 objections, got {len(obj)}"
    print("[PASS] generate_objections_returns_list")


def test_objection_has_required_fields():
    obj = generate_objections("要不要辞职创�?)
    for o in obj:
        assert hasattr(o, "dimension_id")
        assert hasattr(o, "objection_text")
        assert hasattr(o, "strength")
        assert o.strength in ("strong", "medium", "weak")
    print("[PASS] objection_has_required_fields")


def test_validate_decision():
    obj = generate_objections("要不要移�?)
    result = validate_decision("我要移民加拿�?, obj)
    assert hasattr(result, "verdict")
    assert result.verdict in ("ADOPT", "MODIFY", "REJECT")
    assert 0.0 <= result.overall_score <= 1.0
    print("[PASS] validate_decision")


def test_quick_validate():
    result = quick_validate("要不要辞职创�?)
    assert result.verdict in ("ADOPT", "MODIFY", "REJECT")
    assert result.overall_score >= 0.0
    print("[PASS] quick_validate")


def test_strong_objections_exist():
    obj = generate_objections("要不要投资数字货�?)
    strong = [o for o in obj if o.strength == "strong"]
    assert len(strong) >= 3, f"expected >=3 strong objections, got {len(strong)}"
    print("[PASS] strong_objections_exist")


def test_response_reduces_unaddressed():
    obj = generate_objections("要不要接受这份工�?)
    result_before = validate_decision("接受这份工作", obj)
    responses = {o.objection_text: "我考虑过了" for o in obj}
    result_after = validate_decision("接受这份工作", obj, responses)
    assert len(result_after.unaddressed) <= len(result_before.unaddressed)
    print("[PASS] response_reduces_unaddressed")


def test_format_report():
    obj = generate_objections("要不要分�?)
    result = validate_decision("分手", obj)
    report = format_adversarial_report(result)
    assert isinstance(report, str)
    assert len(report) > 30
    print("[PASS] format_report")


if __name__ == "__main__":
    test_generate_objections_returns_list()
    test_objection_has_required_fields()
    test_validate_decision()
    test_quick_validate()
    test_strong_objections_exist()
    test_response_reduces_unaddressed()
    test_format_report()
    print("\nAll tests passed!")
