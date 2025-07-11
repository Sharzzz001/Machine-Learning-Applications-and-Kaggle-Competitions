# === TRAVEL SPENDING TRACKER ===

TOTAL_DAYS = 22
PER_DIEM_TOTAL = 2112
DAILY_LIMIT = 96
DECLARABLE_RATIO = 0.66

spending_log = []

def add_day_spending(day, legit, entertainment):
    if legit + entertainment > DAILY_LIMIT:
        print(f"⚠️ Day {day}: Total spend {legit + entertainment} exceeds daily cap of {DAILY_LIMIT}. Adjust needed.")
    spending_log.append({"Day": day, "Legit": legit, "Entertainment": entertainment})

def summarize_spending():
    total_legit = sum(d["Legit"] for d in spending_log)
    total_entertainment = sum(d["Entertainment"] for d in spending_log)
    total_spent = total_legit + total_entertainment

    remaining_budget = PER_DIEM_TOTAL - total_spent
    billable_ratio = total_legit / total_spent if total_spent > 0 else 0
    non_billable_ratio = total_entertainment / total_spent if total_spent > 0 else 0

    print("\n=== SUMMARY ===")
    print(f"✅ Days logged: {len(spending_log)} / {TOTAL_DAYS}")
    print(f"💰 Total legit (billable): SGD {total_legit:.2f}")
    print(f"🎉 Total entertainment: SGD {total_entertainment:.2f}")
    print(f"📊 Total spent: SGD {total_spent:.2f}")
    print(f"🧾 Billable %: {billable_ratio*100:.2f}% (Min required: 66%)")
    print(f"🛍️ Non-billable %: {non_billable_ratio*100:.2f}% (Max allowed: 33%)")
    print(f"💼 Remaining budget: SGD {remaining_budget:.2f}")

    if total_spent > PER_DIEM_TOTAL:
        print("❌ You have exceeded the total per diem allowance!")
    elif billable_ratio < DECLARABLE_RATIO:
        print("⚠️ You need to increase legit expenses to meet 66% requirement.")

# ==== EXAMPLE USAGE ====

# Example: first 6 days already spent
add_day_spending(1, 45, 10)
add_day_spending(2, 50, 8)
add_day_spending(3, 46, 12)
add_day_spending(4, 40, 15)
add_day_spending(5, 43, 7)
add_day_spending(6, 43.61, 8)

# Then you can keep adding new days like:
# add_day_spending(7, 50, 40)

summarize_spending()