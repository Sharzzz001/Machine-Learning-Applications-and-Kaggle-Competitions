def calculate_split(existing_inr, additional_inr, entry_price_usd, leverage, inr_usdt_rate):
    # Convert INR to USDT
    existing_margin_usdt = existing_inr / inr_usdt_rate
    additional_usdt = additional_inr / inr_usdt_rate

    # Current position size (ETH)
    existing_eth = (existing_margin_usdt * leverage) / entry_price_usd

    # Keep liquidation same: maintain margin-to-position ratio
    # Solve for split of additional_usdt between position and margin

    # Let x be USDT used for position, remaining goes to margin
    # Position size after: existing_eth + (x * leverage / entry)
    # Margin after: existing_margin + (additional_usdt - x)

    # Maintain ratio:
    # existing_margin / existing_eth = (existing_margin + (additional_usdt - x)) / (existing_eth + (x * leverage / entry_price_usd))

    from sympy import symbols, Eq, solve

    x = symbols('x')
    lhs = existing_margin_usdt / existing_eth
    rhs = (existing_margin_usdt + (additional_usdt - x)) / (existing_eth + (x * leverage / entry_price_usd))

    eq = Eq(lhs, rhs)
    sol = solve(eq, x)

    x_usdt_position = float(sol[0])
    x_usdt_margin = additional_usdt - x_usdt_position

    # Convert back to INR
    position_inr = x_usdt_position * inr_usdt_rate
    margin_inr = x_usdt_margin * inr_usdt_rate

    return round(position_inr, 2), round(margin_inr, 2)

# Example usage:
existing_inr = 5000
additional_inr = 10000
entry_price_usd = 2988.33
leverage = 8
inr_usdt_rate = 93

pos_inr, margin_inr = calculate_split(existing_inr, additional_inr, entry_price_usd, leverage, inr_usdt_rate)

print(f"Add to Position: ₹{pos_inr}")
print(f"Add to Margin: ₹{margin_inr}")