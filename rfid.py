import tkinter as tk
import serial
import threading
import queue
from datetime import datetime
from PIL import Image, ImageTk
import mysql.connector
import os

################################### Data base connect ###############################################
def connect_to_database():
    try:
        db_connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="rfid_project"
        )
        db_cursor = db_connection.cursor()
        return db_connection, db_cursor
    except mysql.connector.Error as e: # If Database is not detected 
        print(f"Error connecting to MySQL database: {e}")
        return None, None

########################### Disconnect (For refresh)########################################### 
def disconnect_from_database(connection, cursor):
    if cursor:
        cursor.close()
    if connection:
        connection.close()

#######################################RFID READ###############################################
def read_from_port(port, rfid_queue):
    try: #attempt to connect to arduino 
        arduino = serial.Serial(port, 9600)
        print(f"Connected to Arduino on port {port}")
    except serial.SerialException as e: #On fail display which port 
        print(f"Failed to connect to Arduino on port {port}: {e}")
        return

    def update_display():
        while True:
            data = arduino.readline().strip().decode()
            if data:
                rfid_queue.put((port, data))
                print(f"[{port}] {data}")  # Print to terminal

                # Check access when RFID code is received
                check_access(arduino, data)

    thread = threading.Thread(target=update_display)
    thread.daemon = True
    thread.start()

def process_rfid(rfid_queue, text_widget):
    while True:
        if not rfid_queue.empty():
            port, data = rfid_queue.get()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"[{timestamp}] [{port}] {data}\n"
            if text_widget and text_widget.winfo_exists():
                text_widget.insert(tk.END, message)
                text_widget.see(tk.END)
            rfid_queue.task_done()

def del_user_from_database():
    """
    Delete a user from the database.
    """
    root = tk.Tk()
    root.title("Delete User")
    root.geometry("400x400")
    root.resizable(False, False)
    root.config(bg="#57738b")

    # RFID label and entry widget
    rfid_label = tk.Label(root, text="RFID:", font=("Arial", 12), bg="#57738b", fg="white")
    rfid_label.pack(pady=(20, 5))
    rfid_entry = tk.Entry(root, font=("Arial", 12))
    rfid_entry.pack()

    db_connection, db_cursor = connect_to_database()   
    # Function to display error messages
    def display_error_message(message):
        error_label.config(text=message)
    # Function to clear error message
    def clear_error_message():
        error_label.config(text="")

    # Display search results
    search_results_text = tk.Text(root, height=10, width=50)
    search_results_text.pack(pady=10)

    def search_user():
        """
        Search for the user in the database.
        """
        # Clear previous search results
        search_results_text.delete("1.0", tk.END)

        # Get RFID from entry widget
        rfid = rfid_entry.get()

        if not rfid:
            display_error_message("ERROR: RFID is missing.")
            return

        # Search for user in the database
        query = f"SELECT * FROM users WHERE rfid = '{rfid}'"
        db_cursor.execute(query)
        user = db_cursor.fetchone()

        if user:
            # Display user information
            user_info = f"UserID: {user[1]}\nFirst Name: {user[2]}\nLast Name: {user[3]}\nSecurity Level: {user[4]}\nDescription: {user[5]}"
            search_results_text.insert(tk.END, user_info)
            clear_error_message()
        else:
            display_error_message("ERROR: User not found.")

    # Search button
    search_button = tk.Button(root, text="Search", command=search_user, bg="#FF5733", fg="white",
                              font=("Arial", 12, "bold"))
    search_button.pack(pady=5)

    error_label = tk.Label(root, text="", font=("Arial", 12), bg="#57738b", fg="red")
    error_label.pack()

    def confirm_delete():
        """
        Confirm and delete the user from the database.
        """
        # Get RFID from entry widget
        rfid = rfid_entry.get()

        if not rfid:
            display_error_message("ERROR: RFID is missing.")
            return

        # Search for user in the database
        query = f"SELECT * FROM users WHERE rfid = '{rfid}'"
        db_cursor.execute(query)
        user = db_cursor.fetchone()

        if user:
                # Delete user from the database
                delete_query = f"DELETE FROM users WHERE rfid = '{rfid}'"
                db_cursor.execute(delete_query)
                db_connection.commit()
                display_error_message("Success , User deleted successfully.")
        else:
            display_error_message("ERROR: User not found.")

    # Confirm delete button
    confirm_delete_button = tk.Button(root, text="Confirm Delete", command=confirm_delete, bg="#FF5733", fg="white",
                                      font=("Arial", 12, "bold"))
    confirm_delete_button.pack(pady=5)

    root.mainloop()

