from decimal import Decimal

from app.services.cost import calculate_cost


def test_calculate_cost():
    assert calculate_cost(Decimal("12.5"), Decimal("8.50"), Decimal("2.00")) == Decimal("108.25")
    assert calculate_cost(Decimal("0"), Decimal("8.50"), Decimal("2.00")) == Decimal("2.00")
    assert calculate_cost(Decimal("10"), Decimal("8.50"), None) == Decimal("85.00")
