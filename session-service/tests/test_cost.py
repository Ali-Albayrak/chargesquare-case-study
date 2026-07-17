from decimal import Decimal

from app.services.cost import calculate_cost


def test_worked_example_12_5_kwh():
    cost = calculate_cost(Decimal("12.5"), Decimal("8.50"), Decimal("2.00"))
    assert cost == Decimal("108.25")


def test_zero_energy_bills_start_fee_only():
    cost = calculate_cost(Decimal("0"), Decimal("8.50"), Decimal("2.00"))
    assert cost == Decimal("2.00")


def test_null_start_fee_treated_as_zero():
    cost = calculate_cost(Decimal("10"), Decimal("8.50"), None)
    assert cost == Decimal("85.00")