def edit_user_in_database():
    """
    Edit user information in the database.
    """
    root = tk.Tk()
    root.title("Edit User")
    root.geometry("400x800")
    root.resizable(False, False)
    root.config(bg="#57738b")

    # RFID label and entry widget
    rfid_label = tk.Label(root, text="RFID:", font=("Arial", 12), bg="#57738b", fg="white")
    rfid_label.pack(pady=(20, 5))
    rfid_entry = tk.Entry(root, font=("Arial", 12))
    rfid_entry.pack()

    db_connection, db_cursor = connect_to_database() 

    # Display user information
    error_label = tk.Label(root, text="", font=("Arial", 12), bg="#57738b", fg="red")
    error_label.pack()

    user_info_text = tk.Text(root, height=10, width=50)
    user_info_text.pack(pady=10)

    def display_error_message(message):
        error_label.config(text=message)

    def clear_error_message():
        error_label.config(text="")

    # Function to display user information based on RFID
    def display_user_info():
        """
        Display user information based on RFID.
        """
        # Clear previous user information
        user_info_text.delete("1.0", tk.END)

        # Get RFID from entry widget
        rfid = rfid_entry.get()

        if not rfid:
            display_error_message("ERROR: RFID is missing.")
            return

        # Search for user in the database
        query = f"SELECT * FROM users WHERE rfid = '{rfid}'"
        db_cursor.execute(query)
        user = db_cursor.fetchone()

        if user:
            # Display user information
            user_info = f"UserID: {user[1]}\nFirst Name: {user[2]}\nLast Name: {user[3]}\nSecurity Level: {user[4]}\nDescription: {user[5]}"
            user_info_text.insert(tk.END, user_info)
            clear_error_message()
        else:
            display_error_message("ERROR: User not found.")

    # Search button
    search_button = tk.Button(root, text="Search", command=display_user_info, bg="#FF5733", fg="white",
                              font=("Arial", 12, "bold"))
    search_button.pack(pady=5)

    # Function to update user information in the database
    def update_user_info():
        """
        Update user information in the database.
        """
        # Get RFID from entry widget
        rfid = rfid_entry.get()

        if not rfid:
            display_error_message("ERROR: RFID is missing.")
            return

        # Search for user in the database
        query = f"SELECT * FROM users WHERE rfid = '{rfid}'"
        db_cursor.execute(query)
        user = db_cursor.fetchone()

        if user:
            # Get updated information from entry widgets
            userid = user[1]
            fname = fname_entry.get()
            lname = lname_entry.get()
            security_level = security_level_entry.get()
            description = description_entry.get()

            # Prepare updates list
            updates = []

            # Check if fields are different
            if fname != user[2]:
                updates.append(f"fname = '{fname}'" if fname else "fname = NULL")
            if lname != user[3]:
                updates.append(f"lname = '{lname}'" if lname else "lname = NULL")
            if security_level != user[4]:
                updates.append(f"security_level = '{security_level}'" if security_level else "security_level = NULL")
            if description != user[5]:
                updates.append(f"description = '{description}'" if description else "description = NULL")

            # Update user information in the database
            if updates:
                update_query = f"UPDATE users SET {', '.join(updates)} WHERE rfid = '{rfid}'"
                try:
                    db_cursor.execute(update_query)
                    db_connection.commit()
                    display_error_message("Success, User information updated successfully.")
                    clear_error_message()
                except mysql.connector.Error as e:
                    display_error_message(f"ERROR: {e}")
            else:
                display_error_message("No changes detected.")
        else:
            display_error_message("ERROR: User not found.")

    # First Name label and entry widget
    fname_label = tk.Label(root, text="First Name:", font=("Arial", 12), bg="#57738b", fg="white")
    fname_label.pack(pady=(10, 5))
    fname_entry = tk.Entry(root, font=("Arial", 12))
    fname_entry.pack()

    # Last Name label and entry widget
    lname_label = tk.Label(root, text="Last Name:", font=("Arial", 12), bg="#57738b", fg="white")
    lname_label.pack(pady=(10, 5))
    lname_entry = tk.Entry(root, font=("Arial", 12))
    lname_entry.pack()

    # Security Level label and entry widget
    security_level_label = tk.Label(root, text="Security Level:", font=("Arial", 12), bg="#57738b", fg="white")
    security_level_label.pack(pady=(10, 5))
    security_level_entry = tk.Entry(root, font=("Arial", 12))
    security_level_entry.pack()

    # Description label and entry widget
    description_label = tk.Label(root, text="Description:", font=("Arial", 12), bg="#57738b", fg="white")
    description_label.pack(pady=(10, 5))
    description_entry = tk.Entry(root, font=("Arial", 12))
    description_entry.pack()

    # Update button
    update_button = tk.Button(root, text="Update", command=update_user_info, bg="#FF5733", fg="white",
                              font=("Arial", 12, "bold"))
    update_button.pack(pady=10)

    root.mainloop()
