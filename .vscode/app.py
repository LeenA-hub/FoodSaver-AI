from flask import Flask, render_template, request, jsonify
import os
import csv
from datetime import datetime
import joblib
import pandas as pd
import requests
import json

app = Flask(__name__)

# -----------------
# Config & Setup
# -----------------
CSV_FILE = 'fridge_dataset.csv'
ITEMS_CSV = "../data/items.csv"


# Load food items
items_df = pd.read_csv(ITEMS_CSV)

# Initialize fridge CSV if missing
def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["item", "date_added", "days_left"])
init_csv()

# Load ML model and preprocessor
model = None
preprocessor = None
def load_model():
    global model, preprocessor
    if model is None or preprocessor is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        model = joblib.load(os.path.join(BASE_DIR, "trained_model", "train_model_betterversion.pkl"))
        preprocessor = joblib.load(os.path.join(BASE_DIR, "trained_model", "preprocessor.pkl"))

# -----------------
# Routes
# -----------------
@app.route('/')
def home():
    food_items = items_df['Food Item'].tolist()
    storage_methods = ['Fridge', 'Room Temp', 'Freezer']
    return render_template('index.html', foods=food_items, storages=storage_methods)

@app.route('/content')
def content():
    return render_template('content.html')

@app.route('/fridge')
def fridge():
    return render_template('fridge.html')

@app.route('/shopping')
def shopping():
    return render_template('shopping.html')

@app.route('/cooking')
def cooking():
    return render_template('cooking.html')

# -----------------
# Fridge Endpoints
# -----------------
@app.route("/save_item", methods=["POST"])
def save_item():
    data = request.get_json()
    item = data["item"]
    days_left = data.get("daysLeft", 7)
    date_added = datetime.now().strftime("%Y-%m-%d")

    # Read existing
    rows = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as f:
            rows = list(csv.reader(f))

    # Write back, skipping duplicates
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            if row and row[0] != item:
                writer.writerow(row)
        writer.writerow([item, date_added, days_left])

    return jsonify({"status": "saved"})

@app.route("/remove_item", methods=["POST"])
def remove_item():
    data = request.get_json()
    item_to_remove = data["item"]

    rows = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as f:
            rows = list(csv.reader(f))

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            if row and row[0] != item_to_remove:
                writer.writerow(row)

    return jsonify({"status": "removed"})

@app.route("/fridge_data")
def fridge_data():
    try:
        df = pd.read_csv(CSV_FILE)
        today = datetime.now().date()
        updated_rows = []
        items = {}

        for _, row in df.iterrows():
            item = row["item"]
            date_added = datetime.strptime(row["date_added"], "%Y-%m-%d").date()
            days_passed = (today - date_added).days
            days_left = max(int(row["days_left"]) - days_passed, 0)

            items[item] = {"exists": days_left > 0, "daysLeft": days_left}
            updated_rows.append([item, row["date_added"], days_left])

        pd.DataFrame(updated_rows, columns=["item", "date_added", "days_left"]).to_csv(CSV_FILE, index=False)
        return jsonify(items)
    except FileNotFoundError:
        return jsonify({})

# -----------------
# Prediction Endpoint
# -----------------
@app.route('/predict', methods=['POST'])
def predict():
    load_model()
    try:
        data = request.get_json(force=True)
        food_item = data.get("food", "").strip()
        storage = data.get("storage", "").strip()

        if not food_item or not storage:
            return jsonify({"error": "Missing food item or storage method"}), 400

        # Check if food item exists
        if food_item.lower() not in items_df["Food Item"].str.lower().values:
            return jsonify({"error": f"Item '{food_item}' not found in dataset"}), 404

        X_input = pd.DataFrame([[food_item, storage]], columns=["Food Item", "Storage"])
        X_transformed = preprocessor.transform(X_input)
        prediction = model.predict(X_transformed)[0]

        return jsonify({"food": food_item, "storage": storage, "prediction": float(prediction)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/predict', methods=['GET'])
def get_info():
    return jsonify({
        'message': "Send POST with 'food' and 'storage' to get prediction",
        'available_items': items_df['Food Item'].tolist()
    })

# -----------------
# Cooking generator
# -----------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.route("/generate_recipes", methods=["POST"])
def generate_recipes():
    try:
        payload = request.get_json(force=True) or {}
        ingredients = payload.get("ingredients", [])
        if not isinstance(ingredients, list) or not ingredients:
            return jsonify({"error": "Provide a non-empty list of ingredients"}), 400

        system = (
            "You are a helpful cooking assistant. "
            "Return EXACT JSON only, no extra text, with this schema:\n"
            '{ "recipes": [ { "title": str, "description": str, "steps": [str] } ] }'
        )
        user = (
            f"I have these ingredients: {', '.join(ingredients)}.\n"
            "Suggest 3 quick, simple recipes. Each recipe: description + up to 6 steps."
        )

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": 0.7,
                "max_tokens": 700,
            },
            timeout=30,
        )

        if resp.status_code != 200:
            return jsonify({"error": resp.text}), resp.status_code

        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        try:
            obj = json.loads(content)
            if not isinstance(obj, dict) or "recipes" not in obj:
                raise ValueError("Missing 'recipes' key")
            return jsonify(obj)
        except Exception:
            return jsonify({"recipes_text": content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------
# Run App
# -----------------
if __name__ == '__main__':
    app.run(debug=True)
