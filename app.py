import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os, json, csv
from io import StringIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'finwise-secret'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# =========================
# USER AUTHENTICATION SETUP
# =========================

class User(UserMixin):
    def __init__(self, id):
        self.id = id

def load_users():
    with open('users.json') as f:
        return json.load(f)

@login_manager.user_loader
def load_user(user_id):
    print(f"Loading user with ID: {user_id}")
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        users    = load_users()
        username = request.form['username']
        password = request.form['password']
        for user in users:
            if user['username'] == username and user['password'] == password:
                login_user(User(username))
                return redirect(url_for('index'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# =========================
# LOAD/SAVE DATA
# =========================

def load_data():
    try:
        with open('data.json') as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=2)

tips = [
    "Track every rupee. Small leaks sink big ships!",
    "Start saving 20% of your income today.",
    "Avoid impulse purchases—wait 24 hours!",
    "Use the 50/30/20 rule for smart budgeting.",
    "Invest early—compound interest is magical!",
    "Create an emergency fund for unexpected costs.",
]

@app.route('/')
@login_required
def index():
    print(f"Current user: {current_user.get_id()}")
    data = load_data()

    # Balance
    balance = sum(item['amount'] if item['type'] == 'income' else -item['amount'] for item in data)

    # Expense categories
    categories = {}
    for entry in data:
        if entry['type'] == 'expense':
            categories[entry['category']] = categories.get(entry['category'], 0) + entry['amount']

    if categories:
        plt.figure(figsize=(4, 4))
        plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%', startangle=140)
        plt.title('Expense Breakdown')
        plt.tight_layout()
        plt.savefig(os.path.join('static', 'chart.png'))
        plt.close()

    tip = tips[len(data) % len(tips)]

    return render_template('index.html', data=data, balance=balance, tip=tip)

@app.route('/add', methods=['POST'])
@login_required
def add():
    data = load_data()
    try:
        amount   = float(request.form['amount'])
        category = request.form['category'].capitalize()
        type_    = request.form['type'].lower()
        data.append({
            'amount': amount,
            'category': category,
            'type': type_,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        save_data(data)
    except:
        pass
    return redirect(url_for('index'))

@app.route('/export')
@login_required
def export():
    data = load_data()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Amount', 'Category', 'Type'])
    for item in data:
        writer.writerow([item['amount'], item['category'], item['type']])
    output = si.getvalue()
    return send_file(
        StringIO(output),
        mimetype="text/csv",
        as_attachment=True,
        download_name="finwise_export.csv"
    )

@app.route('/data')
@login_required
def data_api():
    return jsonify(data=load_data())

if __name__ == '__main__':
    app.run(debug=True)

