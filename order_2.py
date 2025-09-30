import secrets
from markupsafe import escape
from flask import Flask, render_template, redirect, url_for, request,jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_wtf import CSRFProtect
from flask_talisman import Talisman
from flask import request
import json
import requests as re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime as d
import time
import os
import random
from flask_wtf.csrf import generate_csrf
from upstash_redis import Redis



r = Redis(url="https://enormous-mastodon-11551.upstash.io", token="AS0fAAIncDJkYTk4MzFhMmY3Yjg0MDQ5YTBiY2Y1NDRlNzk0MTAzYXAyMTE1NTE")



# Define scope - what APIs you want to access
scope = ['https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive']

creds_json = os.environ.get("service-ambrosia-2")
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# Authorize the client
client = gspread.authorize(creds)

creds_json2 = os.environ.get("service-ambrosia-4")
creds_dict2 = json.loads(creds_json2)
creds2 = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# Authorize the client
client2 = gspread.authorize(creds)

service_accounts = ["client", "client2"]

# Open your Google Sheet by name
sheet_customer_cash = client.open('Customer Order').worksheet('table_cash')
sheet_customer_tng = client.open('Customer Order').worksheet('table_tng')


sheet_customer_cash2 = client2.open('Customer Order').worksheet('table_cash')
sheet_customer_tng2 = client2.open('Customer Order').worksheet('table_tng')

sheet_product = client.open('Official Product Database').worksheet('Products')  

sheet_product_two = client.open('Official Product Database').worksheet('Topping')




def load_data():
    global name_list
    global topping_list
    global product_topping_list
    global price_list
    global topping_price
    name_list = sheet_product.col_values(1)[1:]
    price_list = sheet_product.col_values(2)[1:]
    product_topping_list = sheet_product.col_values(3)[1:]
    topping_list = sheet_product.col_values(4)[1:]
    topping_price = sheet_product_two.get_all_values()
    print(name_list)
    print(topping_list)
    print(price_list)
    print(topping_price)

load_data()

def get_ipaddr():
    # If behind a proxy/load balancer, use the first IP in X-Forwarded-For
    if "X-Forwarded-For" in request.headers:
        # sometimes contains multiple IPs, take the first
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    # fallback to remote_addr
    return request.remote_addr

app = Flask(__name__)

def schedule_data_load():
    while True:
        load_data()
        time.sleep(60 * 60 * 12)

def sanitize_for_sheet(value):
    if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@'):
        return "'" + value
    return value



