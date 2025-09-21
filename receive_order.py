from flask import Flask, render_template_string, redirect, url_for, request,session
from flask_cors import CORS
#from flask_limiter import Limiter
#from flask_limiter.util import get_remote_address
from flask_session import Session
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime as d
import time
import os
import threading


# Define scope - what APIs you want to access
scope = ['https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive']

creds_json = os.environ.get("GOOGLE_CREDS_JSON")
creds_dict = json.loads(creds_json)

# Load your service account credentials JSON file
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)



# Authorize the client
client = gspread.authorize(creds)


# Open your Google Sheet by name
sheet_customer = client.open('Customer_order').sheet1

sheet_product = client.open('Product').sheet1  

sheet_product_two = client.open('Product').worksheet('Sheet2')


def write_order(order,customer):
    try:
     order_json = json.dumps(order,indent=4)
     print(order_json)
     sheet_customer.append_row([customer,order_json])
    except:
        return redirect (url_for("gspread_error"))


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

app = Flask(__name__)

def schedule_data_load():
    while True:
        load_data()
        time.sleep(60 * 60 * 12)

# Start background thread
threading.Thread(target=schedule_data_load, daemon=True).start()

app.config.update(
    SECRET_KEY='something_secure_and_secret',
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
    SESSION_TYPE='filesystem'  # ← This makes it truly server-side
)

