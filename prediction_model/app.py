import os
import json
import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from flask import Flask, request, jsonify, send_file
from flasgger import Swagger
from sklearn.preprocessing import StandardScaler, LabelEncoder
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURATION & CONSTANTS
# ==========================================
app = Flask(__name__)
swagger = Swagger(
    app,
    template={
        "info": {
            "title": "PatchTST Sales Forecasting API",
            "description": "Multivariate Time-Series Forecasting using PatchTST with Cold-Start handling.",
            "version": "2.0",
        }
    },
)

MODEL_DIR = "model_store"
os.makedirs(MODEL_DIR, exist_ok=True)

# PatchTST Hyperparameters
CONFIG = {
    "patch_len": 8,
    "stride": 4,
    "d_model": 128,
    "n_heads": 4,
    "n_layers": 2,
    "d_ff": 256,
    "dropout": 0.2,
    "forecast_horizon": 7,
    "context_window": 60,
    "min_samples_for_dl": 40,
    "num_targets": 2,  # Targets: [Sales_Amount, Sales_Quantity]
}

REQUIRED_COLUMNS = [
    "sales_amount",
    "sales_quantity",
    "weather_condition",
    "temperature",
    "fuel_price",
    "has_offers",
    "offer_amount",
    "is_holiday",
    "holidays_list",
    "festivals",
    "local_events",
]

# ==========================================
# 2. VALIDATION LOGIC
# ==========================================


def validate_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_entry(entry, strict_cols=True):
    errors = []
    if "date" not in entry:
        errors.append("Missing 'date' field")
    elif not validate_date(entry["date"]):
        errors.append(f"Invalid date format: {entry['date']}. Expected YYYY-MM-DD")

    if strict_cols and "product_id" not in entry:
        errors.append("Missing 'product_id'")

    if "sales_amount" in entry and (
        not isinstance(entry["sales_amount"], (int, float)) or entry["sales_amount"] < 0
    ):
        errors.append("Invalid 'sales_amount': must be non-negative number")

    if "sales_quantity" in entry and (
        not isinstance(entry["sales_quantity"], (int, float))
        or entry["sales_quantity"] < 0
    ):
        errors.append("Invalid 'sales_quantity': must be non-negative number")

    list_fields = ["holidays_list", "festivals", "local_events"]
    for field in list_fields:
        if field in entry:
            if not isinstance(entry[field], list):
                errors.append(
                    f"Invalid '{field}': must be a JSON list (e.g., ['Event A'])"
                )
    return errors


# ==========================================
# 3. PATCHTST MODEL ARCHITECTURE
# ==========================================