def add_user():
    """
    Add a new user to the database.
    """
    db_connection, db_cursor = connect_to_database()
    root = tk.Tk()
    selected_option = None
    root.title("Add User Menu")
    root.geometry("600x600")  # Set window size
    root.resizable(False, False)  # Lock the window size
    # Change background color to cyan
    root.config(bg="#57738b")

    db_connection, db_cursor = connect_to_database()   
    # Function to display error messages
    def display_error_message(message):
        error_label.config(text=message)
    # Function to clear error message
    def clear_error_message():
        error_label.config(text="")

    # Create a new window for adding a user
    # Username label and entry widget
    username_label = tk.Label(root, text="RFID:", font=("Arial", 12), bg="#57738b", fg="white")
    username_label.pack(pady=(0, 5))
    username_entry = tk.Entry(root, font=("Arial", 12))
    username_entry.pack()

    # User ID label and entry widget
    userid_label = tk.Label(root, text="UserID:", font=("Arial", 12), bg="#57738b", fg="white")
    userid_label.pack(pady=(10, 5))
    userid_entry = tk.Entry(root, font=("Arial", 12))
    userid_entry.pack()

    # First name label and entry widget
    fname_label = tk.Label(root, text="First Name :", font=("Arial", 12), bg="#57738b", fg="white")
    fname_label.pack(pady=(10, 5))
    fname_entry = tk.Entry(root, font=("Arial", 12))
    fname_entry.pack()

    # Last name label and entry widget
    lname_label = tk.Label(root, text="Last Name :", font=("Arial", 12), bg="#57738b", fg="white")
    lname_label.pack(pady=(10, 5))
    lname_entry = tk.Entry(root, font=("Arial", 12))
    lname_entry.pack()

    # Security level label and entry widget
    security_level_label = tk.Label(root, text="Security Level :", font=("Arial", 12), bg="#57738b", fg="white")
    security_level_label.pack(pady=(10, 5))
    security_level_entry = tk.Entry(root, font=("Arial", 12))
    security_level_entry.pack()

    # Description label and entry widget
    description_level_label = tk.Label(root, text="Description:", font=("Arial", 12), bg="#57738b", fg="white")
    description_level_label.pack(pady=(10, 5))
    description_level_entry = tk.Entry(root, font=("Arial", 12))
    description_level_entry.pack()

    # Error message label
    error_label = tk.Label(root, text="", font=("Arial", 12), bg="#57738b", fg="red")
    error_label.pack(pady=(10, 5))

    def add_user_to_database():
        """
        Add the new user to the database.
        """
        # Get user information from entry widgets
        rfid = username_entry.get()
        userid = userid_entry.get()
        fname = fname_entry.get()
        lname = lname_entry.get()
        security_level = security_level_entry.get()
        description = description_level_entry.get()

        # Check if UserID is empty
        if not userid:
            display_error_message("ERROR: User ID is missing.")
            return

        # Convert empty fields to NULL
        rfid = f"'{rfid}'" if rfid else "NULL"
        fname = f"'{fname}'" if fname else "NULL"
        lname = f"'{lname}'" if lname else "NULL"
        security_level = f"'{security_level}'" if security_level else "NULL"
        description = f"'{description}'" if description else "NULL"

        # Add user to the database
        query = f"INSERT INTO users (rfid, userid, fname, lname, security_level, description) VALUES ({rfid}, '{userid}', {fname}, {lname}, {security_level}, {description})"
        try:
            db_cursor.execute(query)
            db_connection.commit()
            clear_error_message()
        except mysql.connector.Error as e:
            display_error_message(f"ERROR: {e}")


    # Add user button
    add_user_button = tk.Button(root, text="Add User", command=add_user_to_database, bg="#FF5733", fg="white",
                                font=("Arial", 12, "bold"))
    add_user_button.pack(pady=10)

    root.mainloop()

