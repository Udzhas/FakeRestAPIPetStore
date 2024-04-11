import json

from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
DATABASE = 'petstore.db'


# Function to get a database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


# Function to execute SQL queries and return results
def execute_query(query, args=()):
    cur = get_db().cursor()
    cur.execute(query, args)
    get_db().commit()
    return cur.fetchall()


# Define data models
class User:
    def __init__(self, id, username, email, phone, address, user_status):
        self.id = id
        self.username = username
        self.email = email
        self.phone = phone
        self.address = address
        self.user_status = user_status


class Pet:
    def __init__(self, id, name, category_id, photo_urls, tags, status):
        self.id = id
        self.name = name
        self.category_id = category_id
        self.photo_urls = photo_urls
        self.tags = tags
        self.status = status


class Order:
    def __init__(self, id, pet_id, quantity, ship_date, status, complete):
        self.id = id
        self.pet_id = pet_id
        self.quantity = quantity
        self.ship_date = ship_date
        self.status = status
        self.complete = complete


class Category:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class Tag:
    def __init__(self, id, name):
        self.id = id
        self.name = name


# Function to create tables if they don't exist
def init_db():
    with app.app_context():
        cursor = get_db().cursor()
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                userStatus INTEGER NOT NULL,
                address TEXT NOT NULL
            )
        ''')

        # Create pets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pets (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                photoUrls TEXT NOT NULL,
                tags TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                pet_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                shipDate TEXT NOT NULL,
                status TEXT NOT NULL,
                complete BOOLEAN NOT NULL,
                FOREIGN KEY (pet_id) REFERENCES pets (id)
            )
        ''')

        # Create categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')

        # Create tags table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')

        get_db().commit()


# Function to close database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Initialize database when the application starts
init_db()


# Function to execute SQL queries and return results

# Define endpoints
# /users
@app.route('/users', methods=['GET'])
def get_users():
    query = "SELECT * FROM users"
    users = execute_query(query)
    user_objects = [User(*user) for user in users]
    return jsonify([vars(user) for user in user_objects])


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    user = execute_query(query, (user_id,))
    if user:
        return jsonify(vars(User(*user[0])))
    return jsonify({"error": "User not found"}), 404


@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    # Validate required fields
    required_fields = ['username', 'email', 'phone']
    for field in required_fields:
        if field not in data:
            return jsonify(message=f"Missing required field: {field}"), 400
    # Validate email format
    if '@' not in data['email']:
        return jsonify(message="Invalid email format"), 400
    # Validate phone number format (e.g., 10 digits)
    if len(data['phone']) != 10 or not data['phone'].isdigit():
        return jsonify(message="Invalid phone number format. Phone number must be 10 digits."), 400
    # Validate username length (e.g., between 3 and 50 characters)
    if len(data['username']) < 3 or len(data['username']) > 50:
        return jsonify(message="Username must be between 3 and 50 characters long."), 400
    # Validate address length (optional, limit to 100 characters)
    if 'address' in data and len(data['address']) > 100:
        return jsonify(message="Address must be less than 100 characters long."), 400
    # Validate user_status length (optional, limit to 50 characters)
    if 'user_status' in data and data['user_status'] > 50:
        return jsonify(message="User status must be less than 50"), 400
    # Insert user into database
    query = "INSERT INTO users (username, email, phone, address, user_status) VALUES (?, ?, ?, ?, ?)"
    args = (data['username'], data['email'], data['phone'], data.get('address'), data.get('user_status'))
    execute_query(query, args)
    return jsonify({"message": "User created successfully"}), 201


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    # Check if user exists
    query = "SELECT * FROM users WHERE id = ?"
    user = execute_query(query, (user_id,))
    if not user:
        return jsonify(message="User not found"), 404

    # Validate email format if provided
    if 'email' in data and '@' not in data['email']:
        return jsonify(message="Invalid email format"), 400

    # Validate phone number format if provided
    if 'phone' in data and (len(data['phone']) != 10 or not data['phone'].isdigit()):
        return jsonify(message="Invalid phone number format. Phone number must be 10 digits."), 400

    # Validate username length if provided
    if 'username' in data and (len(data['username']) < 3 or len(data['username']) > 50):
        return jsonify(message="Username must be between 3 and 50 characters long."), 400

    # Validate address length if provided
    if 'address' in data and len(data['address']) > 100:
        return jsonify(message="Address must be less than 100 characters long."), 400

    # Validate user_status length if provided
    if 'user_status' in data and data['user_status'] > 50:
        return jsonify(message="User status must be less than 50"), 400

    # Update user in database
    query = "UPDATE users SET username = ?, email = ?, phone = ?, address = ?, user_status = ? WHERE id = ?"
    args = (
        data.get('username', user[0][1]),  # Use existing username if not provided in request
        data.get('email', user[0][2]),  # Use existing email if not provided in request
        data.get('phone', user[0][3]),  # Use existing phone if not provided in request
        data.get('address', user[0][4]),  # Use existing address if not provided in request
        data.get('user_status', user[0][5]),  # Use existing user_status if not provided in request
        user_id
    )
    execute_query(query, args)
    return jsonify({"message": "User updated successfully"})


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Check if user exists
    query = "SELECT * FROM users WHERE id = ?"
    user = execute_query(query, (user_id,))
    if not user:
        return jsonify(message="User not found"), 404

    # Delete user from database
    query = "DELETE FROM users WHERE id = ?"
    execute_query(query, (user_id,))
    return jsonify({"message": "User deleted successfully"}), 204


