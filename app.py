import os
import re
import time
import uuid
import bcrypt
import random
import string
import smtplib
import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st
from email.mime.text import MIMEText
from bson.objectid import ObjectId
from pymongo import MongoClient, TEXT
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime

st.set_page_config(page_title="Online Shop", layout="wide", initial_sidebar_state="expanded")

st.session_state.setdefault("user_id", None)
st.session_state.setdefault("user_name", None)
st.session_state.setdefault("user_email", None)
st.session_state.setdefault("is_admin", False)
st.session_state.setdefault("page_number", 1)
st.session_state.setdefault("products_per_page", 6)
st.session_state.setdefault("active_page", "Home")
st.session_state.setdefault("show_details_for", None)
st.session_state.setdefault("load_more_key", 0)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["sho"]
users_collection = db["users"]
products_collection = db["products"]
interactions_collection = db["interactions"]
orders_collection = db["orders"]
reviews_collection = db["reviews"]
promo_codes_collection = db["promo_codes"]
activity_logs_collection = db["activity_logs"]

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def check_password(plain, hashed):
    return bcrypt.checkpw(plain.encode("utf-8"), hashed)

def valid_password(p):
    if len(p) < 8: return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", p): return False
    return True

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def record_activity(user_id, action, details=""):
    activity_logs_collection.insert_one({
        "user_id": user_id,
        "action": action,
        "details": details,
        "timestamp": datetime.utcnow()
    })

def record_interaction(user_id, product_id, t):
    if t == "like": rating = 5
    elif t == "save": rating = 3
    elif t == "cart": rating = 4
    else: rating = 0
    interactions_collection.update_one(
        {"user_id": user_id, "product_id": product_id},
        {"$set": {"rating": rating, "timestamp": datetime.utcnow()}},
        upsert=True
    )
    record_activity(user_id, f"Interaction: {t}", f"product_id={product_id}")

def init_products():
    if products_collection.count_documents({}) == 0:
        sample = [
            {
                "product_id": str(uuid.uuid4())[:8],
                "name": "Cool T-Shirt",
                "category": "Fashion",
                "description": "A stylish T-shirt with unique prints.",
                "price": 19.99,
                "likes_count": 0,
                "image_url": "https://via.placeholder.com/200/222222/FFFFFF?text=Cool+T-Shirt",
                "inventory": 50
            },
            {
                "product_id": str(uuid.uuid4())[:8],
                "name": "Gaming Mouse",
                "category": "Electronics",
                "description": "High-precision wireless mouse.",
                "price": 29.99,
                "likes_count": 0,
                "image_url": "https://via.placeholder.com/200/222222/FFFFFF?text=Gaming+Mouse",
                "inventory": 20
            },
            {
                "product_id": str(uuid.uuid4())[:8],
                "name": "Smart Watch",
                "category": "Wearables",
                "description": "Track your daily activity and fitness.",
                "price": 99.99,
                "likes_count": 0,
                "image_url": "https://via.placeholder.com/200/222222/FFFFFF?text=Smart+Watch",
                "inventory": 10
            },
        ]
        products_collection.insert_many(sample)

def build_item_similarity_matrix():
    data = list(interactions_collection.find({}))
    if not data: return None, None, None
    df = pd.DataFrame(data)
    df["user_id"] = df["user_id"].astype(str)
    df["product_id"] = df["product_id"].astype(str)
    pivot = df.pivot_table(index="product_id", columns="user_id", values="rating", fill_value=0)
    items = pivot.index.tolist()
    matrix = pivot.values
    sim = cosine_similarity(matrix)
    return sim, pivot, items

def predict_rating(user_id, product_id, sim_matrix, pivot, item_ids):
    if sim_matrix is None: return 2.5
    if product_id not in item_ids: return 2.5
    idx = item_ids.index(product_id)
    cols = pivot.columns.tolist()
    if user_id not in cols: return 2.5
    user_ratings = pivot.iloc[:, cols.index(user_id)].values
    sim_scores = sim_matrix[idx]
    num, den = 0, 0
    for i, r in enumerate(user_ratings):
        if r > 0:
            num += sim_scores[i] * r
            den += abs(sim_scores[i])
    if den == 0: return 2.5
    return num / den

def content_score(u_doc, p_doc):
    liked_cats = set()
    for pid in u_doc.get("liked_products", []):
        item = products_collection.find_one({"product_id": pid})
        if item: liked_cats.add(item["category"])
    if not liked_cats: return 1
    if p_doc["category"] in liked_cats: return 5
    return 1