def rfid_viewing(rfid_queue, main_root):
    root = tk.Toplevel(main_root)  # Create a Toplevel window for the RFID viewing
    root.title("RFID Scan Data")

    text = tk.Text(root)
    text.pack(fill=tk.BOTH, expand=True)

    processing_thread = threading.Thread(target=process_rfid, args=(rfid_queue, text))
    processing_thread.daemon = True
    processing_thread.start()

    def close_window():
        root.destroy()  # Close the window without quitting the application

    exit_button = tk.Button(root, text="Close Window", command=close_window)
    exit_button.pack(side=tk.BOTTOM)

def user_config_menu():
    root = tk.Tk()
    selected_option = None
    root.title("RFID User Menu")
    root.geometry("600x300")  # Set window size
    root.resizable(False, False)  # Lock the window size
    # Change background color to cyan
    root.config(bg="#57738b")

    def view_user_table():
        nonlocal selected_option
        selected_option = "View User Table"
        # Connect to database
        db_connection, db_cursor = connect_to_database()
        display_user_table(root, db_cursor, db_connection, "users", "User Table")

    def add_users():
        nonlocal selected_option
        selected_option = "Add User"
        add_user()

    def edit_user():
        nonlocal selected_option
        selected_option = "Edit User"
        edit_user_in_database()

    def remove_user():
        nonlocal selected_option
        selected_option = "Remove User"
        del_user_from_database()

    user_table_button = tk.Button(root, text="View User Table", command=view_user_table, bg="#FF5733", fg="white",
                                  font=("Arial", 12, "bold"), width=25, pady=5)
    user_table_button.pack(pady=(40, 5))  # Add some space above the button

    user_table_button = tk.Button(root, text="Add User", command=add_users, bg="#FF5733", fg="white",
                                  font=("Arial", 12, "bold"), width=25, pady=5)
    user_table_button.pack(pady=5)

    user_table_button = tk.Button(root, text="Edit User", command=edit_user, bg="#FF5733", fg="white",
                                  font=("Arial", 12, "bold"), width=25, pady=5)
    user_table_button.pack(pady=5)

    user_table_button = tk.Button(root, text="Remove User", command=remove_user, bg="#FF5733", fg="white",
                                  font=("Arial", 12, "bold"), width=25, pady=5)
    user_table_button.pack(pady=5)

    root.mainloop()

def monitor_option_selected(rfid_queue, main_root):
    # Open RFID viewing window
    rfid_viewing(rfid_queue, main_root)

