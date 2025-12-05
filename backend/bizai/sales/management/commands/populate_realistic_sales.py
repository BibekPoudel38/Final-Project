import random
import math
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import InventorModel, SupplierModel
from merchant.models import BusinessProfileModel, AddressModel
from sales.models import SalesModel, SalesHolidayModel, TrainingMetrics


class Command(BaseCommand):
    help = "Populates the database with REALISTIC sales data (Sine wave + Trend) for better AI training"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email of the user to populate data for",
            default="admin@example.com",
        )
        parser.add_argument(
            "--days",
            type=int,
            help="Number of days to generate",
            default=365,
        )

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting REALISTIC data population...")

        # 1. Clear existing data
        self.stdout.write("Clearing old sales data...")
        SalesModel.objects.all().delete()
        TrainingMetrics.objects.all().delete()

        email = kwargs["email"]
        days_to_generate = kwargs["days"]

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email, defaults={"is_admin": False, "is_active": True}
        )
        if created:
            user.set_password("admin")
            user.save()

        # Ensure Address & Business
        address, _ = AddressModel.objects.get_or_create(
            street="123 Main St",
            city="Tech City",
            state="CA",
            zip_code="90210",
            country="USA",
        )
        business, _ = BusinessProfileModel.objects.get_or_create(
            business_name="BizAI Cafe",
            defaults={
                "address": address,
                "business_email": "contact@bizai.com",
                "owner": user,
            },
        )

        # Ensure Inventory
        items_data = [
            ("Coffee Beans", 15.00, 50),  # Base daily sales
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

        inventory_items = []
        for name, price, base_vol in items_data:
            item, _ = InventorModel.objects.get_or_create(
                item_name=name,
                defaults={
                    "item_description": f"Fresh {name}",
                    "quantity": 1000,
                    "quantity_unit": "pcs",
                    "type": "Consumable",
                    "selling_price": price,
                    "cost_price": price * 0.4,
                    "business": business,
                    "user": user,
                    "supplier": "Global Foods",
                    "min_quantity": 10,  # Also good to have
                },
            )
            # Store base volume on the object for generation logic
            item.base_vol = base_vol
            inventory_items.append(item)

        # Generate Data
        end_date = date.today()
        start_date = end_date - timedelta(days=days_to_generate)

        current_date = start_date
        sales_count = 0

        self.stdout.write(f"Generating data from {start_date} to {end_date}...")

        while current_date <= end_date:
            # Time features
            day_of_year = current_date.timetuple().tm_yday
            weekday = current_date.weekday()  # 0=Mon, 6=Sun

            # 1. Seasonality (Sine Wave) - Peak in Summer (approx day 180)
            seasonality = math.sin((day_of_year - 180) * 2 * math.pi / 365)
            # Scale seasonality: -1 to 1 -> 0.8 to 1.2 multiplier
            season_factor = 1.0 + (seasonality * 0.2)

            # 2. Weekly Pattern - Peak on Weekend
            if weekday >= 5:  # Sat, Sun
                week_factor = 1.3
            elif weekday == 4:  # Fri
                week_factor = 1.1
            else:
                week_factor = 1.0

            # 3. Trend (Linear Growth) - 20% growth over the year
            days_passed = (current_date - start_date).days
            trend_factor = 1.0 + (0.2 * (days_passed / days_to_generate))

            # Weather (Correlated with Season but with randomness)
            rand_weather = random.random()

            if season_factor > 1.1:  # Summer-ish
                if rand_weather > 0.8:
                    weather = "Rainy"
                    temp = 20 + random.uniform(-5, 5)
                elif rand_weather > 0.6:
                    weather = "Cloudy"
                    temp = 22 + random.uniform(-5, 5)
                else:
                    weather = "Sunny"
                    temp = 28 + random.uniform(-5, 5)
            elif season_factor < 0.9:  # Winter-ish
                if rand_weather > 0.7:
                    weather = "Rainy"
                    temp = 8 + random.uniform(-5, 5)
                elif rand_weather > 0.4:
                    weather = "Cloudy"
                    temp = 10 + random.uniform(-5, 5)
                else:
                    weather = "Cold"
                    temp = 2 + random.uniform(-5, 5)
            else:  # Spring/Fall
                if rand_weather > 0.7:
                    weather = "Rainy"
                    temp = 12 + random.uniform(-5, 5)
                elif rand_weather > 0.4:
                    weather = "Sunny"
                    temp = 18 + random.uniform(-5, 5)
                else:
                    weather = "Cloudy"
                    temp = 15 + random.uniform(-5, 5)

            # 4. "Closed Store" Scenario (Thesis Requirement)
            # Randomly skip 3-5 days (simulating holidays/emergencies)
            # 2% chance to start a closed block
            if random.random() < 0.02:
                closed_days = random.randint(3, 5)
                self.stdout.write(
                    f"Store Closed for {closed_days} days starting {current_date}"
                )
                current_date += timedelta(days=closed_days)
                continue

            for item in inventory_items:
                # Calculate Quantity
                # Base * Season * Week * Trend * Random Noise
                noise = random.uniform(0.9, 1.1)  # +/- 10% noise

                qty = int(
                    item.base_vol * season_factor * week_factor * trend_factor * noise
                )

                # Ensure positive
                qty = max(1, qty)

                revenue = float(item.selling_price) * qty

                SalesModel.objects.create(
                    sales_uid=f"SALE-{current_date.strftime('%Y%m%d')}-{item.id}",
                    prod_id=item,
                    sale_date=current_date,
                    quantity_sold=qty,
                    revenue=revenue,
                    customer_flow=int(qty * 1.5),
                    weather_temperature=temp,
                    weather_condition=weather,
                    was_on_sale=False,
                    is_active=True,
                )
                sales_count += 1

            current_date += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated {sales_count} realistic sales records!"
            )
        )