def hybrid_recommendations(user_id, top_k=5):
    user_doc = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user_doc: return []
    sim, pivot, items = build_item_similarity_matrix()
    all_p = list(products_collection.find({}))
    scores = []
    for prod in all_p:
        cf = predict_rating(str(user_doc["_id"]), prod["product_id"], sim, pivot, items)
        cb = content_score(user_doc, prod)
        final = 0.7 * cf + 0.3 * cb
        scores.append((prod, final))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in scores[:top_k]]

def product_by_id(pid):
    return products_collection.find_one({"product_id": pid})

def check_and_login(email, password):
    with st.spinner("Authenticating..."):
        user_doc = users_collection.find_one({"email": email})
        if not user_doc:
            return None, "User not found."
        if not check_password(password, user_doc["hashed_password"]):
            return None, "Incorrect password."
        return user_doc, None

def register_user(name, email, password):
    h = hash_password(password)
    r = generate_referral_code()
    doc = {
        "name": name,
        "email": email,
        "hashed_password": h,
        "is_admin": False,
        "saved_products": [],
        "liked_products": [],
        "cart": [],
        "orders": [],
        "referral_code": r,
        "referred_by": None,
        "wishlist": [],
        "phone": "",
        "address": "",
        "city": "",
        "postal_code": "",
        "extra_info": ""
    }
    users_collection.insert_one(doc)
    return doc

def get_current_user():
    if not st.session_state["user_id"]: return None
    return users_collection.find_one({"_id": ObjectId(st.session_state["user_id"])})

def login_screen():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if not email or not password:
            st.error("Please fill all fields.")
            return
        user, err = check_and_login(email, password)
        if err:
            st.error(err)
            return
        st.session_state["user_id"] = str(user["_id"])
        st.session_state["user_name"] = user["name"]
        st.session_state["user_email"] = user["email"]
        st.session_state["is_admin"] = user.get("is_admin", False)
        record_activity(str(user["_id"]), "Login")
        st.success("Logged in successfully!")
        st.experimental_rerun()

def signup_screen():
    st.subheader("Sign Up")
    name = st.text_input("Name")
    email = st.text_input("Email")
    p = st.text_input("Password", type="password")
    c = st.text_input("Confirm Password", type="password")
    ref = st.text_input("Referral Code (Optional)")
    if st.button("Sign Up"):
        if not name or not email or not p or not c:
            st.error("Please fill all fields.")
            return
        if p != c:
            st.error("Passwords do not match.")
            return
        if not valid_password(p):
            st.error("Password must be at least 8 chars and include a special character.")
            return
        e = users_collection.find_one({"email": email})
        if e:
            st.error("Account with this email already exists.")
            return
        new_user = register_user(name, email, p)
        if ref:
            ref_user = users_collection.find_one({"referral_code": ref})
            if ref_user:
                users_collection.update_one(
                    {"_id": new_user["_id"]},
                    {"$set": {"referred_by": str(ref_user["_id"])}}
                )
        st.success("Account created successfully!")
        st.info("You can now log in.")
        time.sleep(1)
        st.experimental_rerun()

def logout():
    record_activity(st.session_state["user_id"], "Logout")
    st.session_state["user_id"] = None
    st.session_state["user_name"] = None
    st.session_state["user_email"] = None
    st.session_state["is_admin"] = False
    st.success("You have been logged out.")
    time.sleep(1)
    st.experimental_rerun()