def check_access(arduino, scanned_line):
    # Extract room ID and RFID code from the scanned line
    try:
        room_id, rfid_code = scanned_line.split(None, 1)
    except ValueError:
        print("Invalid scanned line format")
        return

    # Connect to database
    db_connection, db_cursor = connect_to_database()

    if db_cursor and db_connection:
        # Fetch user security level from the database
        query = f"SELECT security_level FROM users WHERE rfid = '{rfid_code.strip()}'"
        db_cursor.execute(query)
        user_security_level = db_cursor.fetchone()

        if user_security_level:
            user_security_level = user_security_level[0]

            # Fetch room security level from the database
            query = f"SELECT security_level FROM access_points WHERE room_id = '{room_id}'"
            db_cursor.execute(query)
            room_security_level = db_cursor.fetchone()

            if room_security_level:
                room_security_level = room_security_level[0]

                # Compare user's security level with room's security level
                if user_security_level >= room_security_level:
                    print(f"User {rfid_code} with security level {user_security_level} successfully accessed {room_id} with a security level of {room_security_level}")
                    # Send response to Arduino (1)
                    arduino_response = '1'
                    add_to_access_granted_table(db_cursor, db_connection, rfid_code, room_id)
                else:
                    print(f"User {rfid_code} with security level {user_security_level} not accessed {room_id} with a security level of {room_security_level}")
                    # Send response to Arduino (0)
                    arduino_response = '0'
                    add_to_access_denied_table(db_cursor, db_connection, rfid_code, room_id)
            else:
                print(f"Room {room_id} not found")
                arduino_response = '0'
                add_to_access_denied_table(db_cursor, db_connection, rfid_code, room_id)
        else:
            print(f"User {rfid_code} not found")
            arduino_response = '0'
            add_to_access_denied_table(db_cursor, db_connection, rfid_code, room_id)

        # Send response to Arduino
        send_response_to_arduino(arduino, arduino_response)

        # Disconnect from database
        disconnect_from_database(db_connection, db_cursor)

def add_to_access_granted_table(db_cursor, db_connection, rfid_code, room_id):
    """
    Add access granted data to the database.

    Args:
        db_cursor (mysql.connector.cursor.MySQLCursor): Database cursor object.
        db_connection (mysql.connector.connection.MySQLConnection): Database connection object.
        rfid_code (str): RFID code.
        room_id (str): Room ID.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    datestamp = datetime.now().strftime("%Y-%m-%d")
    query = f"INSERT INTO access_granted (rfid, room_id, time, date) VALUES ('{rfid_code}', '{room_id}', '{timestamp}', '{datestamp}')"
    db_cursor.execute(query)
    db_connection.commit()

def add_to_access_denied_table(db_cursor, db_connection, rfid_code, room_id):
    """
    Add access denied data to the database.

    Args:
        db_cursor (mysql.connector.cursor.MySQLCursor): Database cursor object.
        db_connection (mysql.connector.connection.MySQLConnection): Database connection object.
        rfid_code (str): RFID code.
        room_id (str): Room ID.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    datestamp = datetime.now().strftime("%Y-%m-%d")
    query = f"INSERT INTO access_denied (rfid, room_id, time, date) VALUES ('{rfid_code}', '{room_id}', '{timestamp}', '{datestamp}')"
    db_cursor.execute(query)
    db_connection.commit()

def send_response_to_arduino(arduino, response):
    """
    Send response to Arduino.

    Args:
        arduino (serial.Serial): Serial connection to Arduino.
        response (str): Response to send.
    """
    # Send response to Arduino
    # For demonstration purposes, print the response
    print("Response sent to Arduino:", response)
    arduino.write(response.encode('utf-8'))  # Write response to Arduino

