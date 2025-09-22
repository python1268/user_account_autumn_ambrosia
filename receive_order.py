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
    SESSION_COOKIE_DOMAIN=".onrender.com",
    SESSION_TYPE='filesystem'  # ← This makes it truly server-side
)

CORS(
    app,
    supports_credentials=True,
    origins=["https://index-autumn.onrender.com"],
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
        
@app.route("/order")
def index():
        return render_template_string("""
        <!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
   /* Homepage */
    #hamburger_radio:checked ~ #hamburger_container #hamburger_group {
      display: block;
    }
    
     #find_food2 {
        display: block;
        margin: 1%;
        width: 25%;
        background-color: blue;
        color: white;
        height: 7%;
        font-size: 0.9em;
        border: 1px solid blue;
        border-radius: 10px;
        cursor: pointer;
      }

    #sign_out_button {
      padding: 10px 20px;
      color: white;
      background-color: red;
      margin-top: 20px;
      font-size: 16px;
      border: 1px solid red;
      border-radius: 10px;
      cursor: pointer;
    }

    .hamburger_item {
      list-style-type: none;
      font-size: 2.7vw;
      margin-bottom: 4vh;
      margin-left: 10%;
      padding: 2px;
    }

    .hamburger_item:hover {
      background-color: blue;
      color: white;
    }

    #hamburger_group {
      margin: 0;
      padding: 0;
      position: absolute;
      width: 20%;
      height: 100%;
      background-color: #F3F3F3;
      left: 0;
      z-index: 1;
      display: none;
      margin-top: 2.4vh;
      opacity: 0.85;
    }

    #home_hamburger {
      margin-top: 4vh;
    }

    #order_button {
      width: 20%;
      height: 5%;
      background-color: green;
      color: white;
      margin-top: 4%;
    }

    .homepage_uppertext {
      color: black;
      margin: -3px;
      text-align: center;
    }

    #food_search {
      margin-top: 10px;
      margin-bottom: 10px;
      height: 50%;
      width: 30%;
      border-radius: 8px;
      border: 1px solid black;
      padding-left: 20%;
      font-size: 1.1em;
    }

    #find_food {
      border-radius: 8px;
      background-color: blue;
      color: white;
      border: 2px solid black;
      width: 30%;
      font-size: 1.3em;
      margin-top: 10px;
      margin-bottom: 10px;
      float: right;
      margin-right: 9px;
      height: 70%;
    }

    #search {
      border: 2px solid black;
      box-shadow: 4px 2px 2px 1px black;
      width: 50%;
      margin: auto;
      margin-top: 3px;
      text-align: center;
    }

    #find {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      height: 100vh;
      position: relative;
    }

    #find::before {
      content: "";
      position: absolute;
      width: 100%;
      height: 100vh;
      background-color: rgb(243, 251, 250);
      z-index: -1;
    }

    #mobile_nav {
      overflow: hidden;
      flex-direction: column;
      width: 100%;
      height: 10%;
      margin: 0;
      padding: 0;
      margin-top: 5vh;
    }

    #name, #burger_list, .mobile_icon, #menu {
      color: black;
      list-style-type: none;
      padding: 3.5vh;
      float: right;
      font-size: 1.3em;
      cursor: pointer;
    }

    #name {
      float: left;
      font-size: 1.6em !important;
      font-family: Inria Serif;
      font-style: italic;
    }

    #logo {
      margin: 5vh;
      width: 20%;
      height: 50%;
    }

    #main {
      color: white;
      margin-top: 20vh;
      margin-left: 10vh;
    }

    #details {
      padding: 1vh 5vh;
      border: 2px solid white;
      border-radius: 20px;
      color: black;
    }

    span {
      width: 8vh;
      height: 0.8vh;
      background-color: black;
      display: none;
      margin-bottom: 7px;
    }

    #span3 {
      margin-bottom: 0px !important;
    }

    #burger {
      float: right;
      margin: 0;
      margin-right: 4.5vh;
      display: block;
      position: absolute;
    }

    .icon {
      width: 10vh;
      height: 10vh;
    }

    

    @media (min-width: 844px) {
      #all {
        margin-left: 10%;
      }

      #name {
        margin-left: 2.4em;
      }
    }

    @media (max-width: 844px) {
      .icon {
        width: 5vh;
        height: 5vh;
      }
    }

    @media (max-width: 692px) {
      span {
        display: block;
        padding: 0px;
      }

      #burger {
        float: left;
        margin-top: 0.5em;
      }

      #mobile_nav {
        display: inline-block;
        width: 100%;
        overflow: hidden;
        padding: 0;
        margin: 0;
      }

      #name, #burger_list, .mobile_icon, #menu {
        display: none;
      }

      .mobile_icon {
        display: block;
        margin-left: 1vh;
        list-style-type: none;
        float: right;
      }

      #burger_list {
        display: block;
        float: left;
      }

      



      #name {
        display: none;
      }
    }

    @media (min-width: 1100px) {
      #details {
        margin-right: 20vh;
      }

      #name, #burger_list, .mobile_icon, #menu {
        margin-left: 9vh;
      }
    }

    /* Order page */
    #order_page {
      display: none;
    }
    
    .order_type_title {
      text-align: center;
    }

    #cancel_button_order_inner {
      color: red;
      font-size: 44px;
      border: none;
      padding: 0;
      background-color: transparent;
      margin-left: 10px;
    }

    #order_navigation {
      margin: 0;
      margin-top: 25px;
      padding: 0;
      width: 100%;
    }

    #cancel_button_order, #cart_link {
      float: left;
      font-size: 35px;
      list-style-type: none;
    }

    #cart_link {
      float: right;
    }

    .order_images {
      width: 350px;
      aspect-ratio: 1/1.5;
      flex-shrink: 0;
      margin-right: 5vw;
      cursor: pointer;
    }

    .order_img_container {
      overflow-x: auto;
      display: flex;
      flex-direction: row;
      margin-bottom: 3.5vw;
    }

    .scroll-container::-webkit-scrollbar {
      display: none;
    }

 

    /* Order chosen */
    #add_to_cart_button {
      padding: 8px;
      border-radius: 8px;
      border: 2px solid blue;
      color: white;
      margin-top: 0.7em;
    }
    #add_to_cart_quantit {
      display: flex;
      flex-direction: row;
    }
    #add_to_cart_item {
      width: 15em;
      height: 20em;

    }
    #button_add_to_cart_add {
  display: inline-block;
  padding: 7px;
  background-color: green;
  color: white;
  border: 1px solid green;
}
#add_to_cart_quantit {
  display: inline-block;
  padding: 7px 12.5px;
}
#button_add_to_cart_decrease {
  padding: 7px;
  display: inline-block;
  background-color: green;
  color: white;
  border: 1px solid green;
}
 #add_to_cart_items {
  display: flex;
  flex-direction: row;
  border: 1px solid grey;
  padding: 0;
  width: 5em;
  margin-left: 10px;
  margin-bottom: 20px;
}
#details_add_to_cart {
  margin-left: 20px;
}

.image_about_waves {
  width: 100%;
  height: 8em;
  margin: 0;
 }
#image_about_footer {
  margin-top: 80vh;
  transform: rotate(180deg);
}
#add_to_cart_back {
  width: 2em;
  height: 2em;
  margin-top: 0.6em;
}
#template_add_to_cart_item {
  width: 100%;
  display: flex;
  justify-content: center;
}

#quantity_select {
  float: left;
  margin-right: 6px;
  font-size: 25px;
 
}

#price_per {
  margin: 0;
  padding: 0;
}

#topping_selection {
  font-size: 25px;
  width: 120px;
}

#topping_selection_label {
  font-size: 21px;
  margin-right: 7px;
}

   /*Cart page*/
      #cart_page {
         margin: 0;
         padding: 0;
       }
      .cart_image {
        width: 9.6em;
        height: 15em;
        margin-top: 2px;
      }
      .cart_info_item {
         margin-left: 15px;

      }
      .cart_item {
        display: flex;
        flex-direction: rows;
        border: 1px solid black;
        margin-bottom: 2em;
      }
      .add_cart_button {
          display: inline-block;
  padding: 7px;
  background-color: green;
  color: white;
  border: 1px solid green;
}
      }
      .minus_cart_button {
          display: inline-block;
  padding: 7px;
  background-color: green;
  color: white;
  border: 1px solid green;
}
      }
      .quantity_cart {
        display: flex;
        flex-direction: row;
        border: 1px solid grey;
      }
      .quantity_cart_item {
        font-size: 1.1em;
        padding-top: 0;
      }
      .select_item_container {
        display: flex;
        align-items: center;
        padding: 1em;
      }
      .selected_items {
        width: 20px;
        height: 20px;
      }
      .button_delete_cart {
        padding: 6px;
        border: 2px solid white;
        border-radius: 6px;
        background-color: red;
        color: white;
      }
      .quantity_cart_bar {
         display: flex;
        flex-direction: row;
      }
      .label_quantity {
        margin-right: 5px;
      }

       #cart_navigation_bar {
            background-color: rgb(20,46,100);
            overflow: hidden;
            margin: 0;
            padding: 0;
            width: 100%;
            margin-bottom: 2em;

        }
        #cart_navigation_back {
            background-color: rgb(20,46,100);
            color: white;
            font-size: 22px;
            padding: 0.5em;
        }

       #cart_arrow_back {
         padding: 0.5em;
         width: 3em;
         height: 3em;
         cursor: pointer;
       }
       .cart_navigation_item {
         float: left;
         list-style-type: none;
       }
       .price_per_item {
         display: flex;
         flex-direction: row;
         margin: 0;
         margin-top: -10px;
       }
       .price_item_cart {
         margin-left: 5px;
       }
       .cart_items {
  display: flex;
  flex-direction: row;
  border: 1px solid grey;
  padding: 0;
  width: 5em;
}
.button_cart_add {
  list-style-type: none;
  padding: 7px;
  border-right: 1px solid grey;
}
.cart_quantity {
  list-style-type: none;
  padding: 7px 12.5px;
}
.button_cart_decrease {
  list-style-type: none;
  padding: 7px;
  border-left: 1px solid grey;
}
.cart_item_details {
  margin-bottom: 15px;
}
#place_order {
  font-size: 17px;
  padding: 10px;
  background-color: blue;
  color: white;
  border: 2px white;
  border-radius: 12px;
}
#place_order:hover {
  background-color: green;
  color: white;
}
#add_to_chosen_tilte {
  font-family: cursive;
  font-size: 40px;
  text-align: center;
}

#add_to_cart_img {
  width: 40px;
  height: 40px;
  margin-left: 17px;
  margin-top: 3px;
}
#add_to_button {
  border: 5px solid rgb(77,166,59);
  border-radius: 20px;
  display: flex;
  flex-direction: rows;
  width: 180px;
}
#add_cart_title {
  font-size: 15px;
  margin-left: 17px;
  margin-top: 13px;
  font-weight: bold;
  font-family: sans-serif;
  color: rgb(77,166,59);
}

/*About*/
.each_person {
            box-shadow: 3px 5px 5px#aaaa;
            width: 15em;
            height: 20em;
            margin-left: 10px;
            text-align: center;
           }

        #about_navigation_bar {
            background-color: rgb(20,46,100);
            overflow: hidden;
            margin: 0;
            padding: 0;
            width: 100%;

        }
        #about_navigation_back {
            background-color: rgb(20,46,100);
            color: white;
            font-size: 22px;
            padding: 0.5em;
        }

       #arrow_back {
         padding: 0.5em;
         width: 2em;
         height: 2em;
       }
       .about_navigation_item {
         float: left;
         list-style-type: none;
       }
        #contact_us_background {
          z-index: -1;
          position: absolute;
          width: 100%;
          height: 20em;
        }
        #contact_us_content {
          position: relative;
          top: 100px;
        }
         #name_content {
           display: flex;
    flex-wrap: wrap;
    justify-content: space-evenly; /* Distributes items evenly */
    gap: 20px; /* Optional: adds space between items */
    padding: 20px;
        }
        #about_us_background {
          width: 100%;
        }
        #about_us {
          font-family: Cursive;
        }


.container {
      margin-bottom: 20px;
    }

    .create_h4, .create_input {
      display: inline-block;
      margin-bottom: 10px;
    }
   
    #create_screen {
      border: 2px solid black;
      width: 400px; /* Set width in px */
      padding: 20px; /* Set padding in px */
      height: auto; /* Height will adjust automatically based on content */
      margin: 50px auto; /* Center the fieldset horizontally */
      border-radius: 10px; /* Optional: rounded corners */
    }
   
    #create_button {
      padding: 8px 16px; /* Increased padding for button */
      background-color: blue;
      color: white;
      border: none; /* Optional: remove button border */
      cursor: pointer; /* Make the button look clickable */
      margin-top: 20px;
      width: 100%; /* Make button span the full width */
    }

    #create_button:hover {
      background-color: darkblue; /* Hover effect for button */
    }
    
    * {box-sizing: border-box}
body {font-family: Verdana, sans-serif; margin:0}
.mySlides {display: none}
img {vertical-align: middle;}

/* Slideshow container */
.slideshow-container {
  max-width: 1000px;
  position: relative;
  margin: auto;
}

/* Next & previous buttons */
.prev, .next {
  cursor: pointer;
  position: absolute;
  top: 50%;
  width: auto;
  padding: 16px;
  margin-top: -22px;
  color: white;
  font-weight: bold;
  font-size: 18px;
  transition: 0.6s ease;
  border-radius: 0 3px 3px 0;
  user-select: none;
}

/* Position the "next button" to the right */
.next {
  right: 0;
  border-radius: 3px 0 0 3px;
}

/* On hover, add a black background color with a little bit see-through */
.prev:hover, .next:hover {
  background-color: rgba(0,0,0,0.8);
}

/* Caption text */
.text {
  color: #f2f2f2;
  font-size: 15px;
  padding: 8px 12px;
  position: absolute;
  bottom: 8px;
  width: 100%;
  text-align: center;
}

/* Number text (1/3 etc) */
.numbertext {
  color: #f2f2f2;
  font-size: 12px;
  padding: 8px 12px;
  position: absolute;
  top: 0;
}

/* The dots/bullets/indicators */
.dot {
  cursor: pointer;
  height: 15px;
  width: 15px;
  margin: 0 2px;
  background-color: #bbb;
  border-radius: 50%;
  display: inline-block;
  transition: background-color 0.6s ease;
}

.active, .dot:hover {
  background-color: #717171;
}

/* Fading animation */
.fade {
  animation-name: fade;
  animation-duration: 1.5s;
}

@keyframes fade {
  from {opacity: .4} 
  to {opacity: 1}
}

/* On smaller screens, decrease text size */
@media only screen and (max-width: 300px) {
  .prev, .next,.text {font-size: 11px}
}

#drinks_image {
  width: 240px;
  height: 240px;
  display: inline-block;
  margin-left: 60px;
  margin-right: 50px;
}

#description_about {
  display: inline-block;
}


.each_person {
            box-shadow: 3px 5px 5px#aaaa;
            width: 15em;
            height: 20em;
            margin-left: 60px;
            text-align: center;
            display: inline-block;
            margin-bottom: 2em;
            border: 1px solid grey;
           }
           
 #name_content {
   margin-top: 60px;
   text-align: center;
 }
 
 #our_drinks {
   text-align: center;
   display: block;
 }
 
 #here_are {
   text-align: center;
   display: block;
 }
 
 
 #about_title {
   text-align: center;
   font-size: 40px;
 }
 
 #about_navigation_bar {
            background-color: rgb(20,46,100);
            overflow: hidden;
            margin: 0;
            padding: 0;
            width: 100%;

        }
        #about_navigation_back {
            background-color: rgb(20,46,100);
            color: white;
            font-size: 22px;
            padding: 0.5em;
        }

       #arrow_back {
         padding: 0.5em;
         width: 3em;
         height: 3em;
       }
       .about_navigation_item {
         float: left;
         list-style-type: none;
       }
       
       .image_about {
         width: 10em;
         height: 15em;
         margin-top: 12px;
       }
       
       #chosen_quantity_title {
         display: inline-block;
         margin-right: 12px;
       }
       
     #logo_autumn {
       width: 300px;
       height: 300px;
     }
  </style>
</head>

<body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/sql-wasm.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.2/papaparse.min.js"></script>
<script>
  window.addEventListener("offline",function() {
    console.log("No connection");
    backup_navigate = navigation;
    navigation = 'no_connection';
    navigate();
  });
 
  window.addEventListener("online",function() {
  });

  window.addEventListener("unload" , function() {
    send_cartdata();
  })

  window.addEventListener("load", function() {
    first_to_run();
  })
 
  let db;
  var data;
  var backup_navigate;
  let navigation;
  var homepage = document.getElementById("homepage");
  var order_page = document.getElementById("order_page");
  var menu_preview = document.getElementById("menu_preview");
  var order_chosen = document.getElementById("add_to_cart_page");
  var cart_page = document.getElementById("cart_page");
  var about_page = document.getElementById("about_page");
  var body = document.getElementsByTagName("body")[0];
  var no_internet = document.getElementById("no_internet_screen");
  var create = document.getElementById("create_screen");
  let topping_price;
  let product_list;

  function hideAllScreens() {
    const screens = [
    homepage, order_page, order_chosen, cart_page,
    about_page, no_internet,create
    ];
    screens.forEach(screen => screen.style.display = "none");
    console.log("Running");
    body.style.backgroundColor = "white";
  }

  function home() {
    hideAllScreens();
    homepage.style.display = "block";
  }

  function order() {
    hideAllScreens();
    order_page.style.display = "block";
  }

  function order_chosen_choice() {
    hideAllScreens();
    order_chosen.style.display = "block";
  }

  function cart() {
    hideAllScreens();
    cart_page.style.display = "block";
  }

  function menu_preview_f() {
    hideAllScreens();
    menu_preview.style.display = "block";
  }

function about() {
    hideAllScreens();
    about_page.style.display = "block";
  }


  function create_acc_page() {
    hideAllScreens();
    create.style.display = "block";
  }



  function no_connection() {
    hideAllScreens();
    no_internet.style.display = "block";
  }

 function navigate() {
    switch (navigation) {
      case "about":
        about();
        break;
      case "order":
        order();
        break;
      case "menu_preview":
        window.open("https://autumnambrosia.my.canva.site/menu");
        break;
      case "cart":
        cart();
        cartpage();
        break;
      case "order_chosen":
        order_chosen_choice();
        break;
      case "create":
        create_acc_page();
        break;
      default:
        home();
        break;
    }
 }

function add_one(id) {
    var final_number = String(parseInt(document.getElementById(id).innerText) + 1);
    document.getElementById(id).innerText = final_number;
    var update_l = db.exec(`SELECT name, topping, total_price FROM cart WHERE id=${id}`)[0].values;
    console.log(update_l);
    console.log(update_l[0]);
    var change = check(update_l[0][0],update_l[0][1]);
    var update = Number(update_l[0][2]) + change;
    update_quantity(final_number, update, id);
  }

  function minus_one(id) {
    var final_number = parseInt(document.getElementById(id).innerText) - 1;
    if (final_number < 0) {
      final_number = String(0);
      document.getElementById(id).innerText = final_number;
      return;
    } else {
       document.getElementById(id).innerText = final_number;
       var update_l = db.exec(`SELECT name, topping, total_price FROM cart WHERE id=${id}`)[0].values;
       console.log(update_l);
       console.log(update_l[0]);
       var change = check(update_l[0][0],update_l[0][1]);
       var update = Number(update_l[0][2]) - change;
     }
     
    if (update != 0) {
      update_quantity(final_number, update, id);
    } else {
      update_quantity(final_number, 0, id);
    }
  }

     function delete_dropdown() {
       document.getElementById("topping_selection").innerHTML = "";
     }

     function cartpage() {
       var result = db.exec("SELECT * FROM cart");
       var cart_items = [];
       if (result.length > 0) {
         cart_items = result[0].values;
       }
       document.getElementById("cart_inner").innerHTML = "";
       cart_items.forEach(row => {
         var id = String(row[0])
         var name = row[1];
         var quantity = row[2];
         var total_price = row[3];
         var topping = row[4];
         var image_link = row[5];
         var item_id = "item" + id;
         console.log({id,name,quantity,total_price,topping,item_id,image_link});
         document.getElementById("cart_inner").innerHTML += `
            <div class="cart_item" id="${item_id}">
      <div class="select_item_container">
      <input type="checkbox" class="selected_items" value=${id}>
       </div>
        <img src="${image_link}" class="cart_image">
        <div class="cart_info_item">
          <h2>${name}</h2>
           <div class="quantity_cart_bar">
          <h3 class="label_quantity">Quantity: </h3>
       <ul class="cart_items">
  <button class="button_cart_add" onclick='add_one("${id}")'>+</button>
  <li class="cart_quantity" id="${id}">${quantity}</li>
  <button class="button_cart_decrease" onclick='minus_one("${id}")'>-</button>
</ul>
</div>
         
         <h4 class="cart_item_details_content">Topping: ${topping}</h4>
 
          <button class="button_delete_cart" onclick='delete_cart(${id})'>Delete</button>
          <div class="price_per_item">
          <h5 class="price_tag_per_item">Total price: <h5 class="price_item_cart">RM${total_price}</h5></h5>
          </div>
        </div>
      </div>
         `
       });
       document.getElementById("cart_inner").innerHTML += `<button id="place_order" onclick="send()">Place order</button>`;
     }



  function add_to_cart() {
    var name_item = document.getElementById("add_to_chosen_tilte").innerText;
    var quantity_item = Number(document.getElementById("add_to_cart_quantit").innerText);
    var topping_item = document.getElementById("topping_selection").value;
    var per_item_price = document.getElementById("price_per").innerText;
    var take_price = per_item_price.trim().split("RM");
    per_item_price = take_price = Number(take_price[1]);
    var totalprice = per_item_price * quantity_item;
    var url = document.getElementById("add_to_cart_item").src;
    var add_price_topping = check_topping(topping_item, quantity_item);
    totalprice = totalprice + add_price_topping;
    db.run("INSERT INTO cart (name,quantity,total_price,topping,url) VALUES (?,?,?,?,?);",[name_item,quantity_item,totalprice,topping_item,url]);
    alert("Successfully added item to your database!");
  }

  function delete_cart(id_delete) {
    if (confirm("Are you sure? After you have clicked you cannot undo.")) {
       id_delete = Number(id_delete)
       db.run('DELETE FROM cart WHERE id = ?',[id_delete]);
       cartpage()
    } else {
      //skip
    }
  }
 
  function update_quantity(new_quantity, update_price, id) {
    try {
      id = Number(id);
      new_quantity = Number(new_quantity)
      db.run("UPDATE cart SET quantity = ? ,total_price = ? WHERE id= ?",[new_quantity,update_price,id]);
      cartpage();
    } catch(err) {
      alert(err.message);
    }
  }

  function check(name, topping) {
    var price;
    var topping_change;
    console.log("Checking product_list:", product_list);
    console.log("Checking for name:", name);
    for (i=0; i < product_list.length; i++) {
      if (product_list[i][0] == name) {
        price = Number(product_list[i][1]);
        console.log(price);
        break
      }
    }
    for (y=0; y < topping_price.length; y++) {
      console.log(topping_price[y][0]);
      if (topping == topping_price[y][0]) {
        topping_change = Number(topping_price[y][1]);
        break
      }
    }
    console.log(price + topping_change);
    return price + topping_change
  }

   //dropdown change
   function change_topping(dropdown_id) {
    var new_topping = document.getElementById(dropdown_id).value;
    update_topping(new_topping, dropdown_id);
  }

  function update_topping(new_topping, id) {
      db.run("UPDATE cart SET topping = ? WHERE id= ?",[new_topping,id]);
      cartpage();
    }

  // Drinks
function drinks() {
  const apiKey = "AIzaSyDWNrk5Y3tlT7g1xAs157Pd77-oLMmOw0M";
  const spreadsheetId = "1-VKCQfq0YvXrXWmcz6omL8aTF_0BARiF0zUlET_brXQ";
  const range = "Sheet1"; // Change this range as needed

  const url = `https://sheets.googleapis.com/v4/spreadsheets/${spreadsheetId}/values/${range}?key=${apiKey}`;

  console.log(url);
  console.log("Running drinks");
  document.getElementById("drink_menu").innerHTML = "";
  console.log("Running drinks");
  return fetch(url)
  .then(response => response.json())
  .then(data => data.values)
  .catch(err => {console.log(err); return [];})
 }


function render_images() {
    for (let i=1; i<product_list.length; i++) {
      const row = product_list[i];
      var name = row[0];
      var price = row[1];
      var topping = JSON.stringify(row[2].trim().split(", ")).replace(/"/g, "'");
      var image = row[3];
      console.log({ name, price, topping, image })
      console.log(topping)
      document.getElementById("drink_menu").innerHTML += `<img class="order_images" src="${image}" onclick="navigation='order_chosen';navigate();add_cart('${name}','${price}','${image}', ${topping})">`;
    }
}


// Topping
function topping_info() {
  const apiKey = "AIzaSyDWNrk5Y3tlT7g1xAs157Pd77-oLMmOw0M";
  const spreadsheetId = "1-VKCQfq0YvXrXWmcz6omL8aTF_0BARiF0zUlET_brXQ";
  const range = "Sheet2";
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${spreadsheetId}/values/${range}?key=${apiKey}`;
  return fetch(url)
  .then(response => response.json())
  .then(data => data.values)
  .catch(err => {console.log(err); return [];});
}


// Topping add on price
function check_topping(topping, quantity) {
  let topping_add_on_price;
  let found = false;
  if (topping != null) {
    for (i=0; i < topping_price.length; i++) {
       if (topping == topping_price[i][0]) {
        console.log("Pass")
        found = true;
        topping_add_on_price = quantity * Number(topping_price[i][1]);
        break
       }
    }
  }
  if (!found) {
    alert("No topping found");
  }
  return topping_add_on_price
}

function add_cart(name,price,image,topping) {
  console.log("Running");
  var cart_add = document.getElementById("upper_section_add_to_cart");
  cart_add.innerHTML = "";
  cart_add.innerHTML += `
    <div id="template_add_to_cart_item">
      <img src=${image} id="add_to_cart_item">
     </div>
      <div id="details_add_to_cart">
        <h2 id="add_to_chosen_tilte">${name}</h2>
        <hr>
          <br>
            <label id="topping_selection_label" for="topping_selection">Topping: </label>
            <select id="topping_selection">
            </select>
           <br>
           <br>
           <br>
        <div id="add_to_cart">
       <h3 id="chosen_quantity_title">Quantity: </h3>
  <button id="button_add_to_cart_add" onclick="add_one('add_to_cart_quantit')">+</button>
  <li id="add_to_cart_quantit">1</li>
  <button id="button_add_to_cart_decrease" onclick="minus_one('add_to_cart_quantit')">-</button>
       </div>
        <br>
        <div>
        <h3>Price: <strong id="price_per">RM${price}</strong></h3>
        <br>
        <div id="add_to_button" onclick="add_to_cart();"><img src="https://media.istockphoto.com/id/898475764/vector/shopping-trolley-cart-icon-in-green-circle-vector.jpg?s=612x612&w=0&k=20&c=W_b90qFRpj_FyLyI19xWqB6EoNSuJYwMSN9nnKkE9Hk=" id="add_to_cart_img"><p id="add_cart_title">Add to cart</p></div>
        </div>
      </div>
      </div>
      <br>
      <hr>
       `;
     document.getElementById("topping_selection").innerHTML = "";
      for (i=0; i<topping.length; i++) {
      document.getElementById("topping_selection").innerHTML += `<option value="${topping[i]}">${topping[i]}</option>`;
    }
}




//send
function send() {
  var order = document.getElementsByClassName("selected_items");
    let order_checked = [];
    for (i=0; i<order.length; i++) {
      if (order[i].checked) {
        order_checked.push(order[i].value);
      } else {
        //skip
    }
  }

  order_list_items = []
  order_checked.forEach(value => {
    x = db.exec(`SELECT name, quantity, topping FROM cart WHERE id= ${value}`)
    x = x[0].values[0];
    console.log(x);
    order_list_items.push(x);
  })

  if (order_checked.length === 0) {
    alert("Please select an item");
    return;
  }
  let user = localStorage.getItem("user");
  var string_data = {order_items: order_list_items, username: user}

  console.log(string_data)

  fetch("https://user-account-autumn-ambrosia.onrender.com",{
    method: "POST",
    credentials: "include",
    headers: {
    "Content-Type": "application/json"
    },
    body: JSON.stringify(string_data)
  })
  .then(response => {
    return response.text();  // Or .json() if your Flask route returns JSON
  })
  .then(data => {
    console.log("Server response:", data);
    // Now safe to redirect after session is stored
    window.location.href = "https://user-account-autumn-ambrosia.onrender.com/confirm";
  })
 }

  function get_user() {
      const name = document.getElementById("create_name").value.trim();
      var userclass = document.getElementById("create_class").value;
      var email = document.getElementById("create_email").value;
      var phone = document.getElementById("create_phone").value;
      
      if (name == null || name === "" || userclass === ""|| userclass === null|| email === "" || email == null) {
         alert("Please provide your name, class, and email.");
         navigation = "create";
         navigate();
         return;
      } else {
     
        localStorage.setItem("user", name);
        localStorage.setItem("user_class", userclass);
        localStorage.setItem("user_email", email);
        localStorage.setItem("user_phone", phone);
     
        const user = localStorage.getItem("user");
     
       if (user != null) {
          try {
           document.getElementById("welcome").innerHTML = `Hello ${user}, what would you like to search today?`;
           console.log("running");
           navigation = "home";
           console.log("running");
           navigate();
           alert("Running");
       }
         catch (err) {
           alert(`Error: ${err.message}`);
       }
      } else {
        navigation = "create";
        navigate();
      }
    }
   }
 

//Sign in
function check_if_got_user() {
  var user = localStorage.getItem("user");
  console.log(user);
  if (user != null) {
     try {
      document.getElementById("welcome").innerHTML = `Hello ${user}, what would you like to search today?`;
      console.log("running");
      navigation = "home";
      console.log("running");
      navigate();
     }
     catch (err) {
      alert(`Error: ${err.message}`);
     }
  } else {
    navigation = "create";
    navigate();
  }
}



 //delete account
 function delete_acc() {
  localStorage.removeItem("user");
  navigation = "create";
  navigate();
 }

 function first_to_run() {
    check_if_got_user();
    console.log("Run");
    drinks();
    initSqlJs({ locateFile: file => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/${file}` }).then(SQL => {
    if (localStorage.getItem("saved_database")) {
      const savedDatabase = localStorage.getItem("saved_database");
      const uInt8Array = new Uint8Array(JSON.parse(savedDatabase));
      db = new SQL.Database(uInt8Array);
    } else {
      db = new SQL.Database();
      db.run("CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, quantity INTEGER, total_price INTEGER, topping TEXT, url TEXT);");
    }
    });
    console.log("Run");

    topping_info().then(data => {
     topping_price = data;
     console.log(topping_price);
    });

    drinks().then(data => {
      product_list = data;
      console.log(product_list);
      render_images();
    });
 }
 
 let slideIndex = 1;
showSlides(slideIndex);

function plusSlides(n) {
  showSlides(slideIndex += n);
}

function currentSlide(n) {
  showSlides(slideIndex = n);
}

function showSlides(n) {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  let dots = document.getElementsByClassName("dot");
  if (n > slides.length) {slideIndex = 1}    
  if (n < 1) {slideIndex = slides.length}
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";  
  }
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";  
  dots[slideIndex-1].className += " active";
}
</script>

<!--No internet-->
<div id="no_internet_screen" style="display: none;">
  <h1>No internet connection</h1>
  <h3>Please connect to the internet and try again.</h3>
  <svg width="100px" height="100px" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <title>wifi-error-solid</title>
  <g id="Layer_2" data-name="Layer 2">
    <g id="invisible_box" data-name="invisible box">
      <rect width="48" height="48" fill="none"/>
    </g>
    <g id="Q3_icons" data-name="Q3 icons">
      <g>
        <path d="M19.9,27.3l-.2-1.7a15.6,15.6,0,0,0-7.4,4.9,1.9,1.9,0,0,0-.4,1.2,2,2,0,0,0,.4,1.3,2,2,0,0,0,3.1,0,11.2,11.2,0,0,1,5.3-3.5A3.5,3.5,0,0,1,19.9,27.3Z"/>
        <path d="M28.3,25.6l-.2,1.7a3.5,3.5,0,0,1-.8,2.2A11.2,11.2,0,0,1,32.6,33a2,2,0,0,0,3.1,0,2.1,2.1,0,0,0,0-2.5A15.6,15.6,0,0,0,28.3,25.6Z"/>
        <path d="M19.1,17.5A23,23,0,0,0,7.5,23.9a2,2,0,0,0-.6,1.4,2.8,2.8,0,0,0,.4,1.2,1.9,1.9,0,0,0,3,.2,18.8,18.8,0,0,1,9.1-5.1Z"/>
        <path d="M28.9,17.5l-.3,4.1a18.8,18.8,0,0,1,9.1,5.1,1.9,1.9,0,0,0,3-.2,2,2,0,0,0-.2-2.6A23,23,0,0,0,28.9,17.5Z"/>
        <path d="M18.5,9.5A32,32,0,0,0,2.6,17.4a2.1,2.1,0,0,0-.2,2.7h0a2,2,0,0,0,3,.2,27.7,27.7,0,0,1,13.4-6.8Z"/>
        <path d="M45.4,17.4A32,32,0,0,0,29.5,9.5l-.3,4a27.7,27.7,0,0,1,13.4,6.8,2,2,0,0,0,3-.2h0A2.1,2.1,0,0,0,45.4,17.4Z"/>
        <circle cx="24" cy="38" r="5"/>
        <path d="M23.9,29h.2a1.9,1.9,0,0,0,2-1.9L27.7,7a3.7,3.7,0,1,0-7.4,0l1.6,20.1A1.9,1.9,0,0,0,23.9,29Z"/>
      </g>
    </g>
  </g>
</svg>
</div>



<!-- Homepage -->
<div id="homepage">
  <ul id="mobile_nav">
    <li id="name">Autumn's Ambrosia</li>
    <li id="burger_list">
      <input type="checkbox" id="hamburger_radio" hidden="">
      <label for="hamburger_radio">
        <img src="https://static.thenounproject.com/png/462023-200.png" id="hamburger_icon" class="icon">
      </label>
      <div id="hamburger_container">
        <ul id="hamburger_group">
          <li class="hamburger_item" id="home_hamburger" onclick="navigation='home';navigate()">Home</li>
          <li class="hamburger_item" onclick="navigation='about';navigate()">About</li>
          <li class="hamburger_item" onclick="navigation='cart';navigate()">Cart</li>
          <li class="hamburger_item" onclick="navigation='menu_preview';navigate()">Menu Preview</li>
          <li class="hamburger_item" onclick="navigation='order';navigate()">Main Menu</li>
        </ul>
      </div>
    </li>
    <li class="mobile_icon" onclick="navigation='about';navigate()">
      <div>
        <img class="icon" id="about_icon" src="https://cdn-icons-png.freepik.com/256/12099/12099654.png?semt=ais_hybrid">
        <p class="homepage_uppertext">About</p>
      </div>
    </li>
    <li class="mobile_icon" onclick="navigation='cart';navigate()">
      <div>
        <img id="cart_icon" class="icon" src="https://cdn-icons-png.flaticon.com/512/3081/3081840.png">
        <p class="homepage_uppertext">Cart</p>
      </div>
    </li>
    <li id="menu" onclick="navigation='menu_preview';navigate()">
      <div>
        <img class="icon" src="https://cdn-icons-png.flaticon.com/512/971/971709.png" alt="Menu icon">
        <p class="homepage_uppertext">Menu</p>
      </div>
    </li>
  </ul>

  <br>

  <div id="find">
    <img id="logo_autumn" src="https://i.ibb.co/yFpXyxP3/Black-White-Flat-Illustrative-Floral-Design-Logo-2-removebg-preview.png">
    <h2 id="welcome">Hello, what would you like to search today?</h2>

    <button id="find_food2" onclick="navigation='order';navigate()">Order Now</button>
    <button id="sign_out_button" onclick="delete_acc();">Sign out</button>
  </div>
</div>

<!-- Order Page -->
<div id="order_page" style="display: none;">
  <ul id="order_navigation">
    <li id="cancel_button_order" onclick="navigation='home';navigate()"><button id="cancel_button_order_inner">x</button></li>
    <li id="cart_link"><a href="#" id="cart_href" onclick="navigation='cart';navigate()">My cart</a></li>
  </ul>

  <br><br><br>

  <h1 class="order_type_title">Drinks</h1>
  <div class="order_img_container" id="drink_menu">
  </div>
  <hr>
</div>



<!--Add to cart-->
<div id="add_to_cart_page" style="display: none;">
    <img id="image_about_header" class="image_about_waves" src="https://img.freepik.com/free-vector/modern-flowing-blue-wave-banner-white-background_1035-18960.jpg">
    <div id="template_add_to_cart_back">
     <img src="https://cdn-icons-png.flaticon.com/512/3964/3964488.png" id="add_to_cart_back" onclick="navigation='order';delete_dropdown();navigate();">
    </div>
    <br>
    <div id="upper_section_add_to_cart">
      </div>
     
     </div>

  <!--Cart page-->
    <div id="cart_page" style="display: none;">
    <ul id="cart_navigation_bar">
            <li class="cart_navigation_item"><img id="cart_arrow_back" src="https://png.pngtree.com/png-vector/20220623/ourmid/pngtree-back-arrow-backward-direction-previous-png-image_5198415.png" onclick="navigation='home';navigate()"></li>
            <li id="cart_navigation_back" class="cart_navigation_item">Back</li>
            </ul>
      <div id="cart_inner"></div>
   </div>

   <!--About page-->
<div id="about_page">
        <ul id="about_navigation_bar">
            <li class="about_navigation_item"><img id="arrow_back" src="https://png.pngtree.com/png-vector/20220623/ourmid/pngtree-back-arrow-backward-direction-previous-png-image_5198415.png" onclick="navigation='home';navigate()"></li>
            <li id="about_navigation_back" class="about_navigation_item">Back</li>
        </ul>

<h1 id="about_title">About us</h1>

<div class="slideshow-container">

<div class="mySlides fade">
  <div class="numbertext">1 / 3</div>
  <img src="https://images.immediate.co.uk/production/volatile/sites/30/2023/10/GF01115BackPagePSOCocktailspreview-829355e.jpg?quality=90&resize=708,643" style="width:100%">
  <div class="text">Caption Text</div>
</div>

<div class="mySlides fade">
  <div class="numbertext">2 / 3</div>
  <img src="https://images.immediate.co.uk/production/volatile/sites/30/2023/10/GF01115BackPagePSOCocktailspreview-829355e.jpg?quality=90&resize=708,643" style="width:100%">
  <div class="text">Caption Two</div>
</div>

<div class="mySlides fade">
  <div class="numbertext">3 / 3</div>
  <img src="https://images.immediate.co.uk/production/volatile/sites/30/2023/10/GF01115BackPagePSOCocktailspreview-829355e.jpg?quality=90&resize=708,643" style="width:100%">
  <div class="text">Caption Three</div>
</div>

<a class="prev" onclick="plusSlides(-1)">❮</a>
<a class="next" onclick="plusSlides(1)">❯</a>

</div>
<br>

<div style="text-align:center">
  <span class="dot" onclick="currentSlide(1)"></span> 
  <span class="dot" onclick="currentSlide(2)"></span> 
  <span class="dot" onclick="currentSlide(3)"></span> 
</div>
<br>
<hr>
<br>
<div>
 <img src="https://images.immediate.co.uk/production/volatile/sites/30/2023/10/GF01115BackPagePSOCocktailspreview-829355e.jpg?quality=90&resize=708,643" id="drinks_image">
 <p id="description_about">We offer some....</p>
</div>
<br>
<hr>
<div id="name_content">
  <div>
       <h1 id="our_drinks">Our drinks</h1>
       
       <p id="here_are">Here are some of our famous drinks.</p>
   </div>
        <div class="each_person">
            <img src="https://i.ibb.co/MyQ7Sbbd/img1.png" class="image_about" alt="image">
            <h3 class="name_each_person">Lychee Sensation</h3>
        </div>
         <div class="each_person">
            <img src="https://ik.imagekit.io/jasonooi/Add%20a%20heading.zip%20-%204.jpeg?updatedAt=1754308163899" class="image_about" alt="image">
            <h3 class="name_each_person">Choko Deez Nuts</h3>
        </div>
        <div class="each_person">
            <img src="https://ik.imagekit.io/jasonooi/Add%20a%20heading.jpeg?updatedAt=1754308163956" class="image_about" alt="image">
            <h3 class="name_each_person">Spooky Choc</h3>
        </div>
        <div class="each_person">
            <img src="https://ik.imagekit.io/jasonooi/Add%20a%20heading.zip%20-%209.jpeg?updatedAt=1754308163882" class="image_about" alt="image">
            <h3 class="name_each_person">Boba Tea</h3>
        </div>
        </div>
      </div>
    
    
     <fieldset id="create_screen">
        <h1>Log in</h1>
        <div class="container">
         <h4 class="create_h4">Name (Full name):</h4>
         <input type="text" class="create_input" id="create_name" required>
        </div>
        <div>
         <h4>If you are the Taylor Puchong students, please choose the class or put "other".</h4>
         <h4 class="create_h4">Class:</h4>
         <input type="text" class="create_input" id="create_class" required>
        </div>
        <div>
         <h4 class="create_h4">Email: </h4>
         <input type="email" class="create_input" id="create_email" required>
        </div>
        <div>
         <h4 class="create_h4">Phone number:</h4>
         <input type="tel" class="create_input" id="create_phone">
        </div>
        <button id="create_button" type="button" onclick="get_user();">Log in</button>
  </fieldset>
 
</body>
</html>
        """)


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