##############################################################################
# ADD A "prefix" PARAMETER TO MAKE WIDGET KEYS UNIQUE PER SECTION OR CONTEXT #
##############################################################################
def inline_product_details(prod, prefix=""):
    u = get_current_user()
    if not u:
        st.warning("Please log in first.")
        return
    st.write("Category:", prod["category"])
    st.write("Price:", f"${prod['price']}")
    st.write("Likes:", prod["likes_count"])
    st.write(prod["description"])

    like_key = f"{prefix}_like_{prod['product_id']}"
    save_key = f"{prefix}_save_{prod['product_id']}"
    cart_key = f"{prefix}_cart_{prod['product_id']}"

    like_clicked = st.button("Like", key=like_key)
    save_clicked = st.button("Save", key=save_key)
    cart_clicked = st.button("Add to Cart", key=cart_key)

    if like_clicked:
        if prod["product_id"] not in u.get("liked_products", []):
            users_collection.update_one({"_id": u["_id"]}, {"$push": {"liked_products": prod["product_id"]}})
            products_collection.update_one({"product_id": prod["product_id"]}, {"$inc": {"likes_count": 1}})
            record_interaction(str(u["_id"]), prod["product_id"], "like")
        st.experimental_rerun()
    if save_clicked:
        if prod["product_id"] not in u.get("saved_products", []):
            users_collection.update_one({"_id": u["_id"]}, {"$push": {"saved_products": prod["product_id"]}})
            record_interaction(str(u["_id"]), prod["product_id"], "save")
        st.experimental_rerun()
    if cart_clicked:
        cart_items = [c["product_id"] for c in u.get("cart", [])]
        if prod["product_id"] not in cart_items:
            users_collection.update_one(
                {"_id": u["_id"]},
                {"$push": {"cart": {"product_id": prod["product_id"], "quantity": 1}}}
            )
            record_interaction(str(u["_id"]), prod["product_id"], "cart")
        st.experimental_rerun()

    st.subheader("Reviews")
    reviews = list(reviews_collection.find({"product_id": prod["product_id"]}).sort("timestamp", -1))
    if reviews:
        for rv in reviews:
            rv_user = users_collection.find_one({"_id": ObjectId(rv["user_id"])})
            uname = rv_user["name"] if rv_user else "Unknown User"
            st.write(uname, "rated it", rv["rating"], "stars")
            st.write(rv["review"])
            st.caption(str(rv["timestamp"]))
            st.write("---")
    else:
        st.info("No reviews yet.")

    st.write("Write a Review")

    rating_key = f"{prefix}_rating_{prod['product_id']}"
    review_key = f"{prefix}_review_{prod['product_id']}"
    submit_key = f"{prefix}_submit_{prod['product_id']}"

    rating_val = st.slider("Rating", 1, 5, 5, key=rating_key)
    review_val = st.text_area("Review", key=review_key)
    submit_btn = st.button("Submit Review", key=submit_key)

    if submit_btn:
        reviews_collection.update_one(
            {"user_id": str(u["_id"]), "product_id": prod["product_id"]},
            {"$set": {"rating": rating_val, "review": review_val, "timestamp": datetime.utcnow()}},
            upsert=True
        )
        record_activity(str(u["_id"]), "Review", f"product_id={prod['product_id']}")
        st.success("Review submitted!")
        st.experimental_rerun()

def home_page():
    u = get_current_user()
    if not u: return
    st.subheader(f"Welcome, {u['name']}!")

    recs = hybrid_recommendations(str(u["_id"]), 5)
    st.subheader("Recommended for You")
    for prod in recs:
        # Use a "recommendation" prefix
        with st.expander(prod["name"]):
            st.image(prod["image_url"], width=160)
            inline_product_details(prod, prefix="rec")

    st.write("---")
    st.subheader("All Products")
    search = st.text_input("Search")
    category = st.selectbox("Category", ["All"] + sorted(products_collection.distinct("category")))
    low, high = st.slider("Price Range", 0, 1000, (0, 1000))
    if st.button("Apply Filters"):
        st.session_state.page_number = 1
        st.session_state["load_more_key"] += 1

    query = {}
    if search:
        query["$text"] = {"$search": search}
    if category != "All":
        query["category"] = category
    query["price"] = {"$gte": low, "$lte": high}

    skip_count = (st.session_state.page_number - 1) * st.session_state.products_per_page
    items = list(products_collection.find(query).skip(skip_count).limit(st.session_state.products_per_page))
    if items:
        for pr in items:
            # Use an "all" prefix
            with st.expander(pr["name"]):
                st.image(pr["image_url"], width=160)
                inline_product_details(pr, prefix="all")
    else:
        st.info("No products found.")

    total_matches = products_collection.count_documents(query)
    loaded_count = skip_count + len(items)
    if loaded_count < total_matches:
        if st.button("Load More", key=f"load_more_{st.session_state['load_more_key']}"):
            st.session_state.page_number += 1
            st.experimental_rerun()

def liked_products_page():
    u = get_current_user()
    if not u: return
    st.subheader("Liked Products")
    if not u.get("liked_products"):
        st.info("No liked products.")
        return
    for pid in u["liked_products"]:
        p = product_by_id(pid)
        if p:
            with st.expander(p["name"]):
                st.image(p["image_url"], width=160)
                inline_product_details(p, prefix="liked")

