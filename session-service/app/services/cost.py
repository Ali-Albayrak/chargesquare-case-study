from decimal import ROUND_HALF_UP, Decimal


def calculate_cost(
    energy_kwh: Decimal,
    price_per_kwh: Decimal,
    start_fee: Decimal | None,
) -> Decimal:
    fee = Decimal("0") if start_fee is None else start_fee
    raw = energy_kwh * price_per_kwh + fee
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
