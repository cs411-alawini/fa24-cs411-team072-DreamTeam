from flask import Flask, request, jsonify, render_template, render_template_string, session, redirect, url_for
import mysql.connector
import hashlib
import os
from dotenv import load_dotenv
from mysql.connector.errors import DatabaseError
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure FLASK_DEBUG from environment variable
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG')

load_dotenv()

# Access environment variables as if they came from the actual environment
GCP_DB_HOST = os.getenv('GCP_DB_HOST')
GCP_DB_USER = os.getenv('GCP_DB_USER')
GCP_DB_PASSWORD = os.getenv('GCP_DB_PASSWORD')
GCP_DB_NAME = os.getenv('GCP_DB_NAME')
APP_SECRET_KEY = os.getenv('APP_SECRET_KEY')
# Database configuration from environment variables

app.secret_key = APP_SECRET_KEY

db_config = {
    'host': GCP_DB_HOST,
    'user': GCP_DB_USER,
    'password': GCP_DB_PASSWORD,
    'database': GCP_DB_NAME,
}
# Connect to MySQL
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Helper function to hash passwords
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


@app.route('/')
def home():
    """Redirect to events page if logged in, otherwise to login page."""
    if 'user' in session and session['is_admin']==0:
        return redirect(url_for('events_page'))
    return redirect(url_for('login'))

@app.route('/admin')
def index():
    return render_template('index.html')

# CRUD APIs

# Create User
@app.route('/users/create', methods=['POST'])
def create_user():
    data = request.json
    conn = None
    try:
        hashed_password = hash_password(data['password'])
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO Users (username, name, password, is_admin) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (data['username'], data['name'], hashed_password, data['is_admin']))
        conn.commit()
        return jsonify({'message': 'User created successfully!'}), 201
    except DatabaseError as e:
        if conn:
            conn.rollback()
        print(e)
        error_code = e.args[0]
        if error_code == 1205: 
            return jsonify({'error': 'Lock wait timeout exceeded. Please try again later.'}), 500
        else:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback() 
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()
# Create Ticket
@app.route('/tickets/create', methods=['POST'])
def create_ticket():
    data = request.json
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO Tickets (ticket_id, event_title, ticket_price, fee, total_price, quantity, full_section, section, row_num) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (data["ticket_id"], data["event_title"], data["ticket_price"], data["fee"], data["total_price"], data["quantity"], data["full_section"], data["section"], data["row_num"]))
        conn.commit()
        return jsonify({'message': 'Ticket created successfully!'}), 201
    except DatabaseError as e:
        if conn:
            conn.rollback()
        print(e)
        error_code = e.args[0]
        if error_code == 1205: 
            return jsonify({'error': 'Lock wait timeout exceeded. Please try again later.'}), 500
        else:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback() 
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

# Create Event
@app.route('/events/create', methods=['POST'])
def create_event():
    data = request.json
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO Events (event_title, event_url, datetime_local, location_name, promoter_name)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (data["event_title"], data["event_url"], data["datetime_local"], data["location_name"], data["promoter_name"]))
        conn.commit()
        return jsonify({'message': 'Events created successfully!'}), 201
    except DatabaseError as e:
        if conn:
            conn.rollback()  # Instantly remove locks by rolling back the transaction
        print(e)
        error_code = e.args[0]
        if error_code == 1205:  # Lock wait timeout exceeded
            return jsonify({'error': 'Lock wait timeout exceeded. Please try again later.'}), 500
        else:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback()  # Ensure rollback for any unexpected error
        print(e)
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

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
    cursor.execute("SELECT * FROM Events LIMIT 10")
    records = cursor.fetchall()
    conn.close()
    return jsonify(records)

