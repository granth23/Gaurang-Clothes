from datetime import datetime
import pytz
from pymongo.mongo_client import MongoClient

from user import User
import random
import string
import smtplib

country_time_zone = pytz.timezone('Asia/Kolkata')
"mongodb+srv://test:test@cluster0.nrvnm.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient("mongodb+srv://test:test@cluster0.nrvnm.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

ecom = client.get_database("GamesTrade")
users_collection = ecom.get_collection("users")
products_collection = ecom.get_collection("products")
orders_collection = ecom.get_collection("orders")
info_collection = ecom.get_collection("info")
track_collection = ecom.get_collection("track")


def get_user(email):
    user_data = users_collection.find_one({'_id': email.split("@")[0], 'email': email})
    return User(user_data['email']) if user_data else None


def get_cart(email):
    _id = email.split("@")[0]
    for x in users_collection.find({'_id': _id}):
        cart = x.get('cart')
        return cart


def user_cart_prod(email, x):
    cart = get_cart(email)
    for i in cart:
        if i['_id'] == x:
            return i['cqty']
    else:
        return 0


def get_product(tag):
    for x in products_collection.find({}):
        name = x.get("_id")
        if tag == name:
            return x


def save_user(email):
    users_collection.insert_one({'_id': email.split("@")[0], 'email': email, 'cart': []})


def get_product_id(tag):
    for x in products_collection.find({}):
        name = x.get("_id")
        if tag == name:
            return x


def update_cart(email, item):
    _id = email.split("@")[0]
    cart = get_cart(email)
    r = 0
    pfront = int(item[:-16])
    ucart = {}
    pback = int(get_product_id(item[-16:])['quantity'])
    for i in cart:
        if str(i['_id']) == item[-16:]:
            ucart = i
        else:
            r += 1
    if r == len(cart):
        if pfront >= 5:
            if pfront >= pback:
                if pback >= 5:
                    cart.append({'_id': item[-16:], 'cqty' : 5})
                else:
                    cart.append({'_id': item[-16:], 'cqty' : pback})
            else:
                cart.append({'_id': item[-16:], 'cqty' : 5})
        elif pfront < 5:
            if pfront >= pback:
                cart.append({'_id': item[-16:], 'cqty' : pback})
            else:
                cart.append({'_id': item[-16:], 'cqty' : pfront})
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
    users_collection.update_one({'_id': _id}, { "$set": { 'cart': cart}})


def set_qty(email, item):
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
    users_collection.update_one({'_id': _id}, { "$set": { 'cart': cart}})


def status():
    if datetime.today().weekday() < 7:
        hour = datetime.now(country_time_zone).strftime("%H:%M:%S")[0:2]
        if int(hour) >= 9 and int(hour) <= 19:
            return "Open Now"
        else:
            return "Closed Now"
    else:
        return "Closed Now"


def prod_names():
    a = []
    for x in products_collection.find({}):
        a.append(x.get('category') + " " + x.get('name'))
    return a


def prod_id():
    a = []
    for x in products_collection.find({}):
        a.append(x.get('_id'))
    return a

def all_prod():
    a = []
    for i in products_collection.find({}):
        a.append(i)
    return a


def all_products(category):
    l = []
    for i in products_collection.find({'category': category}):
        if i.get('quantity') > 0:
            l.append(i)
    for i in range(0, len(l), 20):
        yield l[i:i + 20]


def get_total(email):
    cart = get_cart(email)
    total = 0
    for i in cart:
        product = get_product_id(i['_id'])
        total += product['srp']*i['cqty']
    return total


def set_cart(email):
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
    users_collection.update_one({'_id': _id}, { "$set": { 'cart': cart}})


def id(l):
    r = ''.join((random.choice(string.ascii_uppercase) for x in range(l)))
    return r


