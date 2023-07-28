"""Hi Audience"""
from pymongo.errors import DuplicateKeyError
from flask_login import LoginManager, login_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from flask_socketio import SocketIO
from flask import Flask, render_template, request, redirect, url_for, flash

from db import get_user, save_user, update_cart, get_cart, set_qty
from db import user_cart_prod, set_cart, status, add_info
from db import all_products, get_product, get_product_id
from db import bill, mail, prod_qty, get_total, prod_id, search_prod
from db import all_prod, update_product, save_product, updates
from db import all_orders, ord_track, track_all, empty_cart, total_items

app = Flask(__name__)
app.secret_key = "granthbagadiagranthbagadia"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


tags = ['PS4', 'PS5', 'XBOX X', 'XBOX-1', 'SURFACE', 'ACCESSORIES', 'NINTENDO']


class New(FlaskForm):
    """Hi Audience"""
    name = StringField('name')
    category = StringField('category')
    image = StringField('image')
    info = StringField('info')
    mrp = IntegerField('MRP')
    srp = IntegerField('SRP')
    quantity = IntegerField('Quantity')
    submit = SubmitField('Submit')


class Info(FlaskForm):
    """Hi Audience"""
    name = StringField('Name')
    phone = StringField('Phone')
    address = StringField('Address')
    submit = SubmitField('Submit')


class Track(FlaskForm):
    """Hi Audience"""
    idt = StringField('Order ID')
    ts = StringField('Tracking Service')
    tid = StringField('Tracking Service')
    submit = SubmitField('Tracking ID')


class Search(FlaskForm):
    """Hi Audience"""
    search = StringField('Search')
    submit = SubmitField('Submit')


class Update(FlaskForm):
    """Hi Audience"""
    idt = StringField('idt')
    mrp = IntegerField('MRP')
    srp = IntegerField('SRP')
    quantity = IntegerField('Quantity')
    submit = SubmitField('Submit')


class Contact(FlaskForm):
    """Hi Audience"""
    mail = StringField('Email - ID')
    message = StringField('Message')


class TrackOrder(FlaskForm):
    """Hi Audience"""
    order_id = StringField('Order ID')


@app.context_processor
def base():
    """Hi Audience"""
    form = Search()
    if current_user.is_authenticated:
        tqty = total_items(current_user.email)
    else:
        tqty = 0
    return dict(form=form, status=status(), total_qty=tqty)


@app.route("/")
@app.route("/home", methods=['GET', 'POST'])
def home():
    """Hi Audience"""
    update = updates()
    update.reverse()
    return render_template('home.html', updates=update)


@app.route("/search", methods=['GET', 'POST'])
def search():
    """Hi Audience"""
    form = Search()
    if form.validate_on_submit:
        search_data = form.search.data
        temp_products = list(search_prod(search_data))
        search_data = f"You Searched for {search_data}"
        for i in temp_products:
            for j in i:
                try:
                    tag = j.get("_id")
                    cqty = user_cart_prod(
                        current_user.email, str(get_product(tag)['_id']))
                    j['cqty'] = cqty
                except RuntimeError:
                    j['cqty'] = 0
        temp_cartx = []
        if current_user.is_authenticated:
            current = current_user.email
            set_cart(current)
            temp_cart = get_cart(current_user.email)
            for i in temp_cart:
                temp_ut = get_product_id(i['_id'])
                temp_ut['cqty'] = i['cqty']
                temp_cartx.append(temp_ut)
                for i in temp_cart:
                    if request.method == 'POST':
                        quantity = request.form.get(
                            f'quantity{temp_cart.index(i)}')
                        if quantity is not None:
                            quantity = int(quantity)
                            if quantity != i['cqty']:
                                item = f"{quantity}{i['_id']}"
                                set_qty(current, item)
                                return redirect(url_for('home'))
        return render_template('products.html', lenproducts=len(products),
            products=products, cart=temp_cartx, x=search_data)
    else:
        return render_template('home.html')