class PatchEmbedding(nn.Module):
    def __init__(self, d_model, patch_len, stride, num_features, dropout):
        super().__init__()
        self.patch_len = patch_len
        self.stride = stride
        self.padding_patch_layer = nn.ReplicationPad1d((0, stride))
        self.value_embedding = nn.Linear(patch_len * num_features, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        B, L, F = x.shape
        # Dynamic Padding
        if (L - self.patch_len) % self.stride != 0:
            pad_len = self.stride - ((L - self.patch_len) % self.stride)
            x = x.permute(0, 2, 1)
            x = torch.nn.functional.pad(x, (0, pad_len), mode="replicate")
            x = x.permute(0, 2, 1)
            L = x.shape[1]

        patches = x.unfold(dimension=1, size=self.patch_len, step=self.stride)
        patches = patches.permute(0, 1, 3, 2)
        B, N, P, F = patches.shape
        patches = patches.reshape(B, N, P * F)

        x_emb = self.value_embedding(patches)
        return self.dropout(x_emb)


class PatchTST(nn.Module):
    def __init__(self, config, num_features):
        super().__init__()
        self.config = config
        self.num_features = num_features
        self.patch_len = config["patch_len"]
        self.stride = config["stride"]
        self.context_window = config["context_window"]
        self.forecast_horizon = config["forecast_horizon"]
        self.num_targets = config.get("num_targets", 1)

        self.patch_embedding = PatchEmbedding(
            config["d_model"],
            self.patch_len,
            self.stride,
            self.num_features,
            config["dropout"],
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config["d_model"],
            nhead=config["n_heads"],
            dim_feedforward=config["d_ff"],
            dropout=config["dropout"],
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(
            encoder_layer, num_layers=config["n_layers"]
        )

        # Calculate patch count based on max context window + padding logic
        pad_len = (
            self.stride - ((self.context_window - self.patch_len) % self.stride)
        ) % self.stride
        padded_len = self.context_window + pad_len
        self.num_patches = (padded_len - self.patch_len) // self.stride + 1

        # Projection Head
        self.head = nn.Linear(
            config["d_model"] * self.num_patches,
            self.forecast_horizon * self.num_targets,
        )

    def forward(self, x):
        B, L, F = x.shape
        x_emb = self.patch_embedding(x)
        z = self.encoder(x_emb)
        z = z.reshape(B, -1)

        forecast = self.head(z)
        # Reshape to [Batch, Horizon, Num_Targets]
        forecast = forecast.reshape(B, self.forecast_horizon, self.num_targets)
        return forecast


# ==========================================
# 4. PREDICTOR LOGIC
# ==========================================


class SalesPredictor:
    def __init__(self, business_id):
        self.business_id = business_id
        self.model_type = "naive"
        self.model = None
        # self.scaler = StandardScaler() # Removed Global Scaler
        self.label_encoders = {}
        self.last_context = None
        self.item_ids = []
        self.num_features = 0
        self.num_targets = CONFIG["num_targets"]

    def _process_features(self, df, is_training=True):
        # Ensure columns exist
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                if col in ["has_offers", "is_holiday"]:
                    df[col] = 0
                elif col in [
                    "sales_amount",
                    "sales_quantity",
                    "fuel_price",
                    "temperature",
                    "offer_amount",
                ]:
                    df[col] = 0.0
                else:
                    df[col] = "unknown"

        # Encode Categoricals
        cat_cols = ["weather_condition", "holidays_list", "festivals", "local_events"]
        for col in cat_cols:
            df[col] = df[col].apply(
                lambda x: json.dumps(x) if isinstance(x, list) else str(x)
            )
            if is_training:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col])
                self.label_encoders[col] = le
            else:
                le = self.label_encoders.get(col)
                if le:
                    known_classes = set(le.classes_)
                    fallback = list(known_classes)[0]
                    df[col] = df[col].apply(
                        lambda x: x if x in known_classes else fallback
                    )
                    df[col] = le.transform(df[col])
                else:
                    df[col] = 0

        # Encode Booleans
        bool_cols = ["has_offers", "is_holiday"]
        for col in bool_cols:
            df[col] = df[col].astype(int)

        return df[REQUIRED_COLUMNS]

    def train(self, raw_data):
        df = pd.DataFrame(raw_data)
        if "date" not in df.columns:
            df["date"] = pd.date_range(
                end=pd.Timestamp.now(), periods=len(df), freq="D"
            )
        else:
            df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        self.item_ids = df["product_id"].unique().tolist()
        n_samples = len(df)

        # STRATEGY SELECTION
        if n_samples < CONFIG["min_samples_for_dl"]:
            print(f"[{self.business_id}] Insufficient data. Using Naive Fallback.")
            self.model_type = "naive"
            self.model = {}
            for item in self.item_ids:
                item_df = df[df["product_id"] == item]
                if not item_df.empty:
                    self.model[item] = {
                        "amount_avg": item_df["sales_amount"].tail(7).mean(),
                        "qty_avg": item_df["sales_quantity"].tail(7).mean(),
                    }
        else:
            print(f"[{self.business_id}] Training Multivariate PatchTST with RevIN.")
            self.model_type = "patchtst"
            self._train_patchtst(df)

        # Save Context
        self.last_context = {}
        processed_df = self._process_features(df.copy(), is_training=True)
        processed_df["product_id"] = df["product_id"]

        for item in self.item_ids:
            item_data = processed_df[processed_df["product_id"] == item]
            self.last_context[item] = (
                item_data[REQUIRED_COLUMNS]
                .tail(CONFIG["context_window"])
                .values.tolist()
            )

    def _train_patchtst(self, df):
        processed_df = self._process_features(df.copy(), is_training=True)
        processed_df["product_id"] = df["product_id"]
        self.num_features = len(REQUIRED_COLUMNS)

        X_list, Y_list = [], []
        L = CONFIG["context_window"]
        H = CONFIG["forecast_horizon"]

        for item in self.item_ids:
            item_df = processed_df[processed_df["product_id"] == item]
            data_vals = item_df[REQUIRED_COLUMNS].values

            if len(data_vals) < L + H:
                continue

            for i in range(len(data_vals) - L - H + 1):
                X_list.append(data_vals[i : i + L])
                # Target: Amount (0) and Quantity (1)
                Y_list.append(data_vals[i + L : i + L + H, 0 : self.num_targets])

        if not X_list:
            self.model_type = "naive"
            return

        X_arr = np.array(X_list, dtype=np.float32)
        Y_arr = np.array(Y_list, dtype=np.float32)

        # NO GLOBAL SCALING - RevIN handles it per instance

        X_tensor = torch.FloatTensor(X_arr)
        Y_tensor = torch.FloatTensor(Y_arr)

        self.model = PatchTST(CONFIG, num_features=self.num_features)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        self.model.train()
        dataset = torch.utils.data.TensorDataset(X_tensor, Y_tensor)
        loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)

        for epoch in range(30):
            for bx, by in loader:
                optimizer.zero_grad()

                # --- RevIN Logic (Instance Normalization) ---
                # 1. Calculate Mean/Std for the TARGET columns in the INPUT window
                # We only normalize the targets because we want to predict them relative to the window
                # bx shape: [Batch, Window, Features]
                # Targets are at indices 0 and 1

                target_bx = bx[:, :, 0 : self.num_targets]  # [B, L, 2]
                mean = torch.mean(target_bx, dim=1, keepdim=True)  # [B, 1, 2]
                std = torch.std(target_bx, dim=1, keepdim=True) + 1e-5  # [B, 1, 2]

                # Normalize Input Targets
                bx_norm = bx.clone()
                bx_norm[:, :, 0 : self.num_targets] = (target_bx - mean) / std

                # Normalize Output Targets (Labels)
                # by shape: [Batch, Horizon, 2]
                by_norm = (by - mean) / std  # Broadcast mean/std from input window

                # Forward
                out = self.model(bx_norm)

                # Loss on Normalized Data
                loss = criterion(out, by_norm)

                loss.backward()
                optimizer.step()
        self.model.eval()

    def predict_step_by_step(self, future_entries, req_item_ids):
        results = {item: [] for item in req_item_ids}

        if self.model_type == "naive":
            for item in req_item_ids:
                stats = self.model.get(item, {"amount_avg": 0, "qty_avg": 0})
                results[item] = [
                    {
                        "sales_amount": stats["amount_avg"],
                        "sales_quantity": int(stats["qty_avg"]),
                        "confidence_score": 50.0,
                    }
                ] * len(future_entries)
            return results

        if self.model_type == "patchtst":
            future_df = pd.DataFrame(future_entries)
            # Add dummy targets if missing
            if "sales_amount" not in future_df.columns:
                future_df["sales_amount"] = 0
            if "sales_quantity" not in future_df.columns:
                future_df["sales_quantity"] = 0

            processed_future = self._process_features(future_df, is_training=False)
            future_feats = processed_future.values

            # Load Contexts
            running_contexts = {}
            for item in req_item_ids:
                ctx = self.last_context.get(item)
                if ctx is None:
                    ctx = np.zeros((CONFIG["context_window"], self.num_features))
                else:
                    ctx = np.array(ctx)
                    if len(ctx) < CONFIG["context_window"]:
                        pad = np.zeros(
                            (CONFIG["context_window"] - len(ctx), self.num_features)
                        )
                        ctx = np.vstack([pad, ctx])
                running_contexts[item] = ctx

            # AUTO-REGRESSIVE LOOP
            for i in range(len(future_feats)):
                input_batch = []
                for item in req_item_ids:
                    input_batch.append(running_contexts[item])

                input_arr = np.array(input_batch, dtype=np.float32)
                input_tensor = torch.FloatTensor(input_arr)  # [B, L, F]

                # --- RevIN Logic for Prediction ---
                # 1. Calc Stats
                target_input = input_tensor[:, :, 0 : self.num_targets]
                mean = torch.mean(target_input, dim=1, keepdim=True)
                std = torch.std(target_input, dim=1, keepdim=True) + 1e-5

                # 2. Normalize Input
                input_norm = input_tensor.clone()
                input_norm[:, :, 0 : self.num_targets] = (target_input - mean) / std

                with torch.no_grad():
                    forecast_norm = self.model(input_norm)  # [B, Horizon, 2]

                # 3. Denormalize Output (Inverse RevIN)
                # We only need the first step of the horizon for autoregression
                next_step_norm = forecast_norm[:, 0, :]  # [B, 2]

                # Reshape mean/std for broadcasting: [B, 1, 2] -> [B, 2]
                mean_sq = mean.squeeze(1)
                std_sq = std.squeeze(1)

                next_vals = (next_step_norm * std_sq) + mean_sq
                next_vals = next_vals.numpy()

                current_future_feats = future_feats[i]

                for idx, item in enumerate(req_item_ids):
                    # Cast to python float to avoid JSON errors
                    pred_amt = float(max(0, round(next_vals[idx][0], 2)))
                    pred_qty = float(max(0, round(next_vals[idx][1], 0)))

                    # Calculate Variance Confidence
                    ctx_variance = np.var(running_contexts[item][:, 0])
                    confidence_score = max(0, min(100, 100 - (ctx_variance / 100)))

                    results[item].append(
                        {
                            "sales_amount": pred_amt,
                            "sales_quantity": int(pred_qty),
                            "confidence_score": round(confidence_score, 1),
                        }
                    )

                    # Update History with PREDICTION (Autoregression)
                    new_row = current_future_feats.copy()
                    new_row[0] = pred_amt
                    new_row[1] = pred_qty

                    prev_ctx = running_contexts[item]
                    running_contexts[item] = np.vstack([prev_ctx[1:], new_row])

        return results

    def save(self):
        model_state = None
        if self.model is not None:
            model_state = self.model.state_dict()
            self.model = None

        pkl_path = os.path.join(MODEL_DIR, f"{self.business_id}.pkl")
        with open(pkl_path, "wb") as f:
            pickle.dump(self, f)

        if model_state is not None:
            pth_path = os.path.join(MODEL_DIR, f"{self.business_id}.pth")
            torch.save(model_state, pth_path)
            # Restore
            self.model = PatchTST(CONFIG, num_features=self.num_features)
            self.model.load_state_dict(model_state)
            self.model.eval()

    @staticmethod
    def load(business_id):
        pkl_path = os.path.join(MODEL_DIR, f"{business_id}.pkl")
        if not os.path.exists(pkl_path):
            return None
        with open(pkl_path, "rb") as f:
            predictor = pickle.load(f)

        pth_path = os.path.join(MODEL_DIR, f"{business_id}.pth")
        if os.path.exists(pth_path) and predictor.model_type == "patchtst":
            predictor.model = PatchTST(CONFIG, num_features=predictor.num_features)
            # Safety: Weights Only
            weights = torch.load(pth_path, weights_only=True)
            predictor.model.load_state_dict(weights)
            predictor.model.eval()
        return predictor