def saved_products_page():
    u = get_current_user()
    if not u: return
    st.subheader("Saved Products")
    if not u.get("saved_products"):
        st.info("No saved products.")
        return
    for pid in u["saved_products"]:
        p = product_by_id(pid)
        if p:
            with st.expander(p["name"]):
                st.image(p["image_url"], width=160)
                inline_product_details(p, prefix="saved")

def wishlist_page():
    u = get_current_user()
    if not u: return
    st.subheader("Wishlist")
    if not u.get("wishlist"):
        st.info("No items in your wishlist.")
        return
    for pid in u["wishlist"]:
        p = product_by_id(pid)
        if p:
            with st.expander(p["name"]):
                st.image(p["image_url"], width=160)
                inline_product_details(p, prefix="wish")

def cart_page():
    u = get_current_user()
    if not u: return
    st.subheader("Your Cart")
    cart_items = u.get("cart", [])
    if not cart_items:
        st.info("Your cart is empty.")
        return

    total = 0
    removed = []
    for item in cart_items:
        pr = product_by_id(item["product_id"])
        if pr:
            st.write(pr["name"], "-", f"${pr['price']}")
            st.write("Quantity:", item["quantity"])
            st.image(pr["image_url"], width=80)
            total += pr["price"] * item["quantity"]
            rem_btn = st.button("Remove", key=f"remove_{pr['product_id']}")
            if rem_btn:
                removed.append(item["product_id"])
            st.write("---")

    for r in removed:
        users_collection.update_one({"_id": u["_id"]}, {"$pull": {"cart": {"product_id": r}}})
    if removed:
        st.experimental_rerun()

    st.write("Total:", f"${round(total, 2)}")
    code = st.text_input("Promo Code")
    if st.button("Apply Promo"):
        c = promo_codes_collection.find_one({"code": code})
        if c and c.get("active", False):
            d = c.get("discount", 0)
            total = max(0, total - d)
            st.success(f"Promo applied. Discount: ${d}")
        else:
            st.error("Invalid or inactive promo code.")

    if st.button("Checkout"):
        if total == 0:
            st.warning("Cart is empty or total is 0.")
            return
        oid = str(uuid.uuid4())[:8]
        orders_collection.insert_one({
            "order_id": oid,
            "user_id": str(u["_id"]),
            "items": cart_items,
            "total_amount": round(total, 2),
            "timestamp": datetime.utcnow(),
            "status": "Processing"
        })
        users_collection.update_one({"_id": u["_id"]}, {"$push": {"orders": oid}, "$set": {"cart": []}})
        for ci in cart_items:
            p = product_by_id(ci["product_id"])
            if p and "inventory" in p:
                new_inv = max(0, p["inventory"] - ci["quantity"])
                products_collection.update_one({"product_id": ci["product_id"]}, {"$set": {"inventory": new_inv}})
        try:
            msg = MIMEText(f"Thank you for your order #{oid}. Total: ${total}.")
            msg["Subject"] = "Order Confirmation"
            msg["From"] = "noreply@shop.com"
            msg["To"] = u["email"]
            s = smtplib.SMTP("localhost")
            s.send_message(msg)
            s.quit()
        except:
            pass
        record_activity(str(u["_id"]), "Checkout", f"order_id={oid}")
        st.success(f"Order placed! Your Order ID is {oid}.")

def purchase_history_page():
    u = get_current_user()
    if not u: return
    st.subheader("Purchase History")
    if not u.get("orders"):
        st.info("No orders yet.")
        return
    for odid in u["orders"]:
        o = orders_collection.find_one({"order_id": odid})
        if o:
            st.write("Order ID:", o["order_id"])
            st.write("Total:", f"${o['total_amount']}")
            st.write("Status:", o["status"])
            st.write("Date:", str(o["timestamp"]))
            st.write("---")

