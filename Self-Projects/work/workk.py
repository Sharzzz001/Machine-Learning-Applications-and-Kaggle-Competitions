def calculate_split(existing_inr, additional_inr, entry_price_usd, leverage, inr_usdt_rate):
    # Convert INR to USDT
    existing_margin_usdt = existing_inr / inr_usdt_rate
    additional_usdt = additional_inr / inr_usdt_rate

    # Current position size (ETH)
    existing_eth = (existing_margin_usdt * leverage) / entry_price_usd

    # Total USDT after addition
    total_usdt = existing_margin_usdt + additional_usdt

    # Maintain same liquidation price:
    # New Margin / New Position Size = Old Margin / Old Position Size
    # Let new_eth = existing_eth + delta_eth
    # Let new_margin = existing_margin + margin_added
    # Then:
    # (existing_margin + margin_added) / (existing_eth + delta_eth) = existing_margin / existing_eth

    # Solve for delta_eth and margin_added

    # From new funds, x goes to margin, rest to position
    # Let x = amount in USDT added to margin
    # (existing_margin_usdt + x) / (existing_eth + ((additional_usdt - x) * leverage / entry_price_usd)) = existing_margin_usdt / existing_eth

    from sympy import symbols, Eq, solve

    x = symbols('x')
    lhs = (existing_margin_usdt + x) / (existing_eth + ((additional_usdt - x) * leverage / entry_price_usd))
    rhs = existing_margin_usdt / existing_eth

    eq = Eq(lhs, rhs)
    sol = solve(eq, x)

    x_usdt_margin = float(sol[0])
    x_usdt_position = additional_usdt - x_usdt_margin

    # Convert back to INR
    margin_inr = x_usdt_margin * inr_usdt_rate
    position_inr = x_usdt_position * inr_usdt_rate

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