# Update User
@app.route('/users/update/<old_username>', methods=['PUT'])
def update_user(old_username):
    print(request.json)
    conn = None
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = hash_password(data['password']) if 'password' in data else None
        query = "UPDATE Users SET username = %s, name = %s, password = %s, is_admin = %s WHERE username = %s"
        cursor.execute(query, (data['new_username'], data['name'], hashed_password, data['is_admin'], old_username))
        conn.commit()
        return jsonify({'message': 'User updated successfully!'})
    except DatabaseError as e:
        if conn:
            conn.rollback()
        print(e)
        error_code = e.args[0]
        if error_code == 1205: 
            return jsonify({'error': 'Lock wait timeout exceeded. Please try again later.'}), 500
        else:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback() 
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()
# Update Ticket
@app.route('/tickets/update/<ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    conn = None
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # ticket_id, event_title, ticket_price, fee, total_price, quantity, full_section, section, row_num
        query = "UPDATE Tickets SET event_title = %s, ticket_price = %s, fee = %s, total_price = %s, quantity = %s, full_section = %s, section = %s, row_num = %s WHERE ticket_id = %s"
        cursor.execute(query, (data['event_title'], data['ticket_price'], data['fee'], data['total_price'], data['quantity'], data['full_section'], data['section'], data['row_num'], data["ticket_id"]))
        conn.commit()
        return jsonify({'message': 'Ticket updated successfully!'})
    except DatabaseError as e:
        if conn:
            conn.rollback()
        print(e)
        error_code = e.args[0]
        if error_code == 1205: 
            return jsonify({'error': 'Lock wait timeout exceeded. Please try again later.'}), 500
        else:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback() 
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

# Update Events
@app.route('/events/update/<old_event_title>', methods=['PUT'])
def update_event(old_event_title):
    conn = None
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # event_title, event_url, datetime_local, location_name, promoter_name
        query = "UPDATE Events SET event_title = %s, event_url = %s, datetime_local = %s, location_name = %s, promoter_name = %s WHERE event_title = %s"
        cursor.execute(query, (data['event_title'], data['event_url'], data['datetime_local'], data['location_name'], data['promoter_name'], old_event_title))
        conn.commit()
        return jsonify({'message': 'Event updated successfully!'})
    except DatabaseError as e:
        if conn:
            conn.rollback()
        print(e)
        error_code = e.args[0]
        if error_code == 1205: 
            return jsonify({'error': 'Lock wait timeout exceeded. Please try again later.'}), 500
        else:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback() 
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

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

    try:
        # Set isolation level
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")

        # Start transaction
        conn.start_transaction()
        

        # Insert the new wishlist entry
        cursor.execute("""
                    INSERT INTO Notifications (username, event_title, message)
                    SELECT 
                        w.username,
                        e.event_title,
                        CONCAT('The event "', e.event_title,
                            ' at ', l.location_name, ' (', l.city, ', ', l.state, ') ',
                            'has been cancelled. ',
                            'There are ', other_events.event_count, ' other events happening in ', l.city, '. ',
                            'Check them out!') AS message
                    FROM WishList w
                    JOIN Events e ON w.event_title = e.event_title
                    JOIN Locations l ON e.location_name = l.location_name
                    JOIN (
                        SELECT city, COUNT(*) as event_count
                        FROM Events natural join Locations
                        WHERE event_title != %s
                        GROUP BY city
                    ) other_events ON l.city = other_events.city
                    WHERE e.event_title = %s;
        """, (event_title, event_title))

        # Insert notification
        cursor.execute("""
                    DELETE FROM Events
                    WHERE event_title = %s;
        """, (event_title,))

        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'Event deleted successfully!'}), 200
    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