def bill(email):
    for i in info_collection.find({'_id' : email.split("@")[0]}):
        info_collection.delete_one({'_id' : email.split("@")[0]})
        idt = id(16)
        orders_collection.insert_one({'_id': idt, 'name' : i.get('name'), 'phone' : i.get('phone'), 'address': i.get('address'), 'cart': get_cart(email), 'email': email, 'amount': get_total(email)})
        return idt


def prod_qty(idt):
    cart = orders_collection.find_one({'_id' : idt})
    cart = cart.get('cart')
    for i in cart:
        prod = products_collection.find_one({'_id' : i.get('_id')})
        new_qty = prod.get('quantity') - i.get('cqty')
        products_collection.update_one({'_id' : i.get('_id')}, { "$set": { 'quantity': new_qty}})


def empty_cart(email):
    _id = email.split("@")[0]
    cart = get_cart(email)
    for i in cart:
        cart.remove(i)
    users_collection.update_one({'_id': _id}, { "$set": { 'cart': cart}})


def add_info(email, name, phone, address):
    y = 0
    x = 0

    for i in info_collection.find({}):
        y += 1
        if email == i.get('_id'):
            x += 1
    if x != y:
        info_collection.delete_one({'_id' : email.split("@")[0]})
        info_collection.insert_one({'_id': email.split("@")[0], 'email': email, 'name': name, 'phone': phone, 'address': address})
    else:
        info_collection.insert_one({'_id': email.split("@")[0], 'email': email, 'name': name, 'phone': phone, 'address': address})


def mail(email, message):
    sender_email = "granthbagadia2004@gmail.com"
    rec_email = email
    password = "vhvdnipfduglxqka"
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    server.sendmail(sender_email, rec_email, message)


def save_product(category, name, quantity, mrp, srp, image, info):
    _id = id(16)
    if f"{category} {name}" not in prod_names():
        products_collection.insert_one({'_id': _id, 'category': category, 'name': name, 'quantity': quantity, 'mrp': mrp, 'srp': srp, 'image': image, 'info': info})
        return "Item Added"
    else:
        return "Item Already Present"


def update_product(_id, mrp, srp, quantity):
    if mrp >= 0 and srp >= 0 and quantity >= 0:
        products_collection.update_one({'_id' : _id}, { "$set": { 'mrp': mrp, 'srp': srp, 'quantity' : quantity}})


def delete_users():
    users_collection.delete_many({})


def delete_products():
    products_collection.delete_many({})


def delete_users():
    users_collection.delete_many({})


def delete_products():
    products_collection.delete_many({})


def ord_track(idt, name , tid):
    order = orders_collection.find_one({'_id' : idt})
    order['Service'] = name
    order['Tracking ID'] = tid
    order['Time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message = f"""From: From granthbagadia2004@gmail.com
    Subject: Tracking Details for {idt}

    These are the tracking details for your order on Games-Trade India.
    For Your Order: {idt}

    The Tracking Service is: {name}
    The Tracking ID is: {tid}
    """
    email = orders_collection.find_one({'_id': idt}).get('email')
    mail(email, message)
    track_collection.insert_one(order)
    orders_collection.delete_one({'_id' : idt})


def all_orders():
    a = []
    for i in orders_collection.find({}):
        a.append(i)
    return a


def track_all():
    a = []
    all = track_collection.find({})
    for i in all:
        a.append(i)
    return a


def total_items(email):
    x = 0
    set_cart(email)
    cart = get_cart(email)
    for i in cart:
        x += i.get('cqty')
    return x


def updates():
    a = []
    for i in products_collection.find({}):
        a.append(i)
    a = a[-4:]
    return a


def search_prod(tag):
    all_prod = products_collection.find({})
    filtered = []
    for i in all_prod:
        if tag.upper() in i.get('name').upper():
            filtered.append(i)
        if tag.upper() in i.get('category').upper():
            filtered.append(i)
    for i in range(0, len(filtered), 20):
        yield filtered[i:i + 20]

