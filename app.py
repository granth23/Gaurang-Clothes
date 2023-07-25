import gevent.monkey
gevent.monkey.patch_all()

from flask import Flask, render_template, request, redirect, url_for, flash
from wtforms import StringField, SubmitField, IntegerField
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, current_user
from pymongo.errors import DuplicateKeyError
from db import get_user, save_user, update_cart, get_cart, set_qty
from db import user_cart_prod, set_cart, status, add_info
from db import all_products, get_product, get_product_id
from db import bill, mail, prod_qty, get_total, prod_id, search_prod
from db import all_prod, update_product, save_product, updates
from db import all_orders, ord_track, track_all, empty_cart, total_items
from flask_socketio import SocketIO
import razorpay


app = Flask(__name__)
app.secret_key = "granthbagadiagranthbagadia"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


tags = ['PS4', 'PS5', 'XBOX X', 'XBOX-1', 'SURFACE', 'ACCESSORIES', 'NINTENDO']


class New(FlaskForm):
    name = StringField('name')
    category = StringField('category')
    image = StringField('image')
    info = StringField('info')
    mrp = IntegerField('MRP')
    srp = IntegerField('SRP')
    quantity = IntegerField('Quantity')
    submit = SubmitField('Submit')


class Info(FlaskForm):
    name = StringField('Name')
    phone = StringField('Phone')
    address = StringField('Address')
    submit = SubmitField('Submit')


class Track(FlaskForm):
    idt = StringField('Order ID')
    ts = StringField('Tracking Service')
    tid = StringField('Tracking Service')
    submit = SubmitField('Tracking ID')


class Search(FlaskForm):
    search = StringField('Search')
    submit = SubmitField('Submit')


class Update(FlaskForm):
    idt = StringField('idt')
    mrp = IntegerField('MRP')
    srp = IntegerField('SRP')
    quantity = IntegerField('Quantity')
    submit = SubmitField('Submit')


class Contact(FlaskForm):
    mail = StringField('Email - ID')
    message = StringField('Message')


@app.context_processor
def base():
    form = Search()
    if current_user.is_authenticated:
        tqty = total_items(current_user.email)
    else:
        tqty = 0
    return dict(form = form, status=status(), total_qty = tqty)


@app.route("/")
@app.route("/home", methods=['GET', 'POST'])
def home():
    update = updates()
    update.reverse()
    return render_template('home.html', updates = update)


@app.route("/search", methods=['GET', 'POST'])
def search():
    form = Search()
    if form.validate_on_submit:
        search_data = form.search.data
        products = list(search_prod(search_data))
        search_data = f"You Searched for {search_data}"
        for i in products:
            for j in i:
                try:
                    tag = j.get("_id")
                    cqty = user_cart_prod(current_user.email, str(get_product(tag)['_id']))
                    j['cqty'] = cqty
                except:
                    j['cqty'] = 0
        cartx = []
        if current_user.is_authenticated:
            current = current_user.email
            set_cart(current)
            cart = get_cart(current_user.email)
            for i in cart:
                ut = get_product_id(i['_id'])
                ut['cqty'] = i['cqty']
                cartx.append(ut)
                for i in cart:
                    if request.method == 'POST':
                        quantity = request.form.get(f'quantity{cart.index(i)}')
                        if quantity is not None:
                            quantity = int(quantity)
                            if quantity != i['cqty']:
                                item = f"{quantity}{i['_id']}"
                                set_qty(current, item)
                                return redirect(url_for('home'))
        return render_template('products.html', lenproducts=len(products), products=products, cart = cartx, x = search_data)

    else:
        return render_template('home.html')


@app.route("/info", methods=['GET', 'POST'])
def info():
    form = Info()
    return render_template('info.html', form = form, t="info")


@app.route("/contact-us", methods=['GET', 'POST'])
def contact_us():
    return render_template('contact us.html')


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    form = Contact()
    if form.validate_on_submit:
        message = f"""
    From: {form.mail.data}
    Message: {form.message.data}
    """
        mail("granthbagadia2004@gmail.com", message)
        flash("Query Sent Successfully")
        return render_template('contact us.html')


@app.route('/sign-up/<x>', methods=['GET', 'POST'])
def signup(x):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            save_user(email)
            user = get_user(email)
            login_user(user)
            return redirect(url_for('add', x=x))
        except DuplicateKeyError:
            user = get_user(email)
            login_user(user)
            return redirect(url_for('add', x=x))
    return render_template('info.html', x=x, t="signup")


@app.route("/cart", methods=['GET', 'POST'])
def cart():
    try:
        current = current_user.email
        tamount = get_total(current)
        tqty = total_items(current)
        set_cart(current)
        cart = get_cart(current_user.email)
        x = []
        for i in cart:
            ut = get_product_id(i['_id'])
            ut['cqty'] = i['cqty']
            ut['total'] = i['cqty']*ut['srp']
            x.append(ut)
        if request.method == 'POST':
            for i in cart:
                quantity = request.form.get(f'quantity{cart.index(i)}')
                if quantity is not None:
                    quantity = int(quantity)
                    item = f"{quantity}{i['_id']}"
                    set_qty(current, item)
            x = []
            for i in get_cart(current_user.email):
                ut = get_product_id(i['_id'])
                ut['cqty'] = i['cqty']
                ut['total'] = int(i['cqty'])*int(ut['srp'])
                print("hey")
                x.append(ut)
            flash("Item Quantity Changed Successfully")
            tqty = total_items(current)
            tamount = get_total(current)
            return render_template('cart.html', current=current, cart = x, total_amount = tamount, total_qty = tqty)
        return render_template('cart.html', current=current, cart = x, total_amount = tamount, total_qty = tqty)
    except:
        return redirect(url_for('home'))


