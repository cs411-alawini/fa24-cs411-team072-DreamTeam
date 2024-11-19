from flask import Flask, request, jsonify, render_template
import mysql.connector
import hashlib
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

GCP_DB_HOST = os.getenv('GCP_DB_HOST')
GCP_DB_USER = os.getenv('GCP_DB_USER')
GCP_DB_PASSWORD = os.getenv('GCP_DB_PASSWORD')
GCP_DB_NAME = os.getenv('GCP_DB_NAME')

db_config = {
    'host': GCP_DB_HOST,
    'user': GCP_DB_USER,
    'password': GCP_DB_PASSWORD,
    'database': GCP_DB_NAME,
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

## CRUD ##

# Create User
@app.route('/users/create', methods=['POST'])
def create_user():
    data = request.json
    hashed_password = hash_password(data['password'])
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO Users (username, name, password, is_admin) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (data['username'], data['name'], hashed_password, data['is_admin']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User created successfully!'}), 201
# Create Ticket
@app.route('/tickets/create', methods=['POST'])
def create_ticket():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO Tickets (ticket_id, event_title, ticket_price, fee, total_price, quantity, full_section, section, row_num) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (data["ticket_id"], data["event_title"], data["ticket_price"], data["fee"], data["total_price"], data["quantity"], data["full_section"], data["section"], data["row_num"]))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Ticket created successfully!'}), 201
# Create Event
@app.route('/events/create', methods=['POST'])
def create_event():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO Events (event_title, event_url, datetime_local, location_name, promoter_name) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (data["event_title"], data["event_url"], data["datetime_local"], data["location_name"], data["promoter_name"]))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Event created successfully!'}), 201

# Read Users
@app.route('/users/records', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, name, is_admin FROM Users")
    records = cursor.fetchall()
    conn.close()
    return jsonify(records)
# Read Tickets
@app.route('/tickets/records', methods=['GET'])
def get_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Tickets LIMIT 15")
    records = cursor.fetchall()
    conn.close()
    return jsonify(records)
# Read Events
@app.route('/events/records', methods=['GET'])
def get_events():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Events")
    records = cursor.fetchall()
    conn.close()
    return jsonify(records)

# Update User
@app.route('/users/update/<old_username>', methods=['PUT'])
def update_user(old_username):
    print(request.json)
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(data['password']) if 'password' in data else None
    query = "UPDATE Users SET username = %s, name = %s, password = %s, is_admin = %s WHERE username = %s"
    cursor.execute(query, (data['new_username'], data['name'], hashed_password, data['is_admin'], old_username))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User updated successfully!'})
# Update Ticket
@app.route('/tickets/update/<ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    # ticket_id, event_title, ticket_price, fee, total_price, quantity, full_section, section, row_num
    query = "UPDATE Tickets SET event_title = %s, ticket_price = %s, fee = %s, total_price = %s, quantity = %s, full_section = %s, section = %s, row_num = %s WHERE ticket_id = %s"
    cursor.execute(query, (data['event_title'], data['ticket_price'], data['fee'], data['total_price'], data['quantity'], data['full_section'], data['section'], data['row_num'], data["ticket_id"]))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Ticket updated successfully!'})
# Update Events
@app.route('/events/update/<old_event_title>', methods=['PUT'])
def update_event(old_event_title):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    # event_title, event_url, datetime_local, location_name, promoter_name
    query = "UPDATE Events SET event_title = %s, event_url = %s, datetime_local = %s, location_name = %s, promoter_name = %s WHERE event_title = %s"
    cursor.execute(query, (data['event_title'], data['event_url'], data['datetime_local'], data['location_name'], data['promoter_name'], old_event_title))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Event updated successfully!'})

# Delete User
@app.route('/users/delete/<username>', methods=['DELETE'])
def delete_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Users WHERE username = %s", (username,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User deleted successfully!'})
# Delete Ticket
@app.route('/tickets/delete/<ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Tickets WHERE ticket_id = %s", (ticket_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Ticket deleted successfully!'})
# Delete Event
@app.route('/events/delete/<event_title>', methods=['DELETE'])
def delete_event(event_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Events WHERE event_title = %s", (event_title,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Event deleted successfully!'})

if __name__ == '__main__':
    app.run(debug=True)