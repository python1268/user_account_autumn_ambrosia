
import secrets
from flask import Flask, render_template_string, redirect, url_for, request,jsonify
from flask_cors import CORS
#from flask_limiter import Limiter
#from flask_limiter.util import get_remote_address
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime as d
import time
import os
import threading


from upstash_redis import Redis



r = Redis(url="https://enormous-mastodon-11551.upstash.io", token="AS0fAAIncDJkYTk4MzFhMmY3Yjg0MDQ5YTBiY2Y1NDRlNzk0MTAzYXAyMTE1NTE")



# Define scope - what APIs you want to access
scope = ['https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive']

creds_json = os.environ.get("GOOGLE_CREDS_JSON")
creds_dict = json.loads(creds_json)

# Load your service account credentials JSON file
# Load your service account credentials JSON file

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)


# Authorize the client
client = gspread.authorize(creds)


# Open your Google Sheet by name
sheet_customer = client.open('Customer_order').sheet1

sheet_product = client.open('Product').sheet1  

sheet_product_two = client.open('Product').worksheet('Sheet2')



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


"""
CORS(
    app,
    supports_credentials=True,
    origins=["https://index-autumn.onrender.com"],
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)
"""

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
    
CORS(app)

#First (Get token)
@app.route("/token")
def get_token():
    token = secrets.token_urlsafe(16)
    r.hset(token, "initialized", "true")
    r.expire(token, 200)
    print(token,flush=True)
    """
    users_tokens[token] = {}
    users_tokens[token]["expire_time"] = time.time() + 60*15
    """
    return jsonify({"token": token})

#Token received. Then, frontend sends the order and store the data in memory dictionary 
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
    r.hset(token, "order", json.dumps(order_data))
    r.hset(token, "customer", username)
    """
    users_tokens[token]["order"] = order_data
    users_tokens[token]["customer"] = username
    """

    return jsonify({"message": "success"})

#After receive success messages, then show the GET 
@app.route("/confirm",methods=["GET","POST"])
#@limiter.limit("4 per minute")
#@limiter.limit("9 per hour")
def confirm():
    token = request.args.get("token")
    if not token or not r.exists(token):
        return jsonify({"error": "Invalid token"}), 401
    
    orderdata = r.hgetall(token)
    if "order" in orderdata:
     orderdata["order"] = json.loads(orderdata["order"])

    if request.method == "POST":
                email = request.form.get("user_email")
                transaction_name = request.form.get("transaction_name")
                payment_method = request.form.get("payment_method")
                if email is None:
                        return "Please provide your email."
                if payment_method is None:
                        return "Please choose a payment method."
                elif payment_method == "cash":
                        try:
                           orderdata["Email"] = email
                           orderdata["Payment_Method"] = payment_method
                           order_json = json.dumps(orderdata,indent=4)
                           print(order_json)
                           sheet_customer.append_row([orderdata["customer"],order_json])
                        except Exception as e:
                            return f"Error in confirm: {str(e)}"        
                else:
                        if payment_method == "TNG" and transaction_name is not None:
                            try:
                             r.hset(token, "Email", email)
                             r.hset(token, "Payment_Method", payment_method)
                             r.hset(token, "Transaction_Name", transaction_name)

                             order_json = json.dumps(r.hgetall(token),indent=4)
                             print(order_json)
                             sheet_customer.append_row([orderdata["customer"],order_json])
                            except Exception as e:
                              return f"Error in confirm: {str(e)}"
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
    
    total = 0

    for thing in orderdata["order"]:
                 print(thing[0])
                 thing[1] = int(thing[1])
                 print(thing[1])
                 print(thing[2])

                 if thing[0] not in name_list:
                     print(f"name")
                     return f"We do not have {thing[0]} in our menu"
                 else:
                     name_index = name_list.index(thing[0])
                 
                 if thing[1] > 40:
                     print(thing[1])
                     return f"Too many"
                 
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
                           total += total_price
                           print(f"Amount: {total}")
                         else:
                                print("Failed")
                 else:
                        return f"We do not have {thing[2]} in our topping menu"
    
    print("Running")
    orderdata["total"] = total
        
    for k, v in orderdata.items():
      r.hset(token, k, str(v))
            
    print("TOTAL:", total)
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
""",total=str(orderdata["total"]),ordered=orderdata["order"])

        
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