@app.route("/<x>", methods=['GET', 'POST'])
def products(x):
    print(x)
    if x in tags:
        products = list(all_products(x))
        for i in products:
            for j in i:
                try:
                    tag = j.get("_id")
                    cqty = user_cart_prod(current_user.email, str(get_product(tag)['_id']))
                    j['cqty'] = cqty
                except:
                    j['cqty'] = 0
        cartx = []
        if current_user.is_authenticated:
            current = current_user.email
            set_cart(current)
            cart = get_cart(current_user.email)
            for i in cart:
                ut = get_product_id(i['_id'])
                ut['cqty'] = i['cqty']
                cartx.append(ut)
                for i in cart:
                    if request.method == 'POST':
                        quantity = request.form.get(f'quantity{cart.index(i)}')
                        if quantity is not None:
                            quantity = int(quantity)
                            if quantity != i['cqty']:
                                item = f"{quantity}{i['_id']}"
                                set_qty(current, item)
                                return redirect(url_for('home'))
        return render_template('products.html', lenproducts=len(products), products=products, cart = cartx, x = x)
    elif x in prod_id():
        if current_user.is_authenticated:
            cqty = user_cart_prod(current_user.email, x)
            if request.method == 'POST':
               quantity = request.form.get('quantity')
               x = get_product(x).get('_id')
               quantity += str(x)
               return redirect(url_for('add', x=quantity))
            return render_template('item.html', product=get_product(x), cqty=cqty)
        else:
            if request.method == 'POST':
               quantity = request.form.get('quantity')
               x = get_product(x).get('_id')
               quantity += str(x)
               return redirect(url_for('signup', x=quantity))
            return render_template('item.html', product=get_product(x), cqty=1)
    else:
        return render_template('505.html')


@app.route("/add/<x>", methods=['GET', 'POST'])
def add(x):
    if current_user.is_authenticated:
        update_cart(current_user.email, x)
        flash("Item Added Successfully")
        return redirect(url_for('cart'))
    else:
        return redirect(url_for('signup', x=x))


@app.route("/pay", methods=['GET', 'POST'])
def pay():
    form = Info()
    if form.validate_on_submit:
        email = current_user.email
        name = form.name.data
        phone = form.phone.data
        address = form.address.data
        add_info(email, name, phone, address)
    return render_template('pay.html', email = email)


@app.route("/success", methods=['GET', 'POST'])
def success():
    email = current_user.email
    idt = bill(email)
    empty_cart(email)
    message = f"""From: From granthbagadia2004@gmail.com
    Subject: Order Placed Successfully!

    This is a confirmation for your order on Games-Trade India.
    Your Order ID is {idt}
    """
    mail(email, message)
    prod_qty(idt)
    flash("Order Placed Successfully!")
    return redirect(url_for('home'))


@app.route("/test", methods=['GET', 'POST'])
def test():
    return render_template('test.html')


@app.route("/home-admin", methods=['GET', 'POST'])
def home_admin():
    return render_template('home2.html')


@app.route("/new_product", methods=['GET', 'POST'])
def new_product():
    form = New()
    return render_template('new_product.html', products = all_prod(), form = form, message = "Hello There")


@app.route("/new_prod", methods=['GET', 'POST'])
def new_prod():
    form = New()
    try:
        if form.validate_on_submit:
            category = form.category.data
            name = form.name.data
            mrp = form.mrp.data
            srp = form.srp.data
            info = form.info.data
            quantity = form.quantity.data
            image = form.image.data
            if (category or name or quantity or mrp or srp or image or info) == "":
                message = "Invalid Details"
            else:
                message = save_product(category, name, quantity, mrp, srp, image, info)
            return render_template('new_product.html', products = all_prod(), form = form, message = message)
        else:
            return render_template('new_product.html', products = all_prod(), form = form, message = "Hello There")
    except:
        return render_template('new_product.html', products = all_prod(), form = form, message = "Hello There")


@app.route("/update_prod", methods=['GET', 'POST'])
def update_prod():
    form = Update()
    try:
        if form.validate_on_submit:
            idt = form.idt.data
            mrp = form.mrp.data
            srp = form.srp.data
            quantity = form.quantity.data
            update_product(idt, mrp, srp, quantity)
            return render_template('update_product.html', products = all_prod(), form = form)
        else:
            return render_template('update_product.html', products = all_prod(), form = form)
    except:
        return render_template('update_product.html', products = all_prod(), form = form)


@app.route("/add_track", methods=['GET', 'POST'])
def add_track():
    form = Track()
    try:
        if form.validate_on_submit:
            idt = form.idt.data
            ts = form.ts.data
            tid = form.tid.data
            ord_track(idt, ts, tid)
        return render_template('new_ord.html', orders = all_orders(), form = form, products = all_prod())
    except:
        return render_template('new_ord.html', orders = all_orders(), form = form, products = all_prod())


@app.route("/check_order", methods=['GET', 'POST'])
def check_order():
    return render_template('track_ord.html', orders = track_all(), products = all_prod())


@login_manager.user_loader
def load_user(email):
    return get_user(email)


if __name__ == '__main__':
    socketio.run(app, debug=True)