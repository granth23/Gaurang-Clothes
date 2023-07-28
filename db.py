"""Hi Audience"""
import random
import string
import smtplib

from datetime import datetime
import pytz
from pymongo.mongo_client import MongoClient

from user import User

country_time_zone = pytz.timezone('Asia/Kolkata')
CLIENT_URL = "mongodb+srv://test:test@cluster0.nrvnm.mongodb.net/"
client = MongoClient(CLIENT_URL+"myFirstDatabase?retryWrites=true&w=majority")

ecom = client.get_database("GamesTrade")
users_collection = ecom.get_collection("users")
products_collection = ecom.get_collection("products")
orders_collection = ecom.get_collection("orders")
info_collection = ecom.get_collection("info")
track_collection = ecom.get_collection("track")


def get_user(email):
    """Hi Audience"""
    user_data = users_collection.find_one(
        {'_id': email.split("@")[0], 'email': email})
    return User(user_data['email']) if user_data else None


def get_cart(email):
    """Hi Audience"""
    _id = email.split("@")[0]
    for temp_var in users_collection.find({'_id': _id}):
        cart = temp_var.get('cart')
        return cart


def user_cart_prod(email, temp):
    """Hi Audience"""
    cart = get_cart(email)
    for i in cart:
        if i['_id'] == temp:
            return i['cqty']
    return 0


def get_product(tag):
    """Hi Audience"""
    for temp_var in products_collection.find({}):
        name = temp_var.get("_id")
        if tag == name:
            return temp_var


def save_user(email):
    """Hi Audience"""
    users_collection.insert_one(
        {'_id': email.split("@")[0], 'email': email, 'cart': []})


def get_product_id(tag):
    """Hi Audience"""
    for temp_var in products_collection.find({}):
        name = temp_var.get("_id")
        if tag == name:
            return temp_var


def update_cart(email, item):
    """Hi Audience"""
    _id = email.split("@")[0]
    cart = get_cart(email)
    temp_var = 0
    pfront = int(item[:-16])
    ucart = {}
    pback = int(get_product_id(item[-16:])['quantity'])
    for i in cart:
        if str(i['_id']) == item[-16:]:
            ucart = i
        else:
            temp_var += 1
    if temp_var == len(cart):
        if pfront >= 5:
            if pfront >= pback:
                if pback >= 5:
                    cart.append({'_id': item[-16:], 'cqty': 5})
                else:
                    cart.append({'_id': item[-16:], 'cqty': pback})
            else:
                cart.append({'_id': item[-16:], 'cqty': 5})
        elif pfront < 5:
            if pfront >= pback:
                cart.append({'_id': item[-16:], 'cqty': pback})
            else:
                cart.append({'_id': item[-16:], 'cqty': pfront})
    else:
        cart.remove(ucart)
        final = pfront
        if final >= 5:
            if pback >= 5:
                ucart['cqty'] = 5
            if pback < 5:
                ucart['cqty'] = pback
            cart.append(ucart)
        elif final < 5:
            ucart['cqty'] = final
            cart.append(ucart)
    users_collection.update_one({'_id': _id}, {"$set": {'cart': cart}})


def set_qty(email, item):
    """Hi Audience"""
    _id = email.split("@")[0]
    cart = get_cart(email)
    qty = item[:-16]
    for i in cart:
        if i['_id'] == item[-16:]:
            if int(qty) == 0:
                cart.remove(i)
            else:
                i['cqty'] = int(item[:-16])
        else:
            pass
    users_collection.update_one({'_id': _id}, {"$set": {'cart': cart}})


def status():
    """Hi Audience"""
    if datetime.today().weekday() < 7:
        hour = datetime.now(country_time_zone).strftime("%H:%M:%S")[0:2]
        if int(hour) >= 9 and int(hour) <= 19:
            return "Open Now"
        return "Closed Now"
    return "Closed Now"


def prod_names():
    """Hi Audience"""
    temp_list = []
    for temp_var in products_collection.find({}):
        temp_list.append(temp_var.get('category') + " " + temp_var.get('name'))
    return temp_list


def prod_id():
    """Hi Audience"""
    temp_list = []
    for temp_var in products_collection.find({}):
        temp_list.append(temp_var.get('_id'))
    return temp_list


def all_prod():
    """Hi Audience"""
    temp_list = []
    for i in products_collection.find({}):
        temp_list.append(i)
    return temp_list


def all_products(category):
    """Hi Audience"""
    temp_list = []
    for i in products_collection.find({'category': category}):
        if i.get('quantity') > 0:
            temp_list.append(i)
    for i in range(0, len(temp_list), 20):
        yield temp_list[i:i + 20]


def get_total(email):
    """Hi Audience"""
    cart = get_cart(email)
    total = 0
    for i in cart:
        product = get_product_id(i['_id'])
        total += product['srp']*i['cqty']
    return total