@app.route("/info", methods=['GET', 'POST'])
def info():
    """Hi Audience"""
    form = Info()
    return render_template('info.html', form=form, t="info")


@app.route("/contact-us", methods=['GET', 'POST'])
def contact_us():
    """Hi Audience"""
    return render_template('contact us.html')


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    """Hi Audience"""
    form = Contact()
    if form.validate_on_submit:
        message = f"""
    From: {form.mail.data}
    Message: {form.message.data}
    """
        mail("granthbagadia2004@gmail.com", message)
        flash("Query Sent Successfully")
        return render_template('contact us.html')


@app.route('/sign-up/<temp_x>', methods=['GET', 'POST'])
def signup(temp_x):
    """Hi Audience"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            save_user(email)
            user = get_user(email)
            login_user(user)
            return redirect(url_for('add', x=temp_x))
        except DuplicateKeyError:
            user = get_user(email)
            login_user(user)
            return redirect(url_for('add', x=temp_x))
    return render_template('info.html', x=temp_x, t="signup")


@app.route("/cart", methods=['GET', 'POST'])
def cart():
    """Hi Audience"""
    try:
        current = current_user.email
        tamount = get_total(current)
        tqty = total_items(current)
        set_cart(current)
        temp_cart = get_cart(current_user.email)
        temp_x = []
        for i in temp_cart:
            temp_ut = get_product_id(i['_id'])
            temp_ut['cqty'] = i['cqty']
            temp_ut['total'] = i['cqty']*temp_ut['srp']
            temp_x.append(temp_ut)
        if request.method == 'POST':
            for i in temp_cart:
                quantity = request.form.get(f'quantity{temp_cart.index(i)}')
                if quantity is not None:
                    quantity = int(quantity)
                    item = f"{quantity}{i['_id']}"
                    set_qty(current, item)
            temp_x = []
            for i in get_cart(current_user.email):
                temp_ut = get_product_id(i['_id'])
                temp_ut['cqty'] = i['cqty']
                temp_ut['total'] = int(i['cqty'])*int(temp_ut['srp'])
                temp_x.append(temp_ut)
            flash("Item Quantity Changed Successfully")
            tqty = total_items(current)
            tamount = get_total(current)
            return render_template('cart.html', current=current, cart=temp_x,
                total_amount=tamount, total_qty=tqty)
        return render_template('cart.html', current=current, cart=temp_x,
            total_amount=tamount, total_qty=tqty)
    except RuntimeError:
        return redirect(url_for('home'))


@app.route("/<temp_x>", methods=['GET', 'POST'])
def products(temp_x):
    """Hi Audience"""
    if temp_x in tags:
        temp_products = list(all_products(temp_x))
        for i in temp_products:
            for j in i:
                try:
                    tag = j.get("_id")
                    cqty = user_cart_prod(
                        current_user.email, str(get_product(tag)['_id']))
                    j['cqty'] = cqty
                except RuntimeError:
                    j['cqty'] = 0
        cartx = []
        if current_user.is_authenticated:
            current = current_user.email
            set_cart(current)
            temp_cart = get_cart(current_user.email)
            for i in temp_cart:
                temp_ut = get_product_id(i['_id'])
                temp_ut['cqty'] = i['cqty']
                cartx.append(temp_ut)
                for i in temp_cart:
                    if request.method == 'POST':
                        quantity = request.form.get(f'quantity{temp_cart.index(i)}')
                        if quantity is not None:
                            quantity = int(quantity)
                            if quantity != i['cqty']:
                                item = f"{quantity}{i['_id']}"
                                set_qty(current, item)
                                return redirect(url_for('home'))
        return render_template('products.html', lenproducts=len(products),
            products=products, cart=cartx, x=temp_x)
    elif temp_x in prod_id():
        if current_user.is_authenticated:
            cqty = user_cart_prod(current_user.email, temp_x)
            if request.method == 'POST':
                quantity = request.form.get('quantity')
                temp_x = get_product(temp_x).get('_id')
                quantity += str(temp_x)
                return redirect(url_for('add', x=quantity))
            return render_template('item.html', product=get_product(temp_x), cqty=cqty)
        else:
            if request.method == 'POST':
                quantity = request.form.get('quantity')
                temp_x = get_product(temp_x).get('_id')
                quantity += str(temp_x)
                return redirect(url_for('signup', x=quantity))
            return render_template('item.html', product=get_product(temp_x), cqty=1)
    return render_template('505.html')


@app.route("/add/<temp_x>", methods=['GET', 'POST'])
def add(temp_x):
    """Hi Audience"""
    if current_user.is_authenticated:
        update_cart(current_user.email, temp_x)
        flash("Item Added Successfully")
        return redirect(url_for('cart'))
    return redirect(url_for('signup', x=temp_x))


@app.route("/pay", methods=['GET', 'POST'])
def pay():
    """Hi Audience"""
    form = Info()
    if form.validate_on_submit:
        email = current_user.email
        name = form.name.data
        phone = form.phone.data
        address = form.address.data
        add_info(email, name, phone, address)
    return render_template('pay.html', email=email)


@app.route("/success", methods=['GET', 'POST'])
def success():
    """Hi Audience"""
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
    """Hi Audience"""
    return render_template('test.html')


@app.route("/home-admin", methods=['GET', 'POST'])
def home_admin():
    """Hi Audience"""
    return render_template('home2.html')


@app.route("/new_product", methods=['GET', 'POST'])
def new_product():
    """Hi Audience"""
    form = New()
    return render_template('new_product.html', products=all_prod(),
        form=form, message="Hello There")


@app.route("/new_prod", methods=['GET', 'POST'])
def new_prod():
    """Hi Audience"""
    form = New()
    if form.validate_on_submit:
        category = form.category.data
        name = form.name.data
        mrp = form.mrp.data
        srp = form.srp.data
        temp_info = form.info.data
        quantity = form.quantity.data
        image = form.image.data
        if (category or name or quantity or mrp or srp or image or temp_info) == "":
            message = "Invalid Details"
        else:
            message = save_product(
                category, name, quantity, mrp, srp, image, temp_info)
        return render_template('new_product.html', products=all_prod(), form=form, message=message)
    return render_template('new_product.html', products=all_prod(),
        form=form, message="Hello There")


@app.route("/update_prod", methods=['GET', 'POST'])
def update_prod():
    """Hi Audience"""
    form = Update()
    if form.validate_on_submit:
        idt = form.idt.data
        mrp = form.mrp.data
        srp = form.srp.data
        quantity = form.quantity.data
        update_product(idt, mrp, srp, quantity)
        return render_template('update_product.html', products=all_prod(), form=form)
    return render_template('update_product.html', products=all_prod(), form=form)


@app.route("/add_track", methods=['GET', 'POST'])
def add_track():
    """Hi Audience"""
    form = Track()
    if form.validate_on_submit:
        idt = form.idt.data
        temp_status = form.status.data
        ord_track(idt, temp_status)
    return render_template('new_ord.html', orders=all_orders(), form=form, products=all_prod())


@app.route("/check_order", methods=['GET', 'POST'])
def check_order():
    """Hi Audience"""
    return render_template('check_order.html', orders=track_all(), products=all_prod())


@app.route("/track_order", methods=['GET', 'POST'])
def track_order():
    """Hi Audience"""
    orders = all_orders()
    form = TrackOrder()
    if form.validate_on_submit:
        order_id = form.order_id.data
        for i in orders:
            if i['_id'] == order_id:
                return render_template('track_order.html', order=i, products=all_prod(), stat=1)
    return render_template('track_order.html', stat=0)


@login_manager.user_loader
def load_user(email):
    """Hi Audience"""
    return get_user(email)


if __name__ == '__main__':
    socketio.run(app, debug=True)
