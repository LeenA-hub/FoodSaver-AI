from flask import Flask, render_template, request, redirect, url_for
import pickle

app = Flask(__name__)

# Load ML model
from flask import Flask, render_template, request, redirect, url_for
import pickle
import os   # <-- you need this

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
