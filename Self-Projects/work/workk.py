from sympy import symbols, Eq, solve

def split_with_flexible_liquidation(existing_inr, additional_inr, entry_price_usd, leverage, inr_usdt_rate, max_liq_shift_pct=0.5):
    # Convert INR to USDT
    existing_margin_usdt = existing_inr / inr_usdt_rate
    additional_usdt = additional_inr / inr_usdt_rate

    # Current position size (ETH)
    existing_eth = (existing_margin_usdt * leverage) / entry_price_usd

    # Current notional size in USD
    position_usd = existing_eth * entry_price_usd

    # Maintenance margin rate assumed for liquidation
    mmr = 0.005

    # Current liquidation price
    maint_margin = position_usd * mmr
    initial_margin = existing_margin_usdt
    liq_price = entry_price_usd * (1 - ((initial_margin - maint_margin) / position_usd))

    # Allow liquidation to shift down slightly (max_liq_shift_pct%)
    target_liq_price = liq_price * (1 - max_liq_shift_pct / 100)

    # New funds split calculation
    x = symbols('x')  # Amount added to margin

    new_margin = existing_margin_usdt + x
    new_position_eth = existing_eth + ((additional_usdt - x) * leverage / entry_price_usd)
    new_position_usd = new_position_eth * entry_price_usd

    new_maint_margin = new_position_usd * mmr

    new_liq = entry_price_usd * (1 - ((new_margin - new_maint_margin) / new_position_usd))

    eq = Eq(new_liq, target_liq_price)
    sol = solve(eq, x)

    x_usdt_margin = float(sol[0])
    x_usdt_position = additional_usdt - x_usdt_margin

    # Convert back to INR
    margin_inr = x_usdt_margin * inr_usdt_rate
    position_inr = x_usdt_position * inr_usdt_rate

    return {
        'Add to Position (INR)': round(position_inr, 2),
        'Add to Margin (INR)': round(margin_inr, 2),
        'Old Liq Price': round(float(liq_price), 2),
        'Target Liq Price (0.5% shift)': round(float(target_liq_price), 2),
        'New Liq Check': round(float(new_liq.subs(x, sol[0])), 2)
    }

# Example Usage
result = split_with_flexible_liquidation(
    existing_inr=2000,
    additional_inr=10000,
    entry_price_usd=2988.33,
    leverage=8,
    inr_usdt_rate=93,
    max_liq_shift_pct=0.5  # Allow 0.5% lower liquidation price
)

print(result)