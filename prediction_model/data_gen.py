import json
import random
from datetime import datetime, timedelta

def generate_dataset(filename='training_data.json', days=200):
    print(f"Generating {days} days of training data...")
    
    start_date = datetime.now() - timedelta(days=days)
    products = ['item_A', 'item_B']
    data = []
    
    # Configurations
    weather_types = ['Sunny', 'Cloudy', 'Rainy', 'Stormy']
    holidays = ['Christmas', 'New Year', 'Thanksgiving', 'Easter', 'Labor Day']
    festivals = ['Music Fest', 'Food Fest', 'Art Fair']
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Base environmental factors for the day
        is_weekend = current_date.weekday() >= 5
        day_weather = random.choices(weather_types, weights=[0.5, 0.3, 0.15, 0.05])[0]
        day_temp = round(random.uniform(15, 35), 1) if day_weather == 'Sunny' else round(random.uniform(5, 20), 1)
        fuel_price = round(random.uniform(3.50, 4.50), 2)
        
        # Event Logic
        is_holiday = 1 if random.random() < 0.05 else 0
        holiday_list = [random.choice(holidays)] if is_holiday else []
        
        has_festival = 1 if random.random() < 0.03 else 0
        festival_list = [random.choice(festivals)] if has_festival else []
        
        for pid in products:
            # Base Sales Logic
            base_sales = 100.0 if pid == 'item_A' else 50.0
            
            # Modifiers
            multiplier = 1.0
            if is_weekend: multiplier *= 1.2
            if day_weather == 'Sunny': multiplier *= 1.1
            if day_weather == 'Stormy': multiplier *= 0.6
            if is_holiday: multiplier *= 1.5
            if has_festival: multiplier *= 1.3
            
            final_sales = round(base_sales * multiplier * random.uniform(0.9, 1.1), 2)
            quantity = int(final_sales / 10)
            
            record = {
                "date": date_str,
                "product_id": pid,
                "sales_amount": final_sales,
                "sales_quantity": quantity,
                "weather_condition": day_weather,
                "temperature": day_temp,
                "fuel_price": fuel_price,
                "has_offers": 1 if random.random() > 0.7 else 0,
                "offer_amount": round(random.uniform(5, 20), 2) if random.random() > 0.7 else 0.0,
                "is_holiday": is_holiday,
                "holidays_list": holiday_list,
                "festivals": festival_list,
                "local_events": []
            }
            data.append(record)
            
    # Wrapper for the API
    payload = {
        "business_id": "biz_auto_gen_01",
        "data": data
    }
    
    with open(filename, 'w') as f:
        json.dump(payload, f, indent=2)
        
    print(f"Success! Saved {len(data)} records to {filename}")

if __name__ == '__main__':
    generate_dataset()