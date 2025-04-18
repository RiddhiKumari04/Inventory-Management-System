# Inventory Management System  

## Features  

- **Add, Update, and Delete Inventory Items**  
- **Real-time Inventory Tracking**  
- **MySQL Database Integration**  
- **Interactive UI using Streamlit**  

## Prerequisites  

Ensure you have the following installed:  

- Python 3.x  
- MySQL Server  
- Streamlit  
- Required Python packages (listed in `requirements.txt`)  

## Installation  

### 1️⃣ Clone the Repository  

```bash
git clone https://github.com/your-repo/inventory-management.git
cd inventory-management
```

### 2️⃣ Install Dependencies  

```bash
pip install -r requirements.txt
```

### 3️⃣ Configure Database  

Ensure MySQL is running and execute the following SQL commands to set up the database:  

```sql
CREATE DATABASE inventory_db;
USE inventory_db;

CREATE TABLE inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4️⃣ Update Configuration  

Modify `config.py` to match your MySQL credentials:  

```python
config = {
    'user': 'your_mysql_user',
    'password': 'your_mysql_password',
    'host': 'localhost',
    'port': 3306,
    'database': 'inventory_db'
}
```

### 5️⃣ Run the Application  

```bash
streamlit run app.py
```

## Troubleshooting  

### 🔹 Access Denied Error in MySQL  

Run the following in MySQL to grant permissions:  

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
FLUSH PRIVILEGES;
```

### 🔹 MySQL Connection Issue  

Ensure MySQL is running using:  

```bash
# For Linux
sudo systemctl status mysql  

# For Windows
net start MySQL80  
```

## License  

This project is licensed under the **MIT License**.  

## Author  
Dhruv kumar


## Contact
dhruv124kumar@gmail.com

---

Let me know if you need any modifications! 🚀
