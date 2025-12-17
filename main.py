from flask import Flask, render_template, request, redirect, url_for, session
from datetime import date
from flask_mysqldb import MySQL
import yaml
import os

app = Flask(__name__)
app.secret_key = "super secret key"
userID = None


'''
app.config['MYSQL_HOST']= os.environ.get('CLOUD_SQL_CONNECTION_NAME')
app.config['MYSQL_USER']= 'root'  #os.environ.get('CLOUD_SQL_USERNAME')
app.config['MYSQL_PASSWORD']= '' #os.environ.get('CLOUD_SQL_PASSWORD')
app.config['MYSQL_DB']= 'ubreservation' #os.environ.get('CLOUD_SQL_DATABASE_NAME')
'''

with open('db.yaml', 'r') as f:
    db = yaml.safe_load(f)

app.config['MYSQL_HOST']= db['mysql_host']
app.config['MYSQL_USER']= db['mysql_user']
app.config['MYSQL_PASSWORD']= db['mysql_password']
app.config['MYSQL_DB']= db['mysql_db']


mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html', username=session.get('username', ''), logout = False)


@app.route('/signup', methods=['GET'])
def signup_form():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    # Get form data
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    userType = request.form['userType']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    phone = request.form['phone']
    address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    zipCode = request.form['zipCode']

    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Email: {email}")
    print(f"User Type: {userType}")
    print(f"First Name: {firstName}")
    print(f"Last Name: {lastName}")
    print(f"Phone: {phone}")
    print(f"Address: {address}")
    print(f"City: {city}")
    print(f"State: {state}")
    print(f"Zip Code: {zipCode}")
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO user (username, password, email, userType, firstName, lastName, phone, address, city, state, zipCode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (username, password, email, userType, firstName, lastName, phone, address, city, state, zipCode))
    mysql.connection.commit()
    userID = cur.lastrowid
    cur.close()
    print(str(userID) + " this is the user id that we got ok")

    # Redirect to a success page or another route
    if userType == 'Admin':
        return redirect(url_for('admin_signup', userID=userID))
    else: 
        return redirect('/signup_success')

@app.route('/signup_success')
def success():
    return f'<h1>Sign Up Successful! <a href="{url_for("home")}">click here</a> to go home</h1>'

@app.route('/admin_signup', methods=['GET'])
def admin_signup_form():
    userID = request.args.get('userID')
    return render_template('admin_signup.html', userID=userID)

@app.route('/admin_signup', methods=['POST'])
def admin_signup():
    # Get form data for admin signup
    userID = request.form['userID']
    accessLevel = request.form['accessLevel']
    department = request.form['department']
    hireDate = request.form['hireDate']
    lastLoginDate = request.form['lastLoginDate']
    profilePicture = request.form['profilePicture']
    contactPreference = request.form['contactPreference']
    role = request.form['role']
    activeStatus = request.form['activeStatus']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO admin (userID, accessLevel, department, hireDate, lastLoginDate, profilePicture, contactPreference, role, activeStatus) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (userID, accessLevel, department, hireDate, lastLoginDate, profilePicture, contactPreference, role, activeStatus))
    mysql.connection.commit()
    cur.close()

    # Process admin signup data here

    return f'<h1>Sign Up Successful! <a href="{url_for("home")}">click here</a> to go home</h1>'

@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    # Get form data
    userType = request.form['userType']
    username = request.form['username']
    password = request.form['password']

    # Add your login logic here (e.g., check username/password against database)
    cur = mysql.connection.cursor()
    cur.execute("Select username, password, userType, userID from user where username=%s and password=%s and userType=%s", (username, password, userType))
    user = cur.fetchone()
    cur.close()

    if user: 
        session['username'] = user[0]
        session['loggedin'] = True
        session['user_id'] = user[3]
        session['userType'] = user[2]

        if userType == 'Admin':
            today_date = str(date.today())
            cur = mysql.connection.cursor()
            try:
                cur.execute("UPDATE admin SET LastLoginDate = %s WHERE UserID = %s", (today_date, user[3]))
                mysql.connection.commit()  # Commit changes to the database
                print("Admin LastLoginDate updated successfully.")
            except Exception as e:
                print("Error updating admin LastLoginDate:", e)
            finally:
                cur.close()  # Close the cursor

        return redirect(url_for('home'))
    else: 
        return render_template('login.html', error = 'invalid user name or password.. Try again!')


    # For demo purposes, let's just print the user type, username, and redirect to success page
    print(f"User Type: {userType}")
    print(f"Username: {username}")

    # Redirect to the success page
    return redirect('/success')


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('userType', None)
    userID = None
    return render_template('index.html', username=session.get('username', ''), logout = True)


