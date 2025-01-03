# README.md

# 🌟 streamlit-shop-populator 🌟

Build a mini e-commerce prototype with user authentication, product listing, recommendations, cart, and more—all in **Streamlit**. Includes a data population script to insert sample products for testing.

## 🚀 Features
- **User Signup/Login/Logout**  
- **Product Initialization** (Creates sample products if none exist)  
- **Recommendations** via **CF + Content**  
- **Cart & Wishlist**  
- **Reviews** & **Ratings**  
- **Admin Panel** to manage products, promo codes, etc.  

## 🎉 Quick Start
1. **Clone** this repository:
   ```bash
   git clone https://github.com/your-username/streamlit-shop-populator.git
   ```
2. **Navigate** into the folder:
   ```bash
   cd streamlit-shop-populator
   ```
3. **Install** dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run** the Streamlit app:
   ```bash
   streamlit run populate.py
   ```
5. **Open** the provided URL in your browser to explore the app.

## 📋 Requirements
- **Python 3.7+**  


## 🛠️ Inside populate.py
- **`init_products()`** inserts default items if your database is empty.
- **`home_page()`** shows recommended products + all products.
- **`inline_product_details()`** handles product details, likes, saves, cart.
- **`admin_panel()`** offers product/bulk-upload/promo/user management.

## ⚙️ Customization
- Switch the **database name** from `sho` to something else.
- Modify **`init_products()`** or create additional data.
- Adjust **price** and **inventory** generation logic if desired.

## ❤️ Contribute
- **Fork** this repo
- **Create** a new branch
- **Commit** your changes
- **Open** a Pull Request

## 📧 Feedback / Issues
- Please open an **issue** on GitHub for bugs, ideas, or enhancements.

## ⚖️ License
- Distributed under the **MIT License**.

Enjoy your streamlined e-commerce demo with **Streamlit**! 🎈