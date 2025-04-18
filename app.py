import streamlit as st
import mysql.connector
import pandas as pd
import requests
from streamlit_lottie import st_lottie
from datetime import datetime
import plotly.express as px
import io
import base64
import logging
import sys

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)  # Also log to terminal
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
config = {
    'user': 'root',
    'password': 'April182005!',
    'host': 'localhost',
    'port': 3306,
    'database': 'inventory_db'
}

# Lottie animation helper
def load_lottie(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

# Database connection with error handling
def create_connection():
    logger.info("Attempting database connection")
    try:
        db = mysql.connector.connect(**config)
        logger.info("Database connected successfully")
        return db
    except mysql.connector.Error as err:
        logger.error(f"Database connection failed: {err}")
        st.error(f"Database connection failed: {err}")
        return None

# Database and table initialization
def initialize_database(db):
    logger.info("Initializing database")
    cursor = db.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS inventory_db")
        cursor.execute("USE inventory_db")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            category VARCHAR(100),
            quantity INT NOT NULL DEFAULT 0,
            unit_price DECIMAL(10,2),
            supplier VARCHAR(255),
            supplier_contact VARCHAR(50),
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            minimum_stock INT DEFAULT 0,
            barcode VARCHAR(50),
            location VARCHAR(100)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_id INT,
            transaction_type ENUM('IN', 'OUT', 'ADJUSTMENT') NOT NULL,
            quantity INT NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            user VARCHAR(100),
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
        )
        """)
        
        db.commit()
        logger.info("Database initialized successfully")
    except mysql.connector.Error as err:
        logger.error(f"Database initialization failed: {err}")
        st.error(f"Database initialization failed: {err}")

# CRUD Operations with validation
def fetch_item_by_id(db, item_id):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
        return cursor.fetchone()
    except mysql.connector.Error as err:
        logger.error(f"Failed to fetch item: {err}")
        st.error(f"Failed to fetch item: {err}")
        return None

def add_item(db, name, category, quantity, unit_price, supplier, supplier_contact, minimum_stock, barcode, location):
    try:
        cursor = db.cursor()
        query = """
        INSERT INTO items (name, category, quantity, unit_price, supplier, supplier_contact, minimum_stock, barcode, location)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, category, quantity, unit_price, supplier, supplier_contact, minimum_stock, barcode, location))
        db.commit()
        st.success(f"Item '{name}' added successfully!")
    except mysql.connector.Error as err:
        logger.error(f"Failed to add item: {err}")
        st.error(f"Failed to add item: {err}")

def fetch_all_items(db):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM items")
        return cursor.fetchall()
    except mysql.connector.Error as err:
        logger.error(f"Failed to fetch items: {err}")
        st.error(f"Failed to fetch items: {err}")
        return []

def update_item(db, item_id, name, category, quantity, unit_price, supplier, supplier_contact, minimum_stock, barcode, location):
    try:
        cursor = db.cursor()
        query = """
        UPDATE items SET name = %s, category = %s, quantity = %s, unit_price = %s, 
        supplier = %s, supplier_contact = %s, minimum_stock = %s, barcode = %s, location = %s 
        WHERE id = %s
        """
        cursor.execute(query, (name, category, quantity, unit_price, supplier, supplier_contact, minimum_stock, barcode, location, item_id))
        db.commit()
        st.success("Item updated successfully!")
    except mysql.connector.Error as err:
        logger.error(f"Failed to update item: {err}")
        st.error(f"Failed to update item: {err}")

def delete_item(db, item_id):
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM transactions WHERE item_id = %s", (item_id,))
        cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
        db.commit()
        st.success("Item deleted successfully!")
    except mysql.connector.Error as err:
        logger.error(f"Failed to delete item: {err}")
        st.error(f"Failed to delete item: {err}")

# Transaction Operations with validation
def add_transaction(db, item_id, transaction_type, quantity, notes, user):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT quantity FROM items WHERE id = %s", (item_id,))
        result = cursor.fetchone()
        if result is None:
            st.error("Item ID not found!")
            return
        current_qty = result[0]
        
        if transaction_type == "OUT" and quantity > current_qty:
            st.error("Insufficient stock for this transaction!")
            return
        
        if transaction_type == "IN":
            cursor.execute("UPDATE items SET quantity = quantity + %s WHERE id = %s", (quantity, item_id))
        elif transaction_type == "OUT":
            cursor.execute("UPDATE items SET quantity = quantity - %s WHERE id = %s", (quantity, item_id))
        else:  # ADJUSTMENT
            cursor.execute("UPDATE items SET quantity = %s WHERE id = %s", (quantity, item_id))
            
        query = """
        INSERT INTO transactions (item_id, transaction_type, quantity, notes, user)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (item_id, transaction_type, quantity, notes, user))
        db.commit()
        st.success("Transaction recorded successfully!")
    except mysql.connector.Error as err:
        logger.error(f"Failed to record transaction: {err}")
        st.error(f"Failed to record transaction: {err}")

def fetch_all_transactions(db):
    try:
        cursor = db.cursor()
        query = """
        SELECT t.id, i.name, t.transaction_type, t.quantity, t.transaction_date, t.notes, t.user
        FROM transactions t
        JOIN items i ON t.item_id = i.id
        ORDER BY t.transaction_date DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        logger.error(f"Failed to fetch transactions: {err}")
        st.error(f"Failed to fetch transactions: {err}")
        return []