def display_user_table(root, db_cursor, db_connection, table_name, title):
    """
    
    """
    if db_cursor and db_connection:
        # Create a new window for displaying user table
        table_window = tk.Toplevel(root)
        table_window.title(title)

        table_frame = tk.Frame(table_window, bg="#57738b")
        table_frame.pack(expand=True, pady=10)

        table_label = tk.Label(table_frame, text=title, font=("Arial", 14, "bold"), bg="#57738b", fg="white")
        table_label.pack()

        # Search frame
        search_frame = tk.Frame(table_window, bg="#57738b")
        search_frame.pack(pady=10)

        search_label = tk.Label(search_frame, text="Search RFID:", font=("Arial", 12), bg="#57738b", fg="white")
        search_label.pack(side=tk.LEFT)

        search_entry = tk.Entry(search_frame, font=("Arial", 12))
        search_entry.pack(side=tk.LEFT)

        def search_users():
            nonlocal db_cursor, db_connection
            # Clear the text widget
            table_text.config(state=tk.NORMAL)
            table_text.delete('1.0', tk.END)

            # Re-establish the database connection and cursor if necessary
            db_connection, db_cursor = connect_to_database()

            if db_cursor and db_connection:
                try:
                    # Fetch the data based on the search text
                    search_text = search_entry.get()
                    query = f"SELECT * FROM {table_name} WHERE rfid LIKE '%{search_text}%'"
                    db_cursor.execute(query)
                    items = db_cursor.fetchall()

                    # Display the search results
                    match table_name:
                        case "users":
                            for item in items:
                                table_text.insert(tk.END,
                                                  f"RFID: {item[0]}\tUID: {item[1]}\tName:: {item[2]} {item[3]}\tSecurity Level {item[4]}\n")
                            table_text.config(state=tk.DISABLED)
                        case "access_denied":
                            for item in items:
                                table_text.insert(tk.END,
                                                  f"RFID: {item[0]}\tAccess Point: {item[1]}\tTime: {item[2]}\tDate: {item[3]}\n")
                            table_text.config(state=tk.DISABLED)
                        case "access_granted":
                            for item in items:
                                table_text.insert(tk.END,
                                                  f"RFID: {item[0]}\tAccess Point: {item[1]}\tTime: {item[2]}\tDate: {item[3]}\n")
                            table_text.config(state=tk.DISABLED)
                except mysql.connector.Error as e:
                    print(f"Error executing query: {e}")
                finally:
                    # Disconnect from database
                    disconnect_from_database(db_connection, db_cursor)
            else:
                print("Database connection not established.")

        search_button = tk.Button(search_frame, text="Search", command=search_users, bg="#FF5733", fg="white",
                                  font=("Arial", 12, "bold"))
        search_button.pack(side=tk.LEFT, padx=5)

        table_scrollbar = tk.Scrollbar(table_frame, orient=tk.VERTICAL)
        table_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        table_text = tk.Text(table_frame, yscrollcommand=table_scrollbar.set, wrap=tk.NONE, height=15)
        table_text.pack(fill=tk.BOTH, expand=True)

        table_scrollbar.config(command=table_text.yview)

        def refresh_table():
            nonlocal db_cursor, db_connection
            # Clear the text widget
            table_text.config(state=tk.NORMAL)
            table_text.delete('1.0', tk.END)

            # Re-establish the database connection and cursor if necessary
            db_connection, db_cursor = connect_to_database()

            if db_cursor and db_connection:
                try:
                    # Fetch the updated data from the database
                    query = f"SELECT * FROM {table_name}"
                    db_cursor.execute(query)
                    items = db_cursor.fetchall()

                    # Display the updated data in the text widget
                    match table_name:
                        case "users":
                            for item in items:
                                table_text.insert(tk.END,
                                                  f"RFID: {item[0]}\tUID: {item[1]}\tName:: {item[2]} {item[3]}\tSecurity Level {item[4]}\t Description:{item[4]}\n")
                            table_text.config(state=tk.DISABLED)
                        case "access_denied":
                            for item in items:
                                table_text.insert(tk.END,
                                                  f"RFID: {item[0]}\tAccess Point: {item[1]}\tTime: {item[2]}\tDate: {item[3]}\n")
                            table_text.config(state=tk.DISABLED)
                        case "access_granted":
                            for item in items:
                                table_text.insert(tk.END,
                                                  f"RFID: {item[0]}\tAccess Point: {item[1]}\tTime: {item[2]}\tDate: {item[3]}\n")
                            table_text.config(state=tk.DISABLED)
                except mysql.connector.Error as e:
                    print(f"Error executing query: {e}")
                finally:
                    # Disconnect from database
                    disconnect_from_database(db_connection, db_cursor)
            else:
                print("Database connection not established.")

        # Call refresh_table initially
        refresh_table()

        # Refresh user table automatically every 5 seconds
        table_window.after(5000, refresh_table)

    else:
        print("Database connection not established.")

