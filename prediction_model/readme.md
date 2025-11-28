# Sales Forecast Service (PatchTST, Flask)

A multi-tenant Flask microservice exposing PatchTST-based time-series forecasting for retail sales.

## Endpoints

- `POST /retrain`  
  Train/retrain the PatchTST model for a `business_id`. Saves model & history for fast future predictions.

- `POST /predict`  
  One-off (ad-hoc) prediction using **only** the data in the request body. Model is not persisted.

- `POST /predict-fast`  
  Predict using the **pretrained** model of a `business_id`. Optionally pass the latest few days to extend context (no retrain).

Swagger UI: `http://localhost:8000/apidocs`

## Request/Response Formats

### 1) `/retrain` (POST)
**Body**
```json
{
  "business_id": "STORE-001",
  "data": [
    {
      "date": "2024-06-30",
      "product_id": "P-100",
      "units_sold": 21,
      "revenue": 105.0,
      "customer_flow": 16,
      "weather_temp": 24.5,
      "weather_condition": "Sunny",
      "holiday_name": "None",
      "is_store_open": 1,
      "is_on_sale": 0,
      "discount_percentage": 0.0,
      "flow_students": 0,
      "flow_families": 8,
      "flow_seniors": 8
    }
  ],
  "input_chunk_length": 56,
  "output_chunk_length": 14,
  "n_epochs": 25
}
