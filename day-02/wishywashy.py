"""WishyWashy - carpet-cleaning machine hire: payment processing and daily summary."""

import random


def generate_minutes():
    """Return a random number of minutes (30 to 180, inclusive) a machine was used."""
    return random.randint(30, 180)


def calc_amount(machine_type, minutes):
    """Return the amount before VAT: initial cost + (hourly rate x hours used)."""
    # (initial cost, additional cost per hour) for each machine type
    charges = {
        "A": (50.00, 30.00),
        "B": (62.50, 36.25),
        "C": (74.87, 40.50),
    }
    initial_cost, hourly_rate = charges[machine_type.strip().upper()]
    hours = minutes / 60  # fractional hours are charged proportionally
    return initial_cost + (hourly_rate * hours)


def calc_total_amount(amount):
    """Return the VAT amount (14%) and the total payable."""
    vat_rate = 0.14
    vat = amount * vat_rate
    total = amount + vat
    return vat, total


def display_summary(payments):
    """Display the daily summary for the list of total payments."""
    count = len(payments)
    total = sum(payments)
    average = total / count

    print("\n===== DAILY SUMMARY =====")
    print(f"Customers processed : {count}")
    print(f"Combined payable    : R{total:.2f}")
    print(f"Average payment     : R{average:.2f}")
    print(f"Highest payment     : R{max(payments):.2f}")
    print(f"Lowest payment      : R{min(payments):.2f}")


def process_payments():
    """Process each customer, display their invoice, then show the daily summary."""
    number_of_customers = int(input("Enter the number of customers to process: "))
    payments = []

    for _ in range(number_of_customers):
        print()
        name = input("Enter the customer's name: ")
        machine_type = input("Enter the machine type (A, B or C): ").strip().upper()

        minutes = generate_minutes()
        amount = calc_amount(machine_type, minutes)
        vat, total = calc_total_amount(amount)
        payments.append(total)

        print("\n----- INVOICE -----")
        print(f"Customer          : {name}")
        print(f"Machine type      : {machine_type}")
        print(f"Minutes used      : {minutes}")
        print(f"Amount before VAT : R{amount:.2f}")
        print(f"VAT (14%)         : R{vat:.2f}")
        print(f"Total payable     : R{total:.2f}")

    display_summary(payments)


process_payments()