# ==========================================
# 5. API ENDPOINTS (With Swagger Docs)
# ==========================================


def calculate_metrics(y_true, y_pred):
    from sklearn.metrics import (
        mean_absolute_error,
        mean_squared_error,
        r2_score,
        explained_variance_score,
    )

    # Flatten
    y_true = np.array(y_true).flatten()
    y_pred = np.array(y_pred).flatten()

    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)

    # MAPE handling zeros
    mask = y_true != 0
    if np.any(mask):
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    else:
        mape = 0.0

    r2 = r2_score(y_true, y_pred)
    explained_var = explained_variance_score(y_true, y_pred)

    return {
        "mae": float(mae),
        "mse": float(mse),
        "rmse": float(rmse),
        "mape": float(mape),
        "r2_score": float(r2),
        "explained_variance": float(explained_var),
    }


@app.route("/retrain", methods=["POST"])
def retrain():
    """
    Train the Forecasting Model for a Business.
    ---
    tags:
      - Training
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - business_id
            - data
          properties:
            business_id:
              type: string
              example: "biz_001"
            data:
              type: array
              items:
                type: object
                properties:
                  date:
                    type: string
                    example: "2025-01-01"
                  product_id:
                    type: string
                    example: "item_A"
                  sales_amount:
                    type: number
                    example: 150.50
                  sales_quantity:
                    type: integer
                    example: 5
                  weather_condition:
                    type: string
                    example: "Sunny"
                  temperature:
                    type: number
                    example: 25.0
                  fuel_price:
                    type: number
                    example: 4.10
                  has_offers:
                    type: integer
                    example: 1
                  offer_amount:
                    type: number
                    example: 10.0
                  is_holiday:
                    type: integer
                    example: 0
                  holidays_list:
                    type: array
                    items:
                      type: string
                  festivals:
                    type: array
                    items:
                      type: string
                  local_events:
                    type: array
                    items:
                      type: string
    responses:
      200:
        description: Model trained successfully
        schema:
          type: object
          properties:
            status:
              type: string
            model_type:
              type: string
            metrics:
              type: object
            training_info:
              type: object
      400:
        description: Validation error
    """
    try:
        content = request.json
        business_id = content.get("business_id")
        raw_data = content.get("data")
        if not business_id or not raw_data:
            return jsonify({"error": "Missing fields"}), 400

        # Clean old files
        pkl_path = os.path.join(MODEL_DIR, f"{business_id}.pkl")
        pth_path = os.path.join(MODEL_DIR, f"{business_id}.pth")
        if os.path.exists(pkl_path):
            os.remove(pkl_path)
        if os.path.exists(pth_path):
            os.remove(pth_path)

        # Prepare Data
        df = pd.DataFrame(raw_data)
        if "date" not in df.columns:
            df["date"] = pd.date_range(
                end=pd.Timestamp.now(), periods=len(df), freq="D"
            )
        else:
            df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        # 80/20 Split for Validation
        n_total = len(df)
        split_idx = int(n_total * 0.8)

        # Ensure we have enough data for a meaningful split
        if split_idx > CONFIG["context_window"] and (n_total - split_idx) > 1:
            train_df = df.iloc[:split_idx].copy()
            test_df = df.iloc[split_idx:].copy()

            # 1. Train Validation Model
            val_predictor = SalesPredictor(business_id + "_val")
            val_predictor.train(train_df.to_dict(orient="records"))

            # 2. Predict on Test Set
            test_dates = test_df["date"].dt.strftime("%Y-%m-%d").unique().tolist()
            test_items = test_df["product_id"].unique().tolist()

            future_entries = [{"date": d} for d in test_dates]
            forecast = val_predictor.predict_step_by_step(future_entries, test_items)

            # 3. Calculate Metrics
            y_true_amt = []
            y_pred_amt = []

            # Align predictions with actuals
            for i, date_str in enumerate(test_dates):
                date_obj = pd.to_datetime(date_str)
                for item in test_items:
                    actual_row = test_df[
                        (test_df["date"] == date_obj) & (test_df["product_id"] == item)
                    ]
                    if not actual_row.empty:
                        actual_amt = actual_row.iloc[0]["sales_amount"]
                        pred_amt = forecast[item][i]["sales_amount"]

                        y_true_amt.append(actual_amt)
                        y_pred_amt.append(pred_amt)

            if y_true_amt:
                metrics = calculate_metrics(y_true_amt, y_pred_amt)
                metrics["accuracy"] = metrics["r2_score"]
            else:
                metrics = {
                    k: 0.0
                    for k in [
                        "mae",
                        "mse",
                        "rmse",
                        "mape",
                        "r2_score",
                        "explained_variance",
                        "accuracy",
                    ]
                }

            training_info = {
                "train_start": train_df["date"].min().strftime("%Y-%m-%d"),
                "train_end": train_df["date"].max().strftime("%Y-%m-%d"),
                "test_start": test_df["date"].min().strftime("%Y-%m-%d"),
                "test_end": test_df["date"].max().strftime("%Y-%m-%d"),
                "split_ratio": "80/20",
            }

        else:
            # Fallback for small data: Train on all, no validation metrics
            metrics = {
                k: 0.0
                for k in [
                    "mae",
                    "mse",
                    "rmse",
                    "mape",
                    "r2_score",
                    "explained_variance",
                    "accuracy",
                ]
            }
            training_info = {
                "train_start": df["date"].min().strftime("%Y-%m-%d"),
                "train_end": df["date"].max().strftime("%Y-%m-%d"),
                "test_start": "N/A",
                "test_end": "N/A",
                "split_ratio": "100/0 (Insufficient Data)",
            }

        # 4. Final Training on Full Dataset
        final_predictor = SalesPredictor(business_id)
        final_predictor.train(raw_data)
        final_predictor.save()

        metrics["model_version"] = (
            f"PatchTST-v2.{datetime.now().strftime('%Y%m%d%H%M')}"
        )

        return jsonify(
            {
                "status": "success",
                "model_type": final_predictor.model_type,
                "metrics": metrics,
                "training_info": training_info,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict", methods=["POST"])
def predict():
    """
    Standard Prediction (Assuming neutral future conditions).
    ---
    tags:
      - Forecasting
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - business_id
            - begin_date
            - end_date
            - item_ids
          properties:
            business_id:
              type: string
              example: "biz_001"
            begin_date:
              type: string
              example: "2025-06-01"
            end_date:
              type: string
              example: "2025-06-03"
            item_ids:
              type: array
              items:
                type: string
                example: "item_A"
    responses:
      200:
        description: Forecast generated
        schema:
          type: object
          properties:
            business_id:
              type: string
            forecast:
              type: array
              items:
                type: object
    """
    try:
        content = request.json
        predictor = SalesPredictor.load(content.get("business_id"))
        if not predictor:
            return jsonify({"error": "Model not found"}), 404

        start = pd.to_datetime(content.get("begin_date"))
        end = pd.to_datetime(content.get("end_date"))
        days = (end - start).days + 1

        dummy_future = []
        for i in range(days):
            dummy_future.append(
                {"date": (start + timedelta(days=i)).strftime("%Y-%m-%d")}
            )

        forecast = predictor.predict_step_by_step(dummy_future, content.get("item_ids"))

        formatted = []
        for i, entry in enumerate(dummy_future):
            day_data = {"date": entry["date"], "predictions": []}
            for item in content.get("item_ids"):
                pred_data = forecast[item][i]
                day_data["predictions"].append(
                    {
                        "item_id": item,
                        "sales_amount": pred_data["sales_amount"],
                        "sales_quantity": pred_data["sales_quantity"],
                        "confidence_score": pred_data["confidence_score"],
                    }
                )
            formatted.append(day_data)

        return jsonify({"business_id": predictor.business_id, "forecast": formatted})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict_custom", methods=["POST"])
def predict_custom():
    """
    Advanced Prediction with Known Future Events.
    ---
    tags:
      - Forecasting
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - business_id
            - item_ids
            - future_data
          properties:
            business_id:
              type: string
              example: "biz_001"
            item_ids:
              type: array
              items:
                type: string
              example: ["item_A", "item_B"]
            future_data:
              type: array
              items:
                type: object
                properties:
                  date:
                    type: string
                    example: "2025-12-25"
                  weather_condition:
                    type: string
                    example: "Snowy"
                  temperature:
                    type: number
                    example: -5.0
                  fuel_price:
                    type: number
                    example: 4.20
                  has_offers:
                    type: integer
                    example: 1
                  offer_amount:
                    type: number
                    example: 15.0
                  is_holiday:
                    type: integer
                    example: 1
                  holidays_list:
                    type: array
                    items:
                      type: string
                    example: ["Christmas"]
                  festivals:
                    type: array
                    items:
                      type: string
                    example: []
                  local_events:
                    type: array
                    items:
                      type: string
                    example: []
    responses:
      200:
        description: Forecast generated
    """
    try:
        content = request.json
        predictor = SalesPredictor.load(content.get("business_id"))
        if not predictor:
            return jsonify({"error": "Model not found"}), 404

        future_data = content.get("future_data")
        item_ids = content.get("item_ids")

        forecast = predictor.predict_step_by_step(future_data, item_ids)

        formatted = []
        for i, entry in enumerate(future_data):
            day_data = {"date": entry.get("date"), "predictions": []}
            for item in item_ids:
                pred_data = forecast[item][i]
                day_data["predictions"].append(
                    {
                        "item_id": item,
                        "sales_amount": pred_data["sales_amount"],
                        "sales_quantity": pred_data["sales_quantity"],
                        "confidence_score": pred_data["confidence_score"],
                    }
                )
            formatted.append(day_data)

        return jsonify({"business_id": predictor.business_id, "forecast": formatted})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download_model/<business_id>", methods=["GET"])
def download_model(business_id):
    """
    Download the trained model file for a business.
    ---
    tags:
      - Model Management
    parameters:
      - name: business_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: Model file
      404:
        description: Model not found
    """
    try:
        # Check for .pth file first (PyTorch weights)
        pth_path = os.path.join(MODEL_DIR, f"{business_id}.pth")
        if os.path.exists(pth_path):
            return send_file(pth_path, as_attachment=True)

        # Fallback to .pkl (Full object)
        pkl_path = os.path.join(MODEL_DIR, f"{business_id}.pkl")
        if os.path.exists(pkl_path):
            return send_file(pkl_path, as_attachment=True)

        return jsonify({"error": "Model not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