@app.route('/about/<username>')
def about(username):
    if session['userType'] == 'Admin':
        cur = mysql.connection.cursor()
        cur.execute("select A.username, A.email, A.firstname, A.phone, count(B.userid) reservation_count from user A inner join reservation B on A.userid = B.userid group by B.userid having username =%s", (username,))
        aboutuser = cur.fetchone()
        cur.close()
        return render_template('about.html', user=aboutuser)
    return "you are not authorised."



@app.route('/room_details', methods=['GET', 'POST'])
def room_details():
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Room")  # Fetch all room details
        rooms_data = cur.fetchall()
        cur.close()
        #print(rooms_data)
        return render_template('room_details.html', rooms=rooms_data)
    
    
    
@app.route('/book_room', methods=['GET', 'POST'])
def book_room():
    if request.method == 'GET':
        return redirect(url_for('room_details'))
    roomID = request.form['room_id']
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        return render_template('reservation.html', selected_room_id=roomID)


@app.route('/create_reservation', methods=['POST'])
def create_reservation():
    # Retrieve form data

    user_id = session['user_id']
    room_id = request.form['room_id']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    purpose = request.form['purpose']
    attendees = request.form['attendees']
    equipment = request.form['equipment']
    notes = request.form['notes']


    cur = mysql.connection.cursor()
    cur.execute("""
        select date, description, type, observance from holiday where Date=%s 
        """, (start_date,))
    holiday = cur.fetchone()
    cur.close()
    if holiday:
        return render_template('holiday.html', holidays=holiday)

    # Insert reservation into database
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO Reservation (UserID, RoomID, Date, StartTime, EndTime, Purpose, Attendees, Equipment, Notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, room_id, start_date, start_time, end_time, purpose, attendees, equipment, notes))
    mysql.connection.commit()
    cur.close()
    print(user_id," ", room_id, " ", start_date, " ",end_date, " ",start_time, " ",end_time, " ",purpose, " ",attendees, " ",equipment, " ",notes)

    return redirect(url_for('home'))


@app.route('/my_reservations', methods=['GET', 'POST'])
def my_reservations():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT A.ReservationID, A.Date, A.StartTime, A.Status, CheckInTime, CheckOutTime FROM Reservation A left outer join Attendance B on A.ReservationID = B.ReservationID WHERE A.UserID = %s", (session['user_id'],))
        reservations = cur.fetchall()
        cur.close()

        return render_template('my_reservations.html', reservations=reservations)
    

    if request.method == 'POST':
        checkinout = request.form['status']
        reservation_id = request.form['reservation_id']
        if checkinout == 'Checkin':
            cur = mysql.connection.cursor()
            cur.execute("Update Attendance set CheckInTime=now() WHERE ReservationID = %s", (reservation_id,))
            cur.execute("UPDATE reservation SET Status = %s WHERE ReservationID = %s", ('Checked-In', reservation_id))
            mysql.connection.commit()
            cur.close()
        elif checkinout == 'Checkout':
            cur = mysql.connection.cursor()
            cur.execute("Update Attendance set CheckOutTime=now() WHERE ReservationID = %s", (reservation_id,))
            cur.execute("UPDATE reservation SET Status = %s WHERE ReservationID = %s", ('Completed', reservation_id))
            mysql.connection.commit()
            cur.close()
        return redirect(url_for('my_reservations'))

@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if session['userType'] == 'Admin' and request.method== 'GET':
        cur = mysql.connection.cursor()
        cur.execute("""SELECT A.ReservationID, B.Username, B.Email as User_Email, A.Date, A.StartTime, A.Status, A.Notes, 
                    IF(C.CheckInTime is NULL, 'NA',C.CheckInTime) as CheckInTime , IF(C.CheckOutTime is NULL, 'NA',C.CheckOutTime) as CheckOutTime 
                    FROM Reservation A inner join user B on A.UserID = B.UserID left outer join Attendance C on A.ReservationID = C.ReservationID""")
        reservations = cur.fetchall()
        cur.close()
        return render_template('reservations.html', reservations=reservations)
    if request.method == 'POST':
        reservationID = request.form['reservation_id']
        status = request.form['status']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE reservation SET Status = %s WHERE ReservationID = %s", (status, reservationID))
        mysql.connection.commit()
        if status=='Confirmed':
            cur.execute("INSERT INTO Attendance (ReservationID, UserID) VALUES (%s, %s)", (reservationID,session['user_id']))
        elif status=='Cancelled':
            #print(reservationID, 'this is delete test')
            cur.execute("delete from Attendance where ReservationID=%s", (reservationID,))
        mysql.connection.commit()
        print('status updated successfully')
        cur.close()
        print(reservationID, status)
        return redirect(url_for('reservations'))

@app.route('/feedback')
def feedback():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Feedback")
    feedbacks = cur.fetchall()
    cur.close()
    return render_template('feedback.html', feedbacks=feedbacks)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080,debug=True)