CORS(
    app,
    supports_credentials=True,
    origins=["https://autumn-ambrosia.pages.dev"],
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

Session(app)
"""
limiter = Limiter(
    get_remote_address,
    app=app
)
"""
product_list = []

for x,y,z in zip(name_list,topping_list,price_list):
    product_list.append([x,y,float(z)])
    print(product_list)

@app.route("/", methods=["GET","POST"])
#@limiter.limit("4 per minute")
#@limiter.limit("9 per hour")
def order_view():
      print("SESSION ID:", request.cookies.get("session"))
      if request.method == "POST":
        session.clear()
        if request.is_json:
         session["receive"] = dict(request.get_json())
         receive = session["receive"]
         print(receive)
         session["order_items"] = receive.get("order_items")
         order_items = session["order_items"]
         session["customer"] = receive.get("username")
         session["order_json"] = json.dumps(order_items,indent=4)
         order_json = session["order_json"]
         print(order_json)

         session["ordered"] = []
         total = 0

         for x in order_items:
                 session["name"] = x[0]
                 name = session["name"]
                 print(name)
                 session["quantity"] = int(x[1])
                 quantity = session["quantity"]
                 print(quantity)
                 session["topping"] = x[2]
                 topping = session["topping"]
                 print(topping)
                 place = []

                 if name not in name_list:
                     print(f"name")
                     return f"We do not have {name} in our menu"
                 else:
                     session["name_index"] = name_list.index(name)
                 
                 if quantity > 40:
                     print(quantity)
                     return f"Too many"
                 
                 print("Run")
                 place.append(name)
                 place.append(quantity)
                 place.append(topping)
                 print(f"place: {place}")

                 for x in product_list:
                         if name == x[0]:
                             session["per_price"] = x[2]
                             per_price = session["per_price"]
                             session["total_price"] = per_price*quantity
                             total_price = session["total_price"] 
                             break

                 print("TOPPING PRICE LIST:", topping_price)
                 
                 if "total" not in session:
                      session["total"] = 0
                      session["total"] += total_price
                         
                 if session["topping"] in product_topping_list[session["name_index"]].split(", "): 
                     for y in topping_price:
                         if session["topping"] == y[0]:
                           session["topping_price"] = int(y[1])*quantity
                           total_price += session["topping_price"]
                           print(product_topping_list[session["name_index"]].split(", "))
                           print(total_price)
                           place.append(total_price)
                           session["total"] += total_price
                           print(f"Amount: {session["total"]}")
                         else:
                                print("Failed")
                 else:
                        return f"We do not have {session["topping"]} in our topping menu"
                 session["ordered"].append(place)
         print("Running")
         print("ORDERED:", session.get("ordered"))
         print("TOTAL:", session.get("total"))
         return "Success" , 200
      return "Bad request"
        
@app.route("/confirm",methods=["GET","POST"])
#@limiter.limit("4 per minute")
#@limiter.limit("9 per hour")
def confirm():
    print("SESSION ID:", request.cookies.get("session"))
    total = session.get("total",0)
    ordered = session.get("ordered",[])
    print(total)
    print(ordered)

    if request.method == "POST":
                receive = session.get("receive")
                customer = session.get("customer")
                session.clear()
                session["receive"] = receive
                session["customer"] = customer
                session["email"] = request.form.get("user_email")
                session["transaction_name"] = request.form.get("transaction_name")
                session["payment_method"] = request.form.get("payment_method")
                if session.get("email", None) is None:
                        return "Please provide your email."
                if session.get("payment_method", None) is None:
                        return "Please choose a payment method."
                elif session.get("payment_method", None) == "cash":
                        try:
                           order_dict = session["receive"]
                           order_dict["Email"] = session["email"]
                           order_dict["Payment_Method"] = session["payment_method"]
                           order_json = json.dumps(order_dict,indent=4)
                           print(order_json)
                           sheet_customer.append_row([session["customer"],order_json])
                        except Exception as e:
                            print(f"Error in confirm: {str(e)}")
                            return redirect(url_for("gspread_error"))         
                else:
                        if session.get("payment_method", "") == "TNG" and session.get("transaction_name" , None) is not None:
                            try:
                             order_dict = session["receive"]
                             order_dict["Email"] = session["email"]
                             order_dict["Payment_Method"] = session["payment_method"]
                             order_dict["Transaction_Name"] = session["transaction_name"]
                             order_json = json.dumps(order_dict,indent=4)
                             print(order_json)
                             sheet_customer.append_row([session["customer"],order_json])
                            except Exception as e:
                              print(f"Error in confirm: {str(e)}")
                              return redirect(url_for("gspread_error"))    
                        else:
                            return "No transaction name given"
                return render_template_string("""
 <!--Payment Successful-->
<!DOCTYPE html>
<html>
  <body>
    <picture>
    <h1>Successful!</h1>
      <source media="(max-width: 600px)" srcset="https://cdni.iconscout.com/illustration/premium/thumb/mobile-card-payment-successful-illustration-download-in-svg-png-gif-file-formats--through-by-smart-phone-cashless-trasaction-retail-shopping-pack-e-commerce-illustrations-4841252.png">
     <img src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTZkb3I4ZXo4aDMxbWNxM3h6NG9zOGVvNHRvMWRrZWJvZjhtb3ppbCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/yeYaI0wAgWDKjZhHY5/giphy.gif">
    </picture>
    
  </body>
<style>
img {
      width: 100%;
    }
    h1 {
      color: green;
      display: block;
        text-align: center;  
    }
  </style>
</html>
""")

    return render_template_string("""
    <!DOCTYPE html>
<html>
  <head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      #top_bar {
        margin: 0;
        width: 100%;
        overflow: hidden;
        background-color: black;
        color: white;
        padding: 10px 0;
      }

      #left {
        float: left;
      }

      #right {
        float: right;
      }

      .top_lists {
        list-style-type: none;
        font-size: 22px;
        padding: 0 20px;
      }

      #up {
        width: 100%;
        margin: 0;
        width: 100%;
        overflow: hidden;
        background-color: rgb(0, 144, 254);
        padding: 50px 0;
      }
      #order_submit {
        border: 2px solid black;
      }
      
      #nav {
        border: 5px solid;
        border-image: linear-gradient(to right,red,orange,yellow,green,blue,purple);
        border-image-slice: 1;
      }
      
      #down {
        width: 100%;
        margin: 0;
        width: 100%;
        overflow: hidden;
        background-color: rgb(0, 144, 254);
        padding: 30px 0;
      }
      
      button {
        float: right;
        background-color: black;
        color: white;
        padding: 15px;
        font-size: 16px;
        border: 2px solid black;
        border-radius: 5px;
        margin: 3% 50%;
      }
      
      fieldset {
        width: 350px;
        margin: auto;
        margin-top: 20px 10px;
        box-shadow: 5px 5px 5px grey;
      }
      
      #logo {
        width: 50px;
        height: 35px;
      }
      
      .ordered_items {
        box-shadow: 5px 5px 5px grey;
        border: 2px solid black;
        border-radius: 5px;
        width: 270px;
        margin-left: 70px;
        flex-shrink: 0;
      }
      
      #template_ordered {
        overflow-x: auto;
        display: flex;
        flex-direction: row;
      }
      
      #order_title {
        margin-left: 10px;
      }
      
      #confirm {
        margin-left: 10px;
      }
      label {
        margin-left: 6px;
        font-size: 18px;
      }
      
      .ordered_label {
        margin-left: 7px;
      }
      
      #image {
        width: 400px;
        height: 400px;
      }
                                       
      #total {
        margin-left: 10px;
      }

      .input_form {
        display: inline-block;
        margin-right: 15px;
      }

      .input_text {
         border: 0.8px solid black;
         width: 5em;
      }
    </style>
  </head>
  <body>
    <div id="nav">
      <ul id="top_bar">
        <li class="top_lists" id="left">Company name</li>
        <img src="https://www.freepnglogos.com/uploads/company-logo-png/company-logo-transparent-png-19.png" id="logo">
        <li class="top_lists" id="right">Order Review</li>
      </ul>
    </div>
    
      <h2>Thank you for purchasing our products.</h2>
      <h4>We would like to confirm the order and payment method.</h4>

      
      <div id="order_submit">
        <ul id="up"></ul>
        <img id="image" src="https://img.freepik.com/free-vector/online-order-delivery-service-shipment-internet-shop-basket-cardboard-boxes-buyer-with-laptop-delivery-note-monitor-screen-parcel-vector-isolated-concept-metaphor-illustration_335657-2838.jpg">
        <h3 id="order_title">Your order (Scroll to the right): </h3>
        <div id="template_ordered">
          {% for y in ordered %}
         <div class="ordered_items">
           <h4 class="ordered_label">Item Name: {{y[0]}}</h4>
           <h4 class="ordered_label">Quantity: {{y[1]}}</h4>
           <h4 class="ordered_label">Topping chosen: {{y[2]}}</h4>
           <h4 class="ordered_label">Total price: RM{{y[3]}}</h4>
         </div>
          {% endfor %}
        </div>
        <br>
        <h3 id="total">Total amount: RM{{total}}</h3>
        <br>
        <br>
        <form method="POST">
         <fieldset>
          <h2>Payment method</h2>
          <h4>Choose your payment method below</h4>
          <input type="radio" name="payment_method" id="payment_cash" value="cash">
          <label for="">Pay on cash</label><br>
          <input type="radio" name="payment_method" id="payment_touch" value="TNG">
          <label for="">Pay on Touch N'Go</label>
          <div>
            <p>If you are paying on Touch N'Go please use the QR code below to proceed the payment and provide your transaction name after paid.</p>
            <img src="https://upload.wikimedia.org/wikipedia/commons/d/d0/QR_code_for_mobile_English_Wikipedia.svg" id="qr_code">
          </div>
          <h4 class="input_form">Transaction name:</h4>
          <input type="text" name="transaction_name" class="input_text" required>
          <h4 class="input_form">Your email:</h4>
          <input type="email" name="user_email" class="input_text" required>
         </fieldset>
        <button>Proceed</button>
        </form>
        <br>
        <br>
        <ul id="down"></ul>
      </div>
  </body>
</html>
""",total=str(total),ordered=ordered)

        
@app.route("/gspread_error")
#@limiter.limit("4 per minute")
#@limiter.limit("9 per hour")
def gspread_error():
    return "Error"

@app.route("/wake")
def wake_up():
   return "Wake"

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")