def main_menu(rfid_queue):
    root = tk.Tk()
    selected_option = None

    root.title("RFID Main Menu")
    root.geometry("600x600")  # Set window size
    root.resizable(False, False)  # Lock the window size

    # Change background color to cyan
    root.config(bg="#57738b")

    # Add image at the top
    img_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(img_path):
        img = Image.open(img_path)
        img = img.resize((175, 100))  # Resize image
        img = ImageTk.PhotoImage(img)  # Convert image for tkinter
        img_label = tk.Label(root, image=img, bg="#57738b")
        img_label.image = img
        img_label.pack(pady=(20, 0))
    else:
        print("Image file not found.")

    # Functions for buttons
    def monitor():
        nonlocal selected_option
        selected_option = "Monitor"
        monitor_option_selected(rfid_queue, root)


    def view_access_granted_table():
        nonlocal selected_option
        selected_option = "View Access Granted Table"
        # Connect to database
        db_connection, db_cursor = connect_to_database()
        display_user_table(root, db_cursor, db_connection, "access_granted", "Access Granted Table")

    def view_access_denied_table():
        nonlocal selected_option
        selected_option = "View Access Denied Table"
        # Connect to database
        db_connection, db_cursor = connect_to_database()
        display_user_table(root, db_cursor, db_connection, "access_denied", "Access Denied Table")

    def view_user_config():
        nonlocal selected_option
        selected_option = "View User Config"
        # Connect to database


    def close_program():
        nonlocal selected_option
        selected_option = "Close Program"
        root.quit()

    monitor_button = tk.Button(root, text="Monitor", command=monitor, bg="#FF5733", fg="white",
                               font=("Arial", 12, "bold"), width=25, pady=3)
    monitor_button.pack(pady=5)



    access_granted_button = tk.Button(root, text="View Access Granted Table", command=view_access_granted_table,
                                      bg="#FF5733", fg="white", font=("Arial", 12, "bold"), width=25, pady=5)
    access_granted_button.pack(pady=5)

    access_denied_button = tk.Button(root, text="View Access Denied Table", command=view_access_denied_table,
                                     bg="#FF5733", fg="white", font=("Arial", 12, "bold"), width=25, pady=5)
    access_denied_button.pack(pady=5)

    access_denied_button = tk.Button(root, text="User Config", command=view_user_config,
                                     bg="#FF5733", fg="white", font=("Arial", 12, "bold"), width=25, pady=5)
    access_denied_button.pack(pady=5)

    close_button = tk.Button(root, text="Quit Program", command=close_program, bg="#00529B", fg="white",
                             font=("Arial", 12, "bold"), width=12, pady=5)
    close_button.pack(pady=5)

    root.mainloop()


