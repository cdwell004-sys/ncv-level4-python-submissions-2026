# race_qualifiers.py

QUALIFY_LIMIT = 25 * 60  # 25:00 in seconds

total = 0
qualified = 0
best_time = -1          # -1 means no valid time yet
winner = ""

while True:
    name = input("Athlete name (x to end): ").strip()
    if name.lower() == "x":
        break

    time_text = input("Time (mm:ss): ").strip()
    parts = time_text.split(":")

    # Validation: must be mm:ss, digits only, seconds between 0 and 59
    if len(parts) != 2:
        print("Invalid time, athlete ignored.")
        continue
    if not parts[0].isdigit() or not parts[1].isdigit():
        print("Invalid time, athlete ignored.")
        continue

    minutes = int(parts[0])
    seconds = int(parts[1])
    if seconds >= 60:
        print("Invalid time, athlete ignored.")
        continue

    total_seconds = minutes * 60 + seconds
    total = total + 1

    # Count qualifiers (exactly 25:00 qualifies)
    if total_seconds <= QUALIFY_LIMIT:
        qualified = qualified + 1

    # Find the winner (strict < keeps the first athlete in a tie)
    if best_time == -1 or total_seconds < best_time:
        best_time = total_seconds
        winner = name

# Output
if total == 0:
    print("No valid entries.")
else:
    win_min = best_time // 60
    win_sec = best_time % 60
    print(f"Winner: {winner} ({win_min:02d}:{win_sec:02d})")
    print(f"Qualified: {qualified} of {total}")
