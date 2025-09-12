from flask import Flask, render_template_string, redirect, url_for, request,session
from flask_cors import CORS
#from flask_limiter import Limiter
#from flask_limiter.util import get_remote_address
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime as d
import time
import os


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
    global price_list
    global topping_price
    name_list = sheet_product.col_values(1)[1:]
    price_list = sheet_product.col_values(2)[1:]
    topping_list = sheet_product.col_values(3)[1:]
    topping_price = sheet_product_two.get_all_values()
    print(name_list)
    print(topping_list)
    print(price_list)
    print(topping_price)

load_data()

app = Flask(__name__)
app.secret_key = 'something_secure_and_secret'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
CORS(app,resources={r"/*": {"origins": "*"}}, supports_credentials=True)
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

         ordered = []
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
                 
                 if quantity > 40:
                     print(quantity)
                     return f"Too many"
                 
                 if topping not in topping_list:
                     print(topping)
                     return f"We do not have {topping} in our topping menu"
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

                 for y in topping_price:
                     if topping == y[0]:
                         session["topping_price"] = int(y[1])*quantity
                         total_price += session["topping_price"]
                         print(total_price)
                         place.append(total_price)
                         total += total_price
                         print(f"Amount: {total}")
                         break

                 ordered.append(place)
         print("Running")
         session["ordered"] = ordered
         print(ordered)
         session["total"] = total
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
        write_order(session["receive"],session["customer"])
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
      
     <form method="POST">
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
           <h4 class="ordered_label">Total price: {{y[3]}}</h4>
         </div>
          {% endfor %}
        </div>
        <br>
        <h3 id="total">Total amount: RM{{total}}</h3>
        <br>
        <div id="confirm">
        <h4 id="confirm_title">Is this the correct order?</h4>
        <input type="radio" name="yes_no" id="yes" value="yes">
        <label for="">Yes</label>
        <br>
        <input type="radio" name="yes_no" id="no" value="no">
        <label for="">No</label>
        </div>
        <br>
        <br>
        <fieldset>
          <h2>Payment method</h2>
          <h4>Choose your payment method below</h4>
          <input type="radio" name="payment_method" id="payment_method">
          <label for="">Pay on cash</label><br>
          <input type="radio" name="payment_method" id="payment_method">
          <label for="">Pay on Touch N'Go</label>
          <div>
            <p>If you are paying on Touch N'Go please use the QR code below to proceed the payment.</p>
            <img src="https://upload.wikimedia.org/wikipedia/commons/d/d0/QR_code_for_mobile_English_Wikipedia.svg" id="qr_code">
          </div>
        </fieldset>
        <button>Proceed</button>
        <br>
        <br>
        <ul id="down"></ul>
      </div>
     </form>
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

if __name__ == "__main__":
   app.run(debug=False, host="0.0.0.0", port=5003)

while True: 
    load_data()
    time.sleep(60*60*12)
