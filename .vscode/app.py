from flask import Flask, render_template, request, redirect, url_for
import pickle

app = Flask(__name__)

# Load ML model
from flask import Flask, render_template, request, redirect, url_for
import pickle
import os 
import csv

app = Flask(__name__)

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

DATA_FILE = "saved_items.csv"

# Utility: Save item
def save_item(item, storage):
    file_exists = os.path.isfile(DATA_FILE)
    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:  # add header if file doesn’t exist
            writer.writerow(["item", "storage"])
        writer.writerow([item, storage])

# Utility: Load items
def load_items():
    items = []
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            reader = csv.DictReader(f)
            items = list(reader)
    return items