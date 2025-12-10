import csv
import random
import math
import uuid
import argparse
import os
from datetime import date, timedelta, datetime


def generate_csv(filename="sales_training_data.csv", days=365, start_date_str=None):
    print(f"Generating realistic California-style sales data for {days} days...")

    # Define Products
    products = [
        ("Coffee Beans", 15.00, 50),
        ("Milk", 3.00, 100),
        ("Croissant", 4.50, 80),
        ("Muffin", 3.50, 60),
        ("Sandwich", 8.00, 40),
        ("Juice", 5.00, 70),
        ("Tea", 4.00, 60),
        ("Cake", 6.00, 30),
        ("Salad", 9.00, 25),
        ("Wrap", 7.50, 35),
    ]

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

    current_date = start_date
    rows = []

    for i in range(days):
        # Time features
        day_of_year = current_date.timetuple().tm_yday
        weekday = current_date.weekday()  # 0=Mon, 6=Sun
        month = current_date.month

        # 1. Seasonality & Trend
        seasonality = math.sin((day_of_year - 180) * 2 * math.pi / 365)
        season_factor = 1.0 + (seasonality * 0.15)  # Milder seasonality in CA

        # 2. Weekly Pattern
        if weekday >= 5:
            week_factor = 1.4  # High weekend traffic
        elif weekday == 4:
            week_factor = 1.2  # Fri
        else:
            week_factor = 1.0

        # 3. Trend
        trend_factor = 1.0 + (0.2 * (i / days))

        # 4. California Weather Logic ☀️🌊
        # Mostly Dry/Sunny, mild winters, warm summers.
        # Rain mostly in Dec-Mar.

        rand_weather = random.random()
        base_temp = 20  # Average

        # Temp base on month
        if month in [6, 7, 8, 9]:
            base_temp = 25  # Summer
        elif month in [12, 1, 2]:
            base_temp = 14  # Winter
        else:
            base_temp = 19  # Spring/Fall

        # Weather Condition
        weather = "Sunny"
        temp_noise = random.uniform(-4, 4)

        if month in [12, 1, 2, 3]:  # Rainy season
            if rand_weather < 0.20:
                weather = "Rainy"
            elif rand_weather < 0.40:
                weather = "Cloudy"
            else:
                weather = "Sunny"
        elif month in [5, 6]:  # May Grey / June Gloom
            if rand_weather < 0.30:
                weather = "Cloudy"  # Foggy
            else:
                weather = "Sunny"
        else:  # Dry season
            if rand_weather < 0.05:
                weather = "Rainy"  # Rare
            elif rand_weather < 0.1:
                weather = "Cloudy"
            else:
                weather = "Sunny"

        temp = base_temp + temp_noise
        if weather == "Rainy":
            temp -= 3
        if weather == "Sunny" and month in [7, 8, 9]:
            temp += 5

        # 5. Random Closures
        if random.random() < 0.005:  # Rare closures
            current_date += timedelta(days=1)
            continue

        # Generate Sales
        for name, price, base_vol in products:
            noise = random.uniform(0.85, 1.15)

            # Weather Correlation
            w_effect = 1.0
            if weather == "Rainy":
                w_effect = 0.7  # CA people hate rain
            if weather == "Sunny" and temp > 28:
                if name in ["Juice", "Salad"]:
                    w_effect = 1.3
                if name in ["Coffee Beans", "Tea"]:
                    w_effect = 0.8
            if weather == "Cloudy" and name in ["Coffee Beans"]:
                w_effect = 1.1

            # Promo
            discount = 0
            if random.random() < 0.08:
                discount = int(random.choice([10, 15, 20, 25]))
                noise *= 1 + (discount * 0.02)

            qty = int(
                base_vol * season_factor * week_factor * trend_factor * w_effect * noise
            )
            qty = max(0, qty)

            if qty > 0:
                rows.append(
                    {
                        "product_id": name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "revenue": round(qty * price * (1 - discount / 100), 2),
                        "units_sold": qty,
                        "weather_condition": weather,
                        "weather_temp": round(temp, 1),
                        "customer_flow": int(qty * random.uniform(1.2, 1.8)),
                        "discount_percentage": discount,
                        "sales_uid": f"gen_{uuid.uuid4().hex[:10]}",
                    }
                )

        current_date += timedelta(days=1)

    # Output to File
    filepath = os.path.join(os.getcwd(), "datagen", filename)
    # Ensure dir exists if script run from root
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Success! Generated {len(rows)} rows.")
    print(f"File saved to: {filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate CA Sales Data")
    parser.add_argument(
        "--days", type=int, default=365, help="Number of days to generate"
    )
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument(
        "--out", type=str, default="sales_training_data.csv", help="Output filename"
    )

    args = parser.parse_args()
    generate_csv(args.out, args.days, args.start)