# Search function
def search_items(db, search_term, search_field):
    try:
        cursor = db.cursor()
        query = f"SELECT * FROM items WHERE {search_field} LIKE %s"
        cursor.execute(query, (f"%{search_term}%",))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        logger.error(f"Search failed: {err}")
        st.error(f"Search failed: {err}")
        return []

# Export to CSV
def export_to_csv(data, filename):
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV</a>'
    return href

# Main Application
def main():
    logger.info("Starting Inventory Management System")
    st.set_page_config(page_title="Inventory Management System", layout="wide")  # Moved outside try block
    
    try:
        st.title("Inventory Management System 📦")
        logger.info("Title displayed")
        
        db = create_connection()
        if db is None:
            logger.error("Database connection failed - exiting")
            return
        
        initialize_database(db)
        logger.info("Database setup complete")

        # Session state for user
        if 'user' not in st.session_state:
            st.session_state.user = "Guest"

        # Sidebar
        with st.sidebar:
            st.header("Navigation")
            menu = [
                "Dashboard", "Add Item", "View Inventory", "Update Item",
                "Delete Item", "Record Transaction", "Transaction History",
                "Low Stock Alerts", "Search Items", "Reports"
            ]
            choice = st.selectbox("Menu", menu)
            st.session_state.user = st.text_input("User Name", value=st.session_state.user)

        # Main content
        if choice == "Dashboard":
            st.subheader("Inventory Dashboard")
            items = fetch_all_items(db)
            if items:
                cols = ['ID', 'Name', 'Category', 'Quantity', 'Unit Price', 'Supplier', 'Supplier Contact', 'Date Added', 'Min Stock', 'Barcode', 'Location']
                df = pd.DataFrame(items, columns=cols)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Items", len(items))
                with col2:
                    low_stock = len([item for item in items if item[3] <= item[8]])
                    st.metric("Low Stock Items", low_stock)
                with col3:
                    total_value = sum(item[3] * item[4] for item in items if item[4] is not None)
                    st.metric("Total Inventory Value", f"${total_value:,.2f}")
                
                fig = px.bar(df, x="Name", y="Quantity", title="Stock Levels by Item")
                st.plotly_chart(fig, use_container_width=True)

        elif choice == "Add Item":
            st.subheader("Add New Item")
            with st.form("add_item_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Item Name*")
                    category = st.text_input("Category")
                    quantity = st.number_input("Initial Quantity", min_value=0)
                    unit_price = st.number_input("Unit Price", min_value=0.0, format="%.2f")
                    supplier = st.text_input("Supplier")
                with col2:
                    supplier_contact = st.text_input("Supplier Contact")
                    minimum_stock = st.number_input("Minimum Stock Level", min_value=0)
                    barcode = st.text_input("Barcode")
                    location = st.text_input("Storage Location")
                    submit = st.form_submit_button("Add Item")
                if submit and name:
                    add_item(db, name, category, quantity, unit_price, supplier, supplier_contact, minimum_stock, barcode, location)
                elif submit:
                    st.error("Item Name is required!")

        elif choice == "View Inventory":
            st.subheader("Current Inventory")
            items = fetch_all_items(db)
            if items:
                df = pd.DataFrame(items, columns=['ID', 'Name', 'Category', 'Quantity', 'Unit Price', 'Supplier', 'Supplier Contact', 'Date Added', 'Min Stock', 'Barcode', 'Location'])
                st.dataframe(df, use_container_width=True)
                st.markdown(export_to_csv(df, "inventory_export.csv"), unsafe_allow_html=True)

        elif choice == "Update Item":
            st.subheader("Update Item")
            item_id = st.number_input("Enter Item ID", min_value=1)
            if st.button("Fetch Item"):
                item = fetch_item_by_id(db, item_id)
                if item:
                    with st.form("update_item_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            name = st.text_input("Item Name", value=item[1])
                            category = st.text_input("Category", value=item[2])
                            quantity = st.number_input("Quantity", value=item[3])
                            unit_price = st.number_input("Unit Price", value=float(item[4]), format="%.2f")
                            supplier = st.text_input("Supplier", value=item[5])
                        with col2:
                            supplier_contact = st.text_input("Supplier Contact", value=item[6])
                            minimum_stock = st.number_input("Minimum Stock Level", value=item[8])
                            barcode = st.text_input("Barcode", value=item[9])
                            location = st.text_input("Storage Location", value=item[10])
                            submit = st.form_submit_button("Update Item")
                        if submit:
                            update_item(db, item_id, name, category, quantity, unit_price, supplier, supplier_contact, minimum_stock, barcode, location)
                else:
                    st.error("Item not found")

        elif choice == "Delete Item":
            st.subheader("Delete Item")
            item_id = st.number_input("Enter Item ID to Delete", min_value=1)
            if st.button("Delete", type="primary"):
                if st.button("Confirm Deletion"):
                    delete_item(db, item_id)

        elif choice == "Record Transaction":
            st.subheader("Record Inventory Transaction")
            with st.form("transaction_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    item_id = st.number_input("Item ID", min_value=1)
                    trans_type = st.selectbox("Transaction Type", ["IN", "OUT", "ADJUSTMENT"])
                    quantity = st.number_input("Quantity", min_value=1)
                with col2:
                    notes = st.text_area("Notes")
                    submit = st.form_submit_button("Record Transaction")
                if submit:
                    add_transaction(db, item_id, trans_type, quantity, notes, st.session_state.user)

        elif choice == "Transaction History":
            st.subheader("Transaction History")
            transactions = fetch_all_transactions(db)
            if transactions:
                df = pd.DataFrame(transactions, columns=['ID', 'Item Name', 'Type', 'Quantity', 'Date', 'Notes', 'User'])
                st.dataframe(df, use_container_width=True)
                st.markdown(export_to_csv(df, "transactions_export.csv"), unsafe_allow_html=True)
                
                df['Date'] = pd.to_datetime(df['Date'])
                fig = px.line(df, x="Date", y="Quantity", color="Type", title="Transaction Trends")
                st.plotly_chart(fig, use_container_width=True)

        elif choice == "Low Stock Alerts":
            st.subheader("Low Stock Alerts")
            items = fetch_all_items(db)
            low_stock_items = [item for item in items if item[3] <= item[8]]
            if low_stock_items:
                df = pd.DataFrame(low_stock_items, columns=['ID', 'Name', 'Category', 'Quantity', 'Unit Price', 'Supplier', 'Supplier Contact', 'Date Added', 'Min Stock', 'Barcode', 'Location'])
                st.dataframe(df, use_container_width=True)
                st.warning(f"{len(low_stock_items)} items below minimum stock level!")
            else:
                st.success("No items below minimum stock level!")

        elif choice == "Search Items":
            st.subheader("Search Inventory")
            search_field = st.selectbox("Search By", ["name", "category", "supplier", "barcode"])
            search_term = st.text_input("Search Term")
            if st.button("Search"):
                results = search_items(db, search_term, search_field)
                if results:
                    df = pd.DataFrame(results, columns=['ID', 'Name', 'Category', 'Quantity', 'Unit Price', 'Supplier', 'Supplier Contact', 'Date Added', 'Min Stock', 'Barcode', 'Location'])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No matching items found")

        elif choice == "Reports":
            st.subheader("Inventory Reports")
            report_type = st.selectbox("Select Report", ["Stock Value", "Transaction Summary", "Category Breakdown"])
            
            if report_type == "Stock Value":
                items = fetch_all_items(db)
                df = pd.DataFrame(items, columns=['ID', 'Name', 'Category', 'Quantity', 'Unit Price', 'Supplier', 'Supplier Contact', 'Date Added', 'Min Stock', 'Barcode', 'Location'])
                df['Total Value'] = df['Quantity'] * df['Unit Price']
                st.dataframe(df[['Name', 'Quantity', 'Unit Price', 'Total Value']])
                fig = px.pie(df, values='Total Value', names='Name', title="Stock Value Distribution")
                st.plotly_chart(fig)
                
            elif report_type == "Transaction Summary":
                transactions = fetch_all_transactions(db)
                df = pd.DataFrame(transactions, columns=['ID', 'Item Name', 'Type', 'Quantity', 'Date', 'Notes', 'User'])
                summary = df.groupby('Type')['Quantity'].sum().reset_index()
                st.dataframe(summary)
                fig = px.bar(summary, x="Type", y="Quantity", title="Transaction Summary")
                st.plotly_chart(fig)
                
            elif report_type == "Category Breakdown":
                items = fetch_all_items(db)
                df = pd.DataFrame(items, columns=['ID', 'Name', 'Category', 'Quantity', 'Unit Price', 'Supplier', 'Supplier Contact', 'Date Added', 'Min Stock', 'Barcode', 'Location'])
                category_summary = df.groupby('Category')['Quantity'].sum().reset_index()
                st.dataframe(category_summary)
                fig = px.pie(category_summary, values='Quantity', names='Category', title="Inventory by Category")
                st.plotly_chart(fig)

        db.close()
        logger.info("Application shutdown cleanly")

    except Exception as e:
        logger.error(f"Application crashed: {e}", exc_info=True)
        st.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