def profile_page():
    u = get_current_user()
    if not u: return
    st.subheader("Your Profile")
    st.write("Referral Code:", u.get("referral_code", "N/A"))
    new_name = st.text_input("Name", value=u["name"])
    new_email = st.text_input("Email", value=u["email"])
    new_phone = st.text_input("Phone Number", value=u.get("phone", ""))
    new_address = st.text_input("Address", value=u.get("address", ""))
    new_city = st.text_input("City", value=u.get("city", ""))
    new_postal = st.text_input("Postal Code", value=u.get("postal_code", ""))
    new_extra = st.text_area("Additional Info", value=u.get("extra_info", ""))
    if st.button("Update Profile"):
        if new_email != u["email"]:
            ex = users_collection.find_one({"email": new_email})
            if ex and ex["_id"] != u["_id"]:
                st.error("That email is already in use by another account.")
                return
        users_collection.update_one(
            {"_id": u["_id"]},
            {"$set": {
                "name": new_name,
                "email": new_email,
                "phone": new_phone,
                "address": new_address,
                "city": new_city,
                "postal_code": new_postal,
                "extra_info": new_extra
            }}
        )
        st.session_state["user_name"] = new_name
        st.session_state["user_email"] = new_email
        st.success("Profile updated successfully!")
        st.experimental_rerun()