# /pets
@app.route('/pets', methods=['GET'])
def get_pets():
    query = "SELECT * FROM pets"
    pets = execute_query(query)
    pet_objects = [Pet(*pet) for pet in pets]
    return jsonify([vars(pet) for pet in pet_objects])


@app.route('/pets/<int:pet_id>', methods=['GET'])
def get_pet(pet_id):
    # Check if pet exists
    query = "SELECT * FROM pets WHERE id = ?"
    pet = execute_query(query, (pet_id,))
    if not pet:
        return jsonify(message="Pet not found"), 404

    # If pet exists, return its data
    pet_data = pet[0]
    pet_obj = Pet(*pet_data)
    return jsonify(vars(pet_obj))


@app.route('/pets', methods=['POST'])
def create_pet():
    data = request.json
    # Validate required fields
    if 'name' not in data or 'category_id' not in data or 'status' not in data:
        return jsonify(message="Missing required fields: name, category, status"), 400
    # Validate category length
    if data['category_id'] > 50:
        return jsonify(message="Category must be less than 50"), 400
    # Validate status length
    if len(data['status']) > 50:
        return jsonify(message="Status must be less than 50 characters long"), 400

    # Insert pet into database
    query = "INSERT INTO pets (name, category_id, photo_urls, tags, status) VALUES (?, ?, ?, ?, ?)"
    args = (
        data['name'],
        data['category_id'],
        data.get('photo_urls', ''),  # Allow photo_urls to be optional
        data.get('tags', ''),  # Allow tags to be optional
        data['status']
    )
    execute_query(query, args)
    return jsonify({"message": "Pet created successfully"}), 201


@app.route('/pets/<int:pet_id>', methods=['PUT'])
def update_pet(pet_id):
    data = request.json
    # Check if pet exists
    query = "SELECT * FROM pets WHERE id = ?"
    pet = execute_query(query, (pet_id,))
    if not pet:
        return jsonify(message="Pet not found"), 404

    # Validate category length if provided
    if 'category' in data and data['category_id'] > 50:
        return jsonify(message="Category must be less than 50"), 400
    # Validate status length if provided
    if 'status' in data and len(data['status']) > 50:
        return jsonify(message="Status must be less than 50 characters long"), 400

    # Other validations can be added as needed

    # Update pet in database
    query = "UPDATE pets SET name = ?, category_id = ?, photo_urls = ?, tags = ?, status = ? WHERE id = ?"
    args = (
        data.get('name', pet[0][1]),  # Use existing name if not provided in request
        data.get('category_id', pet[0][2]),  # Use existing category if not provided in request
        data.get('photo_urls', pet[0][3]),  # Use existing photo_urls if not provided in request
        data.get('tags', pet[0][4]),  # Use existing tags if not provided in request
        data.get('status', pet[0][5]),  # Use existing status if not provided in request
        pet_id
    )
    execute_query(query, args)
    return jsonify({"message": "Pet updated successfully"})


