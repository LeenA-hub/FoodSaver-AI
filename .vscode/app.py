
app = Flask(__name__)

# Load ML model
from flask import Flask, render_template, request, redirect, url_for
import pickle
import os 
import csv
from datetime import datetime, timedelta
import jsonify
import pandas as pd

app = Flask(__name__)

CSV_FILE = 'fridge_dataset.csv'

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["item", "date_added", "days_left"])
init_csv()



# Build safe absolute path to the model
model_path = os.path.join("trained_model", "model.pkl")

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/content')
def content():
    return render_template('content.html')

@app.route('/fridge')
def fridge():
    return render_template('fridge.html')


@app.route("/save_item", methods=["POST"])
def save_item():
    data = request.get_json()
    item = data["item"]
    days_left = data.get("daysLeft", 7)
    date_added = datetime.now().strftime("%Y-%m-%d")
    rows = []
    with open(CSV_FILE, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            if row and row[0] != item:  # keep other items
                writer.writerow(row)
        writer.writerow([item, date_added, days_left])  # save new item

    return jsonify({"status": "saved"})


@app.route("/remove_item", methods=["POST"])
def remove_item():
    data = request.get_json()
    item_to_remove = data["item"]

    rows = []
    with open(CSV_FILE, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

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

        # Auto-update days_left based on date_added
        today = datetime.now().date()
        updated_rows = []
        items = {}

        for _, row in df.iterrows():
            item = row["item"]
            date_added = datetime.strptime(row["date_added"], "%Y-%m-%d").date()
            days_passed = (today - date_added).days
            days_left = max(int(row["days_left"]) - days_passed, 0)

            items[item] = {
                "exists": days_left > 0,
                "daysLeft": days_left
            }
            updated_rows.append([item, row["date_added"], days_left])

        # Save back updated days_left to CSV
        pd.DataFrame(updated_rows, columns=["item", "date_added", "days_left"]).to_csv(CSV_FILE, index=False)

        return jsonify(items)
    except FileNotFoundError:
        return jsonify({})


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    prediction = None
    if request.method == 'POST':
        item = request.form['item']
        storage = request.form['storage']
        # Placeholder: later replace with real model code
        prediction = f"{item} stored in {storage} lasts 5 days"
    return render_template('predict.html', prediction=prediction)

@app.route('/shopping', methods=['GET', 'POST'])
def shopping():
    return render_template('shopping.html')

@app.route('/cooking', methods=['GET', 'POST'])
def cooking():
    return render_template('cooking.html')

if __name__ == '__main__':
    app.run(debug=True)