def login():
    # Create login window
    login_window = tk.Tk()
    login_window.title("Login")
    login_window.geometry("400x350")

    # Change background color
    login_window.config(bg="#57738b")

    # Add image at the top
    img_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(img_path):
        img = Image.open(img_path)
        img = img.resize((175, 100))  # Resize image
        img = ImageTk.PhotoImage(img)  # Convert image for tkinter
        img_label = tk.Label(login_window, image=img, bg="#57738b")
        img_label.image = img
        img_label.pack(pady=(20, 10))
    else:
        print("Image file not found.")

    # Username and password labels and entry widgets
    username_label = tk.Label(login_window, text="Username:", font=("Arial", 12), bg="#57738b", fg="white")
    username_label.pack(pady=(0, 5))
    username_entry = tk.Entry(login_window, font=("Arial", 12))
    username_entry.pack()

    password_label = tk.Label(login_window, text="Password:", font=("Arial", 12), bg="#57738b", fg="white")
    password_label.pack(pady=(10, 5))
    password_entry = tk.Entry(login_window, font=("Arial", 12), show="*")
    password_entry.pack()

    def authenticate():
        # Authenticate user against the database
        db_connection, db_cursor = connect_to_database()
        if db_cursor and db_connection:
            userid = username_entry.get()
            password = password_entry.get()
            query = f"SELECT * FROM login WHERE userid = '{userid}' AND password = '{password}'"
            db_cursor.execute(query)
            user = db_cursor.fetchone()
            if user:
                # Close the login window
                login_window.destroy()
                # Proceed to main menu
                main_menu(rfid_queue)
            else:
                # Display error message
                error_label.config(text="Invalid username or password")
            disconnect_from_database(db_connection, db_cursor)
        else:
            print("Database connection not established.")

    # Login button
    login_button = tk.Button(login_window, text="Login", command=authenticate, bg="#FF5733", fg="white",
                             font=("Arial", 12, "bold"), width=10, pady=5)
    login_button.pack(pady=10)

    # Error label
    error_label = tk.Label(login_window, text="", font=("Arial", 12), bg="#57738b", fg="red")
    error_label.pack()

    login_window.mainloop()
def main_menu(rfid_queue):
    root = tk.Tk()
    selected_option = None

    root.title("RFID Main Menu")
    root.geometry("600x600")  # Set window size
    root.resizable(False, False)  # Lock the window size

    # Change background color to cyan
    root.config(bg="#57738b")

    # Add image at the top
    img_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(img_path):
        img = Image.open(img_path)
        img = img.resize((175, 100))  # Resize image
        img = ImageTk.PhotoImage(img)  # Convert image for tkinter
        img_label = tk.Label(root, image=img, bg="#57738b")
        img_label.image = img
        img_label.pack(pady=(20, 0))
    else:
        print("Image file not found.")

    # Functions for buttons
    def monitor():
        nonlocal selected_option
        selected_option = "Monitor"
        monitor_option_selected(rfid_queue, root)

    def view_access_granted_table():
        nonlocal selected_option
        selected_option = "View Access Granted Table"
        # Connect to database
        db_connection, db_cursor = connect_to_database()
        display_user_table(root, db_cursor, db_connection, "access_granted", "Access Granted Table")

    def view_access_denied_table():
        nonlocal selected_option
        selected_option = "View Access Denied Table"
        # Connect to database
        db_connection, db_cursor = connect_to_database()
        display_user_table(root, db_cursor, db_connection, "access_denied", "Access Denied Table")

    def view_user_config():
        nonlocal selected_option
        selected_option = "View User Config"
        # Connect to database
        user_config_menu();

    def close_program():
        nonlocal selected_option
        selected_option = "Close Program"
        root.quit()

    monitor_button = tk.Button(root, text="Monitor", command=monitor, bg="#FF5733", fg="white",
                               font=("Arial", 12, "bold"), width=25, pady=3)
    monitor_button.pack(pady=5)

    access_granted_button = tk.Button(root, text="View Access Granted Table", command=view_access_granted_table,
                                      bg="#FF5733", fg="white", font=("Arial", 12, "bold"), width=25, pady=5)
    access_granted_button.pack(pady=5)

    access_denied_button = tk.Button(root, text="View Access Denied Table", command=view_access_denied_table,
                                     bg="#FF5733", fg="white", font=("Arial", 12, "bold"), width=25, pady=5)
    access_denied_button.pack(pady=5)

    access_denied_button = tk.Button(root, text="User Config", command=view_user_config,
                                     bg="#FF5733", fg="white", font=("Arial", 12, "bold"), width=25, pady=5)
    access_denied_button.pack(pady=5)

    close_button = tk.Button(root, text="Quit Program", command=close_program, bg="#00529B", fg="white",
                             font=("Arial", 12, "bold"), width=12, pady=5)
    close_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    rfid_queue = queue.Queue()

    # Start RFID scanning
    ports = ['COM10', 'COM3', 'COM4']  # Adjust ports accordingly
    for port in ports:
        read_from_port(port, rfid_queue)

    # Login
    login()