@app.route('/pets/<int:pet_id>', methods=['DELETE'])
def delete_pet(pet_id):
    # Check if pet exists
    query = "SELECT * FROM pets WHERE id = ?"
    pet = execute_query(query, (pet_id,))
    if not pet:
        return jsonify(message="Pet not found"), 404

    # Delete pet from database
    query = "DELETE FROM pets WHERE id = ?"
    execute_query(query, (pet_id,))
    return jsonify({"message": "Pet deleted successfully"}), 204


# /orders
@app.route('/orders', methods=['GET'])
def get_orders():
    query = "SELECT * FROM orders"
    orders = execute_query(query)
    order_objects = [Order(*order) for order in orders]
    return jsonify([vars(order) for order in order_objects])


@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    # Check if order exists
    query = "SELECT * FROM orders WHERE id = ?"
    order = execute_query(query, (order_id,))
    if not order:
        return jsonify(message="Order not found"), 404

    # If order exists, return its data
    order_data = order[0]
    order_obj = Order(*order_data)
    return jsonify(vars(order_obj))


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    # Validate required fields
    if 'pet_id' not in data or 'quantity' not in data or 'status' not in data or 'shipDate' not in data:
        return jsonify(message="Missing required fields: pet_id, quantity, status, shipDate"), 400

    # Validate pet_id format
    if not isinstance(data['pet_id'], int) or data['pet_id'] < 0:
        return jsonify(message="Invalid pet_id format"), 400
    # Validate quantity format
    if not isinstance(data['quantity'], int) or data['quantity'] <= 0:
        return jsonify(message="Invalid quantity format"), 400

    # Validate status length
    if len(data['status']) > 50:
        return jsonify(message="Status must be less than 50 characters long"), 400

    # Other validations can be added as needed
    if 'shipDate' not in data:
        return jsonify(message="Ship date is required"), 400

    # Insert order into database
    query = "INSERT INTO orders (pet_id, quantity, ship_date, status, complete) VALUES (?, ?, ?, ?, ?)"
    args = (
        data['pet_id'],
        data['quantity'],
        data['shipDate'],
        data['status'],
        data['complete']
    )
    execute_query(query, args)
    return jsonify({"message": "Order created successfully"}), 201


@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    # Check if order exists
    query = "SELECT * FROM orders WHERE id = ?"
    order = execute_query(query, (order_id,))
    if not order:
        return jsonify(message="Order not found"), 404

    # Validate quantity format if provided
    if 'quantity' in data:
        if not isinstance(data['quantity'], int) or data['quantity'] <= 0:
            return jsonify(message="Invalid quantity format"), 400
    # Validate status length if provided
    if 'status' in data and len(data['status']) > 50:
        return jsonify(message="Status must be less than 50 characters long"), 400

    # Validate ship_date format if provided
    if 'shipDate' not in data:
        return jsonify(message="Ship date is required"), 400

    # Validate complete format if provided
    if 'complete' in data:
        if not isinstance(data['complete'], bool):
            return jsonify(message="Invalid complete format"), 400

    # Update order in database
    query = "UPDATE orders SET pet_id = ?, quantity = ?, ship_date = ?, status = ?, complete = ? WHERE id = ?"
    args = (
        data.get('pet_id', order[0][1]),  # Use existing pet_id if not provided in request
        data.get('quantity', order[0][2]),  # Use existing quantity if not provided in request
        data.get('shipDate', order[0][3]),  # Use existing ship_date if not provided in request
        data.get('status', order[0][4]),  # Use existing status if not provided in request
        data.get('complete', order[0][5]),  # Use existing complete if not provided in request
        order_id
    )
    execute_query(query, args)
    return jsonify({"message": "Order updated successfully"})


@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    # Check if order exists
    query = "SELECT * FROM orders WHERE id = ?"
    order = execute_query(query, (order_id,))
    if not order:
        return jsonify(message="Order not found"), 404

    # Delete order from database
    query = "DELETE FROM orders WHERE id = ?"
    execute_query(query, (order_id,))
    return jsonify(message="Order deleted successfully"), 204


# /categories
@app.route('/categories', methods=['GET'])
def get_categories():
    query = "SELECT * FROM categories"
    categories = execute_query(query)
    category_objects = [Category(*category) for category in categories]
    return jsonify([vars(category) for category in category_objects])


@app.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    # Check if category exists
    query = "SELECT * FROM categories WHERE id = ?"
    category = execute_query(query, (category_id,))
    if not category:
        return jsonify(message="Category not found"), 404

    # If category exists, return its data
    category_data = category[0]
    category_obj = Category(*category_data)
    return jsonify(vars(category_obj))