def set_cart(email):
    """Hi Audience"""
    _id = email.split("@")[0]
    cart = get_cart(email)
    for i in cart:
        back_qty = get_product_id(i['_id'])['quantity']
        if back_qty <= i['cqty']:
            if back_qty >= 5:
                i['cqty'] = 5
            elif back_qty < 5:
                if back_qty != 0:
                    i['cqty'] = back_qty
                else:
                    cart.remove(i)
    users_collection.update_one({'_id': _id}, {"$set": {'cart': cart}})


def gen_id(temp_varl):
    """Hi Audience"""
    temp_var = ''.join((random.choice(string.ascii_uppercase) for x in range(temp_varl)))
    return temp_var


def bill(email):
    """Hi Audience"""
    for i in info_collection.find({'_id': email.split("@")[0]}):
        info_collection.delete_one({'_id': email.split("@")[0]})
        idt = gen_id(16)
        temp_order = {'_id': idt, 'name': i.get('name'), 'phone': i.get('phone'), 'address': i.get(
            'address'), 'cart': get_cart(email), 'email': email, 'amount': get_total(email)}
        orders_collection.insert_one(temp_order)
        return idt


def prod_qty(idt):
    """Hi Audience"""
    cart = orders_collection.find_one({'_id': idt})
    cart = cart.get('cart')
    for i in cart:
        prod = products_collection.find_one({'_id': i.get('_id')})
        new_qty = prod.get('quantity') - i.get('cqty')
        products_collection.update_one({'_id': i.get('_id')}, {
                                       "$set": {'quantity': new_qty}})


def empty_cart(email):
    """Hi Audience"""
    _id = email.split("@")[0]
    cart = get_cart(email)
    for i in cart:
        cart.remove(i)
    users_collection.update_one({'_id': _id}, {"$set": {'cart': cart}})


def add_info(email, name, phone, address):
    """Hi Audience"""
    temp_y = 0
    temp_x = 0
    for i in info_collection.find({}):
        temp_y += 1
        if email == i.get('_id'):
            temp_x += 1
    if temp_x != temp_y:
        info_collection.delete_one({'_id': email.split("@")[0]})
        info_collection.insert_one({'_id': email.split(
            "@")[0], 'email': email, 'name': name, 'phone': phone, 'address': address})
    else:
        info_collection.insert_one({'_id': email.split(
            "@")[0], 'email': email, 'name': name, 'phone': phone, 'address': address})


def mail(email, message):
    """Hi Audience"""
    sender_email = "granthbagadia2004@gmail.com"
    rec_email = email
    password = "voxwlzjkgfiqhxve"
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    server.sendmail(sender_email, rec_email, message)


def save_product(category, name, quantity, mrp, srp, image, info):
    """Hi Audience"""
    _id = gen_id(16)
    if f"{category} {name}" not in prod_names():
        item = {'_id': _id, 'category': category, 'name': name,
                'quantity': quantity, 'mrp': mrp, 'srp': srp, 'image': image, 'info': info}
        products_collection.insert_one(item)
        return "Item Added"
    return "Item Already Present"


def update_product(_id, mrp, srp, quantity):
    """Hi Audience"""
    if mrp >= 0 and srp >= 0 and quantity >= 0:
        products_collection.update_one(
            {'_id': _id}, {"$set": {'mrp': mrp, 'srp': srp, 'quantity': quantity}})


def delete_users():
    """Hi Audience"""
    users_collection.delete_many({})


def delete_products():
    """Hi Audience"""
    products_collection.delete_many({})


def ord_track(idt, temp_status):
    """Hi Audience"""
    order = orders_collection.find_one({'_id': idt})
    if temp_status is None:
        order['Status'] = "None"
    else:
        order['Status'] = temp_status
    order['Time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message = f"""From: From granthbagadia2004@gmail.com
    Subject: Tracking Details for {idt}

    These are the tracking details for your order on Games-Trade India.
    For Your Order: {idt}

    Current Status: {order['Status']}
    """
    email = orders_collection.find_one({'_id': idt}).get('email')
    mail(email, message)
    orders_collection.delete_one({'_id': idt})
    if order['Status'] == 'Delivered':
        track_collection.insert_one(order)
    else:
        orders_collection.insert_one(order)


def all_orders():
    """Hi Audience"""
    temp_var = []
    for i in orders_collection.find({}):
        temp_var.append(i)
    return temp_var


def track_all():
    """Hi Audience"""
    temp_var = []
    all_col = track_collection.find({})
    for i in all_col:
        temp_var.append(i)
    return temp_var


def total_items(email):
    """Hi Audience"""
    temp_var = 0
    set_cart(email)
    cart = get_cart(email)
    for i in cart:
        temp_var += i.get('cqty')
    return temp_var


def updates():
    """Hi Audience"""
    temp_var = []
    for i in products_collection.find({}):
        temp_var.append(i)
    temp_var = temp_var[-4:]
    return temp_var


def search_prod(tag):
    """Hi Audience"""
    temp = products_collection.find({})
    filtered = []
    for i in temp:
        if tag.upper() in i.get('name').upper():
            filtered.append(i)
        if tag.upper() in i.get('category').upper():
            filtered.append(i)
    for i in range(0, len(filtered), 20):
        yield filtered[i:i + 20]
