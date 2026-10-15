from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key-for-production")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///shop.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    category = db.Column(db.String(80), default="General")
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), default="")
    stock = db.Column(db.Integer, default=0, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="Placed", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")
    user = db.relationship("User", backref="orders")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    product_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None

@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    cart_count = sum(int(q) for q in cart.values())
    return {"current_user": current_user(), "cart_count": cart_count}

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in first.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            flash("Admin access is required.", "error")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped

def cart_details():
    cart = session.get("cart", {})
    rows, total = [], 0
    for pid, qty in cart.items():
        product = db.session.get(Product, int(pid))
        qty = int(qty)
        if product and qty > 0:
            subtotal = product.price * qty
            rows.append({"product": product, "quantity": qty, "subtotal": subtotal})
            total += subtotal
    return rows, total

@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.filter_by(category=category)
    products = query.order_by(Product.id.desc()).all()
    categories = [row[0] for row in db.session.query(Product.category).distinct().order_by(Product.category).all()]
    return render_template("index.html", products=products, categories=categories, search=search, selected_category=category)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product.html", product=product)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter your name and email, and use a password of at least 6 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("That email is already registered.", "error")
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("Account created. Welcome!", "success")
            return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            flash("You are now logged in.", "success")
            return redirect(request.args.get("next") or url_for("index"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("index"))

@app.route("/cart")
def cart():
    rows, total = cart_details()
    return render_template("cart.html", rows=rows, total=total)

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        quantity = int(request.form.get("quantity", 1))
    except ValueError:
        quantity = 1
    if quantity < 1:
        quantity = 1
    if product.stock < 1:
        flash("This product is out of stock.", "error")
    else:
        cart = session.get("cart", {})
        new_quantity = int(cart.get(str(product.id), 0)) + quantity
        if new_quantity > product.stock:
            flash(f"Only {product.stock} item(s) are available.", "error")
        else:
            cart[str(product.id)] = new_quantity
            session["cart"] = cart
            session.modified = True
            flash("Added to your cart.", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/cart/update/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    cart = session.get("cart", {})
    product = db.session.get(Product, product_id)
    try:
        quantity = int(request.form.get("quantity", 1))
    except ValueError:
        quantity = 1
    if not product or quantity <= 0:
        cart.pop(str(product_id), None)
    elif quantity <= product.stock:
        cart[str(product_id)] = quantity
    else:
        flash(f"Only {product.stock} item(s) are available.", "error")
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    session.modified = True
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    rows, total = cart_details()
    if not rows:
        flash("Your cart is empty.", "info")
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        if not name or not address or not phone:
            flash("Please complete all delivery fields.", "error")
        else:
            # Re-check stock at checkout before changing inventory.
            for row in rows:
                product = db.session.get(Product, row["product"].id)
                if not product or row["quantity"] > product.stock:
                    flash(f"Not enough stock for {row['product'].name}. Please update your cart.", "error")
                    return redirect(url_for("cart"))
            order = Order(user_id=current_user().id, customer_name=name, address=address,
                          phone=phone, total=total, status="Placed")
            db.session.add(order)
            db.session.flush()
            for row in rows:
                product = db.session.get(Product, row["product"].id)
                product.stock -= row["quantity"]
                db.session.add(OrderItem(order_id=order.id, product_id=product.id,
                                         product_name=product.name, price=product.price,
                                         quantity=row["quantity"]))
            db.session.commit()
            session["cart"] = {}
            flash(f"Order #{order.id} placed successfully with Cash on Delivery.", "success")
            return redirect(url_for("order_detail", order_id=order.id))
    return render_template("checkout.html", rows=rows, total=total)

@app.route("/orders")
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user().id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=user_orders)

@app.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    user = current_user()
    if order.user_id != user.id and not user.is_admin:
        flash("You cannot view that order.", "error")
        return redirect(url_for("orders"))
    return render_template("order_detail.html", order=order)

@app.route("/admin")
@admin_required
def admin():
    return render_template("admin.html", products=Product.query.order_by(Product.id.desc()).all(),
                           orders=Order.query.order_by(Order.created_at.desc()).all(),
                           users_count=User.query.count())

@app.route("/admin/product/new", methods=["GET", "POST"])
@app.route("/admin/product/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_form(product_id=None):
    product = db.session.get(Product, product_id) if product_id else None
    if product_id and not product:
        return redirect(url_for("admin"))
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            price = float(request.form.get("price", "0"))
            stock = int(request.form.get("stock", "0"))
            if not name or price < 0 or stock < 0:
                raise ValueError
            if not product:
                product = Product(name=name, price=price, stock=stock)
                db.session.add(product)
            product.name = name
            product.description = request.form.get("description", "").strip()
            product.category = request.form.get("category", "General").strip() or "General"
            product.price = price
            product.stock = stock
            product.image_url = request.form.get("image_url", "").strip()
            db.session.commit()
            flash("Product saved.", "success")
            return redirect(url_for("admin"))
        except ValueError:
            flash("Enter a valid product name, price, and stock quantity.", "error")
    return render_template("product_form.html", product=product)

@app.route("/admin/product/<int:product_id>/delete", methods=["POST"])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Preserve order history; historical items have a nullable product_id.
    OrderItem.query.filter_by(product_id=product.id).update({OrderItem.product_id: None})
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    status = request.form.get("status", "")
    if status in {"Placed", "Processing", "Shipped", "Delivered", "Cancelled"}:
        order.status = status
        db.session.commit()
        flash("Order status updated.", "success")
    return redirect(url_for("admin"))

def seed_data():
    if Product.query.count() == 0:
        products = [
            Product(name="Wireless Headphones", description="Comfortable wireless headphones for music, classes, and calls.",
                    category="Electronics", price=1499, stock=15, image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85"),
            Product(name="Smart Watch", description="A stylish everyday watch with useful activity features.",
                    category="Electronics", price=2299, stock=12, image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=85"),
            Product(name="Everyday Backpack", description="A practical backpack for college, work, and short trips.",
                    category="Accessories", price=999, stock=20, image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=85"),
            Product(name="Running Shoes", description="Lightweight casual running shoes for daily wear.",
                    category="Fashion", price=1799, stock=10, image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85"),
            Product(name="Sunglasses", description="Classic sunglasses for everyday style.",
                    category="Fashion", price=699, stock=18, image_url="https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=900&q=85"),
            Product(name="Desk Lamp", description="A modern desk lamp for your study or workspace.",
                    category="Home", price=849, stock=8, image_url="https://images.unsplash.com/photo-1503602642458-232111445657?auto=format&fit=crop&w=900&q=85"),
        ]
        db.session.add_all(products)
    if not User.query.filter_by(email="admin@shop.local").first():
        admin_user = User(name="Shop Admin", email="admin@shop.local",
                          password_hash=generate_password_hash("Admin123!"), is_admin=True)
        db.session.add(admin_user)
    db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == "__main__":
    app.run(debug=True)