@app.route('/categories', methods=['POST'])
def create_category():
    data = request.json
    # Validate required fields
    if 'name' not in data:
        return jsonify(message="Missing required field: name"), 400

    # Validate name length
    if len(data['name']) > 50:
        return jsonify(message="Name must be less than 50 characters long"), 400

    # Insert category into database
    query = "INSERT INTO categories (name) VALUES (?)"
    args = (data['name'],)
    execute_query(query, args)
    return jsonify({"message": "Category created successfully"}), 201


@app.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.json
    # Check if category exists
    query = "SELECT * FROM categories WHERE id = ?"
    category = execute_query(query, (category_id,))
    if not category:
        return jsonify(message="Category not found"), 404

    # Validate name length if provided
    if 'name' in data and len(data['name']) > 50:
        return jsonify(message="Name must be less than 50 characters long"), 400

    # Update category in database
    query = "UPDATE categories SET name = ? WHERE id = ?"
    args = (
        data.get('name', category[0][1]),  # Use existing name if not provided in request
        category_id
    )
    execute_query(query, args)
    return jsonify({"message": "Category updated successfully"})


@app.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    # Check if category exists
    query = "SELECT * FROM categories WHERE id = ?"
    category = execute_query(query, (category_id,))
    if not category:
        return jsonify(message="Category not found"), 404

    # Delete category from database
    query = "DELETE FROM categories WHERE id = ?"
    execute_query(query, (category_id,))
    return jsonify({"message": "Category deleted successfully"}), 204


# /orders
@app.route('/tags', methods=['GET'])
def get_tags():
    query = "SELECT * FROM tags"
    tags = execute_query(query)
    tag_objects = [Tag(*tag) for tag in tags]
    return jsonify([vars(tag) for tag in tag_objects])


@app.route('/tags/<int:tag_id>', methods=['GET'])
def get_tag(tag_id):
    # Check if tag exists
    query = "SELECT * FROM tags WHERE id = ?"
    tag = execute_query(query, (tag_id,))
    if not tag:
        return jsonify(message="Tag not found"), 404

    # If tag exists, return its data
    tag_data = tag[0]
    tag_obj = Tag(*tag_data)
    return jsonify(vars(tag_obj))


@app.route('/tags', methods=['POST'])
def create_tag():
    data = request.json
    # Validate required field
    if 'name' not in data:
        return jsonify(message="Missing required field: name"), 400

    # Validate name length
    if len(data['name']) > 50:
        return jsonify(message="Name must be less than 50 characters long"), 400

    # Insert tag into database
    query = "INSERT INTO tags (name) VALUES (?)"
    args = (data['name'],)
    execute_query(query, args)
    return jsonify({"message": "Tag created successfully"}), 201


@app.route('/tags/<int:tag_id>', methods=['PUT'])
def update_tag(tag_id):
    data = request.json
    # Check if tag exists
    query = "SELECT * FROM tags WHERE id = ?"
    tag = execute_query(query, (tag_id,))
    if not tag:
        return jsonify(message="Tag not found"), 404

    # Validate name length if provided
    if 'name' in data and len(data['name']) > 50:
        return jsonify(message="Name must be less than 50 characters long"), 400

    # Update tag in database
    query = "UPDATE tags SET name = ? WHERE id = ?"
    args = (
        data.get('name', tag[0][1]),  # Use existing name if not provided in request
        tag_id
    )
    execute_query(query, args)
    return jsonify({"message": "Tag updated successfully"})


@app.route('/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    # Check if tag exists
    query = "SELECT * FROM tags WHERE id = ?"
    tag = execute_query(query, (tag_id,))
    if not tag:
        return jsonify(message="Tag not found"), 404

    # Delete tag from database
    query = "DELETE FROM tags WHERE id = ?"
    execute_query(query, (tag_id,))
    return jsonify({"message": "Tag deleted successfully"}), 204


@app.route('/complex-json-file', methods=['GET'])
def get_json_file():
    try:
        # Read the JSON file
        with open('complex_data.json', 'r') as file:
            json_data = json.load(file)
        # Return the JSON data as the response
        return jsonify(json_data)
    except Exception as e:
        # Handle any exceptions and return an error response
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)