CORS(
    app,
    supports_credentials=True,
    origins=["https://index-autumn.onrender.com", "https://autumns-ambrosia-store.pages.dev","https://autumns-ambrosia-preorder.pages.dev"],
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

Talisman(app, content_security_policy=None, force_https=True)

limiter = Limiter(
    app=app,
    key_func=get_ipaddr,
    default_limits=["70 per hour"]
)

product_list = []

for x,y,z in zip(name_list,topping_list,price_list):
    product_list.append([x,y,float(z)])
    print(product_list)
    
app.secret_key = secrets.token_urlsafe(16)  # Required for CSRF token signing

app.config.update(
    SESSION_COOKIE_SECURE=True,   # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY=True, # Prevent JS access to cookies
    SESSION_COOKIE_SAMESITE='Lax' # Prevent CSRF via cookies
)


csrf = CSRFProtect(app)

#First (Get token)
@csrf.exempt
@app.route("/token")
def get_token():
    token = secrets.token_urlsafe(16)
    r.json.set(token, "$", {"initialized": True})
    r.expire(token, 730)
    print(token,flush=True)
    """
    users_tokens[token] = {}
    users_tokens[token]["expire_time"] = time.time() + 60*15
    """
    return jsonify({"token": token})

#Token received. Then, frontend sends the order and store the data in memory dictionary 
@csrf.exempt
@limiter.limit("50 per hour")
@app.route("/submit_order", methods=["POST"])
def submit_order():
    token = request.args.get("token")
    if not token or not r.exists(token):
        print("Error")
        return jsonify({"error": "Invalid token"}), 401

    order_data = request.json.get("order_items")  # frontend sends entire order
    if not order_data:
        print("Error")
        return jsonify({"error": "Order data required"}), 400
    
    username = request.json.get("username")  # frontend sends entire order
    if not username:
        print("Error")
        return jsonify({"error": "Username required"}), 400

    # Save final order for this token
    r.json.set(token, "$", {"order": order_data, "customer": username})
    """
    users_tokens[token]["order"] = order_data
    users_tokens[token]["customer"] = username
    """

    return jsonify({"message": "success"})

#After receive success messages, then show the GET 
@csrf.exempt
@app.route("/confirm",methods=["GET","POST"])
@limiter.limit("110 per hour")
def confirm():
    token = request.args.get("token")
    if not token or not r.exists(token):
        return jsonify({"error": "Invalid token"}), 401
    
    orderdata = r.json.get(token, "$")
    orderdata = orderdata[0]

    order_summary = "\n\n".join(
        f"{item[1]} {item[0]} with {item[2]}" for item in orderdata["order"]
    )

    total = 0

    for thing in orderdata["order"]:
                 print(thing[0])
                 thing[1] = int(thing[1])
                 print(thing[1])
                 print(thing[2])

                 if thing[0] not in name_list:
                     print(f"name")
                     return f"<h4>We do not have {escape(thing[0])} in our menu</h4>"
                 else:
                     name_index = name_list.index(thing[0])
                 
                 if thing[1] > 40:
                     print(thing[1])
                     return f"<h4>Too many</h4>"
                 
                 print("Run")

                 for x in product_list:
                         if thing[0] == x[0]:
                             per_price = x[2]
                             total_price = per_price*thing[1]
                             break
              
                 if thing[2] in [t.strip() for t in product_topping_list[name_index].split(",")]: 
                     for y in topping_price:
                         if thing[2] == y[0]:
                           extra_topping_price = int(y[1])*thing[1]
                           total_price += extra_topping_price
                           print(product_topping_list[name_index].split(", "))
                           print(total_price)
                           thing.append(total_price)
                           total += total_price
                           print(f"Amount: {total}")
                         else:
                                print("Failed")
                 else:
                        return f"<h4>We do not have {escape(thing[2])} in our topping menu</h4>"
    
    print("Running")
    orderdata["total"] = total
            
    print("TOTAL:", total)


    if request.method == "POST":
                email = request.form.get("user_email")
                userclass = request.form.get("user_class")
                transaction_name = request.form.get("transaction_name")
                payment_method = request.form.get("payment_method")
                phone_num = request.form.get("user_phone")
                if email is None:
                        return "Please provide your email."
                if payment_method is None:
                        return "<h4>Please choose a payment method.</h4>"
                if userclass is None:
                        return "Please provide details about the class."
                if phone_num is None:
                        phone_num = 'None'
                elif payment_method == "cash":
                        try:
                           if random.choice(service_accounts) == service_accounts[0]: 
                             sheet_customer_cash.append_row([sanitize_for_sheet(orderdata["customer"]),sanitize_for_sheet(order_summary),sanitize_for_sheet(email),sanitize_for_sheet(userclass),sanitize_for_sheet(phone_num),total])
                           else:
                             sheet_customer_cash2.append_row([sanitize_for_sheet(orderdata["customer"]),sanitize_for_sheet(order_summary),sanitize_for_sheet(email),sanitize_for_sheet(userclass),sanitize_for_sheet(phone_num),total])

                           email_data = {"order": orderdata["order"], "email": email}
                           response = re.post("https://script.google.com/macros/s/AKfycbxqeU1Xxzb4ktlnu1BoSvjYk0O3uwnCAP3UVB4SH6kPX3BZMPWQFTMsXGnSadTavmuw/exec", json=email_data, headers={'Content-Type':'application/json'})
                           print(response.status_code)
                        except Exception as e:
                            return f"Error in confirm: {str(e)}" 
                else:
                        if payment_method == "TNG" and transaction_name is not None:
                            try:
                             if random.choice(service_accounts) == service_accounts[0]:
                                  sheet_customer_tng.append_row([sanitize_for_sheet(orderdata["customer"]),sanitize_for_sheet(order_summary),sanitize_for_sheet(email),sanitize_for_sheet(userclass),sanitize_for_sheet(phone_num), sanitize_for_sheet(transaction_name), total])
                             else: 
                                   sheet2_customer_tng.append_row([sanitize_for_sheet(orderdata["customer"]),sanitize_for_sheet(order_summary),sanitize_for_sheet(email),sanitize_for_sheet(userclass),sanitize_for_sheet(phone_num), sanitize_for_sheet(transaction_name), total])
                                     
                             email_data = {"order": orderdata["order"], "email": email}
                             response = re.post("https://script.google.com/macros/s/AKfycbxqeU1Xxzb4ktlnu1BoSvjYk0O3uwnCAP3UVB4SH6kPX3BZMPWQFTMsXGnSadTavmuw/exec", json=email_data, headers={'Content-Type':'application/json'})
                             print(response.status_code)
                            except Exception as e:
                              return f"Error in confirm: {str(e)}"
                        else:
                            return "No transaction name given"
                return render_template("payment_successful.html")

    csrf_token = generate_csrf()
    return render_template("confirm_order.html",total=str(orderdata["total"]),ordered=orderdata["order"], csrf_token=csrf_token)

        
@app.route("/gspread_error")
@limiter.limit("50 per hour")
def gspread_error():
    return "Error"

@app.route("/wake")
def wake_up():
   return "w"

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")