def admin_panel():
    u = get_current_user()
    if not u or not u.get("is_admin", False): return
    st.title("Admin Panel")
    tab = st.selectbox("", [
        "Dashboard",
        "Manage Products",
        "Bulk Upload",
        "Promo Codes",
        "User Management",
        "Order Management",
        "Analytics & Logs",
        "Advanced Reporting"
    ])
    if tab == "Dashboard":
        tu = users_collection.count_documents({})
        tp = products_collection.count_documents({})
        agg = products_collection.aggregate([{"$group": {"_id": None, "sum": {"$sum": "$likes_count"}}}])
        tl_data = list(agg)
        total_likes = tl_data[0]["sum"] if tl_data else 0
        st.metric("Total Users", tu)
        st.metric("Total Products", tp)
        st.metric("Total Likes", total_likes)
        st.subheader("Trending Products")
        tr = products_collection.find().sort("likes_count", -1).limit(5)
        for p in tr:
            st.write(p["name"], "-", p["likes_count"], "likes")
    elif tab == "Manage Products":
        ps = list(products_collection.find({}))
        for pr in ps:
            with st.expander(f"{pr['name']} ({pr['category']})"):
                n = st.text_input(f"Name_{pr['product_id']}", pr["name"])
                c = st.text_input(f"Cat_{pr['product_id']}", pr["category"])
                d = st.text_area(f"Desc_{pr['product_id']}", pr["description"])
                pri = st.number_input(f"Price_{pr['product_id']}", value=pr["price"])
                img = st.text_input(f"Img_{pr['product_id']}", pr["image_url"])
                inv = st.number_input(f"Inv_{pr['product_id']}", value=pr.get("inventory", 0))
                upd_btn = st.button("Update", key=f"upd_{pr['product_id']}")
                if upd_btn:
                    products_collection.update_one(
                        {"_id": pr["_id"]},
                        {"$set": {
                            "name": n,
                            "category": c,
                            "description": d,
                            "price": pri,
                            "image_url": img,
                            "inventory": inv
                        }}
                    )
                    st.experimental_rerun()
                del_btn = st.button("Delete", key=f"del_{pr['product_id']}")
                if del_btn:
                    products_collection.delete_one({"_id": pr["_id"]})
                    st.experimental_rerun()
    elif tab == "Bulk Upload":
        f = st.file_uploader("Upload CSV")
        if f:
            df = pd.read_csv(f)
            for _, row in df.iterrows():
                pid = str(uuid.uuid4())[:8]
                products_collection.insert_one({
                    "product_id": pid,
                    "name": row["name"],
                    "category": row["category"],
                    "description": row["description"],
                    "price": float(row["price"]),
                    "likes_count": 0,
                    "image_url": row.get("image_url", ""),
                    "inventory": row.get("inventory", 0)
                })
            st.success("Bulk upload complete.")
    elif tab == "Promo Codes":
        st.subheader("Create Promo Code")
        code = st.text_input("Code")
        disc = st.number_input("Discount", value=10)
        create_code_btn = st.button("Create Code")
        if create_code_btn:
            promo_codes_collection.insert_one({"code": code, "discount": disc, "active": True})
            st.success("Created.")
        st.subheader("Existing Codes")
        promos = list(promo_codes_collection.find({}))
        for pc in promos:
            with st.expander(pc["code"]):
                active = st.checkbox("Active", value=pc["active"], key=f"ac_{pc['code']}")
                upd_pc_btn = st.button("Update", key=f"upd_pc_{pc['code']}")
                if upd_pc_btn:
                    promo_codes_collection.update_one({"_id": pc["_id"]}, {"$set": {"active": active}})
                    st.experimental_rerun()
                del_pc_btn = st.button("Delete", key=f"del_pc_{pc['code']}")
                if del_pc_btn:
                    promo_codes_collection.delete_one({"_id": pc["_id"]})
                    st.experimental_rerun()
    elif tab == "User Management":
        allu = list(users_collection.find({}))
        for us in allu:
            with st.expander(us["email"]):
                adm = st.checkbox("Is Admin", value=us.get("is_admin", False), key=f"adm_{us['email']}")
                save_usr_btn = st.button("Save", key=f"save_usr_{us['email']}")
                if save_usr_btn:
                    users_collection.update_one({"_id": us["_id"]}, {"$set": {"is_admin": adm}})
                    st.experimental_rerun()
                del_usr_btn = st.button("Delete", key=f"del_usr_{us['email']}")
                if del_usr_btn:
                    users_collection.delete_one({"_id": us["_id"]})
                    st.experimental_rerun()
    elif tab == "Order Management":
        st.subheader("All Orders")
        odx = list(orders_collection.find({}).sort("timestamp", -1))
        for od in odx:
            with st.expander(f"Order {od['order_id']} - Status: {od['status']}"):
                st.write(od)
                ns = st.selectbox(
                    "Status",
                    ["Processing","Shipped","Delivered","Cancelled"],
                    index=["Processing","Shipped","Delivered","Cancelled"].index(od["status"]),
                    key=f"status_{od['order_id']}"
                )
                upd_ord_btn = st.button("Update", key=f"upd_ord_{od['order_id']}")
                if upd_ord_btn:
                    orders_collection.update_one({"_id": od["_id"]}, {"$set": {"status": ns}})
                    st.experimental_rerun()
    elif tab == "Analytics & Logs":
        st.subheader("User Activity Logs")
        logs = list(activity_logs_collection.find({}).sort("timestamp", -1))
        if logs:
            df_logs = pd.DataFrame(logs)
            st.write(df_logs[["user_id", "action", "details", "timestamp"]])
            st.download_button(
                "Download Logs CSV",
                data=df_logs.to_csv(index=False),
                file_name="activity_logs.csv"
            )
        st.subheader("Interactions Over Time")
        inter = list(interactions_collection.find({}))
        if inter:
            df_int = pd.DataFrame(inter)
            if "timestamp" in df_int.columns:
                df_int["timestamp"] = pd.to_datetime(df_int["timestamp"])
                df_int["date"] = df_int["timestamp"].dt.date
                ipd = df_int.groupby("date").size().reset_index(name="interactions")
                figi = px.bar(ipd, x="date", y="interactions", title="Interactions Over Time")
                st.plotly_chart(figi)
            st.download_button(
                "Download Interactions CSV",
                data=df_int.to_csv(index=False),
                file_name="interactions.csv"
            )
    elif tab == "Advanced Reporting":
        st.subheader("Advanced Reporting")
        orz = list(orders_collection.find({}))
        if orz:
            df_ord = pd.DataFrame(orz)
            st.write(df_ord)
            st.download_button(
                "Download Orders CSV",
                data=df_ord.to_csv(index=False),
                file_name="orders.csv"
            )

def role_based_routing():
    user = get_current_user()
    if not user:
        return st.sidebar.radio("Menu", ["Login", "Sign Up"])
    if user.get("is_admin", False):
        return st.sidebar.radio(
            "Menu", 
            ["Home", "Liked", "Saved", "Wishlist", "Cart", "History", "Profile", "Admin", "Logout"],
            index=0
        )
    return st.sidebar.radio(
        "Menu", 
        ["Home", "Liked", "Saved", "Wishlist", "Cart", "History", "Profile", "Logout"],
        index=0
    )

def main():
    init_products()
    choice = role_based_routing()
    if choice == "Login":
        login_screen()
    elif choice == "Sign Up":
        signup_screen()
    elif choice == "Logout":
        logout()
    elif choice == "Home":
        home_page()
    elif choice == "Liked":
        liked_products_page()
    elif choice == "Saved":
        saved_products_page()
    elif choice == "Wishlist":
        wishlist_page()
    elif choice == "Cart":
        cart_page()
    elif choice == "History":
        purchase_history_page()
    elif choice == "Profile":
        profile_page()
    elif choice == "Admin":
        admin_panel()

if __name__ == "__main__":
    main()