# ----------------------------------------------------------------------------------
@app.route('/events')
def view_events():
    """Display a list of events for end-users."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT event_title, datetime_local, location_name, promoter_name, city FROM Events natural join Locations LIMIT 150")
        events = cursor.fetchall()
        return jsonify(events)
    except Exception as e:
        print(e)
        return jsonify({'error': f'An error occurred while fetching events: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/events-page')
def events_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('events.html', username=session['user'], check_notifications=True)

# Not Used
@app.route('/tickets')
def view_tickets():
    """Display a list of tickets for end-users."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT ticket_id, event_title, ticket_price, total_price, quantity, section, row_num FROM Tickets LIMIT 15")
        tickets = cursor.fetchall()
        return render_template('tickets.html', tickets=tickets)
    except Exception as e:
        print(e)
        return jsonify({'error': f'An error occurred while fetching tickets: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/tickets/<event_title>')
def view_tickets_by_title(event_title):
    """Display a list of tickets for a given event title."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT distinct t.section, t.row_num, t.quantity, t.total_price
        FROM Tickets t
        WHERE t.event_title = %s
        """
        cursor.execute(query, (event_title,))
        tickets = cursor.fetchall()
        if not tickets:
            return jsonify({'message': f'No tickets found for event: {event_title}'}), 404
        return jsonify(tickets)
    except Exception as e:
        print(e)
        return jsonify({'error': f'An error occurred while fetching tickets: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/tickets-page/<event_title>')
def tickets_page(event_title):
    """Serve the tickets.html page for a specific event."""
    return render_template('tickets.html', event_title=event_title)

#Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page logic."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="Please enter both username and password.")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT username, password, is_admin FROM Users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()

            if user and user['password'] == hash_password(password):
                session['user'] = user['username']
                session['is_admin'] = user['is_admin']
                if user['is_admin'] == 1:
                    return redirect('/admin')
                else:
                    return redirect('/events-page')
            else:
                return render_template('login.html', error="Invalid username or password.")
        except Exception as e:
            print(e)
            return render_template('login.html', error="An error occurred. Please try again.")
        finally:
            conn.close()

    return render_template('login.html')

#Logout
@app.route('/logout')
def logout():
    """Log the user out."""
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/wishlist-page')
def wishlist_page():
    """Render the wishlist page."""
    if 'user' not in session:
        return redirect('/login')  # Redirect to login if the user is not logged in

    return render_template('wishlist.html', username=session['user'])

@app.route('/wishlist', methods=['POST'])
def add_to_wishlist():
    """Add an event to the wishlist."""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401

    username = session['user']
    event_title = request.json.get('event_title')

    if not event_title:
        return jsonify({'error': 'Event title is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        wishlist_date = datetime.now()
        
        # Set isolation level
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")

        # Start transaction
        conn.start_transaction()
        

        # Insert the new wishlist entry
        cursor.execute("""
            INSERT INTO WishList (username, event_title, wishlist_date)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE wishlist_date = VALUES(wishlist_date)
        """, (username, event_title, wishlist_date))

        # Insert notification
        cursor.execute("""
            INSERT INTO Notifications (username, event_title, message)
            SELECT 
                %s,
                e.event_title,
                CONCAT('You have added "', e.event_title, '" to your wishlist. ',
                    ' at ', e.location_name, ' (', l.city, ', ', l.state, '). ',
                    'Promoted by ', e.promoter_name, '. ',
                    'Currently, ', COUNT(w.username), ' user(s) have wishlisted this event, ',
                    'including you. ')
            FROM Events e
            JOIN Locations l ON e.location_name = l.location_name
            LEFT JOIN WishList w ON e.event_title = w.event_title
            WHERE e.event_title = %s
            GROUP BY e.event_title, e.location_name, l.city, l.state, e.promoter_name
        """, (username, event_title))

        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'Event added to wishlist successfully'}), 200
    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/wishlist', methods=['GET'])
def fetch_wishlist():
    """Fetch wishlist for the logged-in user."""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401

    username = session['user']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT W.event_title, E.datetime_local, E.location_name, E.promoter_name
            FROM WishList W
            JOIN Events E ON W.event_title = E.event_title
            WHERE W.username = %s
            """,
            (username,)
        )
        wishlist_events = cursor.fetchall()
        return jsonify(wishlist_events), 200
    except Exception as e:
        print(e)
        return jsonify({'error': f'Error fetching wishlist: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/wishlist', methods=['DELETE'])
def remove_from_wishlist():
    """Remove an event from the wishlist."""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401

    username = session['user']
    event_title = request.json.get('event_title')

    if not event_title:
        return jsonify({'error': 'Event title is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM WishList
            WHERE username = %s AND event_title = %s
            """,
            (username, event_title)
        )
        conn.commit()
        return jsonify({'message': f'Event "{event_title}" removed from wishlist successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': f'Error removing event: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/popular-events')
def get_popular_events():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("CALL GetPopularEvents(10)")
        popular_events = cursor.fetchall()
        return jsonify(popular_events)
    except Exception as e:
        print(e)
        return jsonify({'error': f'An error occurred while fetching popular events: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/top-cities-events')
def top_cities_events():
    """Fetch events happening in the top 5 major cities."""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Query events happening in the top 5 major cities
        query = """
            call GetTopCitiesEvents(10);
            """
        cursor.execute(query)
        events = cursor.fetchall()
        return jsonify(events)
    except Exception as e:
        print(e)
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/filtered-events')
def filtered_events():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    query = request.args.get('query', '').lower()
    city = request.args.get('city', 'all')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    tab = request.args.get('tab', 'all')
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if tab == 'popular':
            cursor.execute("CALL GetPopularEvents(10)")
            events = cursor.fetchall()
        else:
            sql_query = """
            SELECT event_title, datetime_local, location_name, promoter_name, city 
            FROM Events 
            NATURAL JOIN Locations 
            WHERE LOWER(event_title) LIKE %s
            """
            params = [f'%{query}%']
            if city != 'all':
                sql_query += " AND city = %s"
                params.append(city)
            
            if start_date:
                sql_query += " AND datetime_local >= %s"
                params.append(start_date)
            
            if end_date:
                sql_query += " AND datetime_local <= %s"
                params.append(end_date)
            
            if tab == 'major':
                sql_query += """ AND city in ( Select city from 
                    (select city, count(event_title) from Locations natural join Events group by city order by 2 desc limit 5) z
                    )"""
            
            sql_query += " LIMIT 150"
            
            cursor.execute(sql_query, tuple(params))
            events = cursor.fetchall()
        
        # Apply client-side filtering for the popular tab
        if tab == 'popular':
            events = [event for event in events if
                      (city == 'all' or event['city'] == city) and
                      (not start_date or str(event['datetime_local']) >= start_date) and
                      (not end_date or str(event['datetime_local']) <= end_date) and
                      query in event['event_title'].lower()]
        
        return jsonify(events)
    except Exception as e:
        print(e)
        return jsonify({'error': f'An error occurred while fetching events: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/get_notifications')
def get_notifications():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    username = session['user']
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch unread notifications
        cursor.execute("""
            SELECT notification_id, message FROM Notifications 
            WHERE username = %s AND is_read = 0
        """, (username,))
        notifications = cursor.fetchall()
        
        # Mark notifications as read
        if notifications:
            cursor.execute("""
                UPDATE Notifications 
                SET is_read = 1 
                WHERE username = %s AND is_read = 0
            """, (username,))
            conn.commit()
        
        return jsonify(notifications)
    except Exception as e:
        print(e)
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()


