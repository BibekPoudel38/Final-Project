import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import InventorModel, SupplierModel
from merchant.models import BusinessProfileModel, AddressModel
from sales.models import SalesModel, SalesHolidayModel


class Command(BaseCommand):
    help = "Populates the database with dummy sales and inventory data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email of the user to populate data for",
            default="admin@example.com",
        )

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting data population...")

        email = kwargs["email"]
        User = get_user_model()
        # Ensure we have a user
        user, created = User.objects.get_or_create(
            email=email, defaults={"is_admin": False, "is_active": True}
        )
        if created:
            user.set_password("admin")
            user.save()
            self.stdout.write(f"Created user {email}")

        # Ensure we have an address
        address, _ = AddressModel.objects.get_or_create(
            street="123 Main St",
            city="Tech City",
            state="CA",
            zip_code="90210",
            country="USA",
        )

        # Ensure we have a business profile
        business, _ = BusinessProfileModel.objects.get_or_create(
            business_name="BizAI Cafe",
            defaults={
                "address": address,
                "business_email": "contact@bizai.com",
                "business_phone": "555-0123",
                "owner": user,
            },
        )

        # Create Suppliers
        suppliers = []
        supplier_names = ["Global Foods", "Tech Supplies", "Fresh Farms", "Bean Co"]
        for name in supplier_names:
            supplier, _ = SupplierModel.objects.get_or_create(
                supplier_name=name,
                defaults={
                    "contact_person": f"Manager of {name}",
                    "contact_email": f"contact@{name.lower().replace(' ', '')}.com",
                    "contact_phone": "555-9999",
                    "contact_address": address,
                    "supplier_email": f"info@{name.lower().replace(' ', '')}.com",
                    "supplier_phone": "555-8888",
                },
            )
            suppliers.append(supplier)

        # Create Inventory Items
        items_data = [
            ("Coffee Beans", "Premium Arabica beans", 15.00, 8.00, "kg"),
            ("Milk", "Whole milk", 3.00, 1.50, "liter"),
            ("Sugar", "White sugar", 2.00, 0.80, "kg"),
            ("Croissant", "Butter croissant", 4.50, 1.20, "pcs"),
            ("Muffin", "Blueberry muffin", 3.50, 1.00, "pcs"),
            ("Sandwich", "Ham and cheese", 8.00, 3.00, "pcs"),
            ("Juice", "Orange juice", 5.00, 2.00, "bottle"),
            ("Tea Bags", "Earl Grey", 10.00, 4.00, "box"),
        ]

        inventory_items = []
        for name, desc, sell, cost, unit in items_data:
            item, _ = InventorModel.objects.get_or_create(
                item_name=name,
                defaults={
                    "item_description": desc,
                    "quantity": random.randint(50, 200),
                    "quantity_unit": unit,
                    "type": "Consumable",
                    "min_quantity": 20,
                    "auto_reorder": True,
                    "supplier": random.choice(suppliers).supplier_name,
                    "item_location": "Shelf A",
                    "cost_price": cost,
                    "selling_price": sell,
                    "last_restock_date": date.today()
                    - timedelta(days=random.randint(1, 30)),
                    "business": business,
                    "user": user,
                },
            )
            inventory_items.append(item)

        self.stdout.write(f"Ensured {len(inventory_items)} inventory items exist")

        # Create Holidays
        holidays_data = [
            ("New Year's Day", 1, 1),
            ("Valentine's Day", 2, 14),
            ("Independence Day", 7, 4),
            ("Halloween", 10, 31),
            ("Thanksgiving", 11, 23),  # Approximate
            ("Christmas", 12, 25),
        ]

        holidays = []
        current_year = date.today().year
        # Generate holidays for last year and this year
        for year in [current_year - 1, current_year]:
            for name, month, day in holidays_data:
                h_date = date(year, month, day)
                holiday, _ = SalesHolidayModel.objects.get_or_create(
                    name=name, date=h_date
                )
                holidays.append(holiday)

        self.stdout.write(f"Ensured {len(holidays)} holidays exist")

        # Generate Sales Data
        # Generate for the last 365 days
        end_date = date.today()
        start_date = end_date - timedelta(days=365)

        sales_count = 0
        current_date = start_date
        while current_date <= end_date:
            # Determine if it's a weekend
            is_weekend = current_date.weekday() >= 5

            # Base flow based on weekend
            base_flow = 200 if is_weekend else 100

            # Seasonality (simple approximation)
            month = current_date.month
            if month in [12, 1, 2]:  # Winter
                temp = random.uniform(0, 10)
                weather = "Cold"
            elif month in [3, 4, 5]:  # Spring
                temp = random.uniform(10, 20)
                weather = "Mild"
            elif month in [6, 7, 8]:  # Summer
                temp = random.uniform(20, 35)
                weather = "Hot"
            else:  # Fall
                temp = random.uniform(10, 20)
                weather = "Rainy" if random.random() > 0.7 else "Cloudy"

            # Check for holiday
            days_holidays = [h for h in holidays if h.date == current_date]
            if days_holidays:
                base_flow *= 1.5  # More traffic on holidays
                weather += " (Holiday)"

            # Generate sales for each product
            for item in inventory_items:
                # Random chance to sell this item today
                if random.random() > 0.2:
                    # Quantity sold
                    qty = random.randint(1, 20)
                    if is_weekend:
                        qty += 5
                    if days_holidays:
                        qty += 10

                    # Revenue
                    revenue = float(item.selling_price) * qty

                    # Create Sale
                    sale = SalesModel.objects.create(
                        sales_uid=f"SALE-{current_date.strftime('%Y%m%d')}-{item.id}-{random.randint(1000, 9999)}",
                        prod_id=item,
                        sale_date=current_date,
                        quantity_sold=qty,
                        revenue=revenue,
                        customer_flow=int(base_flow + random.randint(-20, 20)),
                        weather_temperature=temp,
                        weather_condition=weather,
                        was_on_sale=random.random() > 0.9,
                        promotion_type="Seasonal" if random.random() > 0.9 else None,
                        flow_students=int(base_flow * 0.3),
                        flow_family=int(base_flow * 0.4),
                        flow_adults=int(base_flow * 0.3),
                    )

                    if days_holidays:
                        sale.holidays.set(days_holidays)

                    sales_count += 1

            current_date += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully generated {sales_count} sales records")
        )
