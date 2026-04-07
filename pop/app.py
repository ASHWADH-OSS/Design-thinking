import sqlite3
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.secret_key = 'urban_flow_2026_key'

# AI Oracle: Predicts surge based on time of day
def get_ai_surge():
    hour = datetime.now().hour
    # Training data: [Hour] -> [Demand Weight]
    X = np.array([[8], [9], [12], [17], [18], [22]]).reshape(-1, 1)
    y = np.array([90, 100, 40, 110, 105, 10]) 
    model = LinearRegression().fit(X, y)
    return max(0, int(model.predict([[hour]])[0]))

# Database setup
def init_db():
    with sqlite3.connect('urban_flow.db') as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, tokens INTEGER, flow_score REAL)')
        c.execute('CREATE TABLE IF NOT EXISTS routes (id PRIMARY KEY, name TEXT, base_cost INTEGER, bookings INTEGER)')
        c.execute('INSERT OR IGNORE INTO users VALUES (1, 1000, 98.2)')
        c.execute('INSERT OR IGNORE INTO routes VALUES (1, "Expressway A", 50, 0)')
        c.execute('INSERT OR IGNORE INTO routes VALUES (2, "City Blvd B", 30, 0)')
        conn.commit()

@app.route('/')
def index():
    surge = get_ai_surge()
    conn = sqlite3.connect('urban_flow.db')
    conn.row_factory = sqlite3.Row
    user = conn.execute('SELECT * FROM users WHERE id=1').fetchone()
    routes_raw = conn.execute('SELECT * FROM routes').fetchall()
    
    routes = []
    for r in routes_raw:
        price = r['base_cost'] + surge + (r['bookings'] * 5)
        routes.append({'id': r['id'], 'name': r['name'], 'price': price, 'load': r['bookings']})
    return render_template('index.html', user=user, routes=routes, surge=surge)

@app.route('/buy/<int:route_id>')
def buy(route_id):
    surge = get_ai_surge()
    conn = sqlite3.connect('urban_flow.db')
    route = conn.execute('SELECT * FROM routes WHERE id=?', (route_id,)).fetchone()
    price = route[2] + surge + (route[3] * 5)
    user_tokens = conn.execute('SELECT tokens FROM users WHERE id=1').fetchone()[0]

    if user_tokens >= price:
        conn.execute('UPDATE users SET tokens = tokens - ? WHERE id=1', (price,))
        conn.execute('UPDATE routes SET bookings = bookings + 1 WHERE id=?', (route_id,))
        conn.commit()
        flash(f"Route {route[1]} Booked!", "success")
    else:
        flash("Not enough tokens!", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)