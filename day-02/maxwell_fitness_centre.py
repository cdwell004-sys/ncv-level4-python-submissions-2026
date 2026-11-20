"""Maxwell Fitness Centre - non-member facility payment calculator (PoE Activity 6)."""

# Hourly rates (Rand) for each facility code
RATES = {
    "squa": 13.00,  # Squash court
    "swim": 12.00,  # Swimming pool
    "gym": 11.00,   # Gymnasium
    "wei": 8.00,    # Weights
}

VAT_RATE = 0.14  # 14% VAT, as specified for this exercise


def amount_due(facility_code, hours):
    """Look up the hourly rate and return the amount due before VAT."""
    rate = RATES[facility_code.strip().lower()]
    return rate * hours


def final_amount_due(amount):
    """Add 14% VAT to the amount and return the final amount payable."""
    return amount * (1 + VAT_RATE)


def display(name, final_amount):
    """Display the customer's name and the amount payable (R, two decimals)."""
    print(f"Customer: {name}")
    print(f"Amount payable: R{final_amount:.2f}")


def process_payment():
    """Prompt for the details, then calculate and display the payment."""
    name = input("Enter the customer's name: ")
    facility_code = input("Enter the facility code (squa, swim, gym, wei): ")
    hours = float(input("Enter the number of hours (e.g. 1.5): "))

    amount = amount_due(facility_code, hours)
    final_amount = final_amount_due(amount)
    display(name, final_amount)


process_payment()
