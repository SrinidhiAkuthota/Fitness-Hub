from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import threading
import time

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- STORAGE ---------------- #
users = {}
orders = []

# ---------------- ADMIN LOGIN ---------------- #
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

# ---------------- USER SECTION ---------------- #

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        users[request.form['username']] = request.form['password']
        return redirect('/login')
    return render_template('signup.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        if u in users and users[u] == p:
            session['user'] = u
            return redirect('/dashboard')

        return "Invalid Login ❌"

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard.html')


# WORKOUT
@app.route('/workout', methods=['GET','POST'])
def workout():
    plan = None
    if request.method == 'POST':
        goal = request.form['goal']
        if goal == "loss":
            plan = "Cardio + HIIT + Fat burn workouts"
        else:
            plan = "Strength training + Muscle building"
    return render_template('workout.html', plan=plan)


# DIET
@app.route('/diet', methods=['GET','POST'])
def diet():
    plan = None
    if request.method == 'POST':
        goal = request.form['goal']
        if goal == "loss":
            plan = "Salads, fruits, low carbs"
        else:
            plan = "High protein, rice, chicken"
    return render_template('diet.html', plan=plan)


# EXERCISE
@app.route('/exercise', methods=['GET','POST'])
def exercise():
    ex = None
    if request.method == 'POST':
        level = request.form['level']
        if level == "beginner":
            ex = "Walking, squats, pushups"
        else:
            ex = "Deadlift, bench press, HIIT"
    return render_template('exercise.html', ex=ex)


# ---------------- ADMIN SECTION ---------------- #

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid credentials ❌")

    return render_template('admin_login.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    total_orders = len(orders)
    total_revenue = sum(o['total'] for o in orders if o['status'] not in ["Cancelled", "Refunded"])
    pending_orders = sum(1 for o in orders if o['status'] == "Pending")
    delivered_orders = sum(1 for o in orders if o['status'] == "Delivered")

    return render_template(
        'admin_dashboard.html',
        orders=orders,
        total_orders=total_orders,
        total_revenue=total_revenue,
        pending_orders=pending_orders,
        delivered_orders=delivered_orders
    )


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))


# ---------------- ORDER SYSTEM ---------------- #

# SAVE ORDER
@app.route('/save_order', methods=['POST'])
def save_order():
    data = request.get_json()

    # DEFAULT STATUS
    data['status'] = "Pending"
    data['refund'] = "No"

    orders.append(data)

    # AUTO STATUS UPDATE (cool feature 🔥)
    threading.Thread(target=auto_update_status, args=(len(orders)-1,)).start()

    return jsonify({"status": "success"})


# GET ORDERS
@app.route('/get_orders')
def get_orders():
    return jsonify(orders)


# CANCEL ORDER
@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    data = request.get_json()
    index = data.get('index')

    if index is None:
        return jsonify({"status": "error"}), 400

    if index < len(orders):
        if orders[index]['status'] == "Pending":
            orders[index]['status'] = "Cancelled"

    return jsonify({"status": "success"})


# UPDATE STATUS (ADMIN)
@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()

    index = data['index']
    status = data['status']

    if index < len(orders):
        orders[index]['status'] = status

    return jsonify({"status": "updated"})


# REFUND SYSTEM ✅ (ONLY ONE ROUTE - FIXED)
@app.route('/refund_order', methods=['POST'])
def refund_order():
    data = request.get_json()
    index = data['index']

    if index < len(orders):
        orders[index]['refund'] = "Done"
        orders[index]['status'] = "Refunded"

    return jsonify({"status": "success"})


# ---------------- AUTO STATUS ---------------- #

def auto_update_status(index):
    time.sleep(5)
    if orders[index]['status'] == "Pending":
        orders[index]['status'] = "Shipped"

    time.sleep(5)
    if orders[index]['status'] == "Shipped":
        orders[index]['status'] = "Delivered"


# ---------------- RUN ---------------- #
if __name__ == '__main__':
    app.run(debug=True)