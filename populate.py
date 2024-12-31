import uuid
import random
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://canyildiz1386:0COOxv0pH7orehbk@cluster0.3duqw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient("mongodb://localhost:27017/")
db = client["sho"]
collection = db["products"]

electronics = [
    ("Apple iPhone 14 Pro", "Next-level smartphone with advanced chip"),
    ("Samsung Galaxy S22", "High-end Android phone with versatile cameras"),
    ("Sony WH-1000XM4", "Wireless noise-canceling headphones"),
    ("Nintendo Switch OLED", "Hybrid gaming console with OLED screen"),
    ("Dell XPS 13", "Premium ultra-thin laptop"),
    ("Apple MacBook Air M2", "Lightweight laptop with M2 chip"),
    ("Canon EOS R6", "Full-frame mirrorless camera"),
    ("GoPro HERO10", "Rugged action camera for adventures"),
    ("LG C2 OLED TV", "High-contrast 4K OLED television"),
    ("Kindle Paperwhite", "E-ink e-reader with front light"),
    ("Bose SoundLink Revolve+", "Portable 360-degree Bluetooth speaker"),
    ("Garmin Fenix 7", "Multisport GPS smartwatch"),
    ("Sony PlayStation 5", "Next-gen gaming console"),
    ("Xbox Series X", "4K gaming console by Microsoft"),
    ("Samsung Galaxy Tab S8", "High-resolution Android tablet"),
    ("Apple iPad Pro M1", "Powerful tablet with M1 chip"),
    ("DJI Mavic Air 2S", "4K drone with advanced obstacle avoidance"),
    ("Razer BlackWidow V3", "Mechanical gaming keyboard"),
    ("Logitech MX Master 3S", "Advanced wireless mouse for productivity"),
    ("Fitbit Sense", "Health-focused smartwatch with EDA sensor")
]

fashion = [
    ("Levi's 501 Jeans", "Classic straight-fit denim"),
    ("Nike Air Force 1", "Iconic low-top sneakers"),
    ("Adidas Ultraboost", "High-comfort running shoes"),
    ("Ray-Ban Wayfarer", "Timeless unisex sunglasses"),
    ("Michael Kors Jet Set Tote", "Stylish designer tote bag"),
    ("Calvin Klein Boxer Briefs", "Comfortable everyday underwear"),
    ("North Face Thermoball Jacket", "Lightweight insulated jacket"),
    ("Converse Chuck Taylor", "Classic canvas high-tops"),
    ("Rolex Submariner", "Luxury dive watch"),
    ("Hermès Silk Scarf", "High-end silk accessory"),
    ("Lululemon Align Leggings", "Buttery-soft yoga pants"),
    ("Gucci GG Belt", "Signature leather belt with GG buckle"),
    ("Uniqlo Supima Cotton Tee", "Basic T-shirt with premium cotton"),
    ("Puma RS-X", "Chunky sneakers with retro design"),
    ("Adidas Trefoil Hoodie", "Classic logo pullover hoodie"),
    ("Prada Cahier Bag", "Designer leather crossbody"),
    ("Timberland 6-Inch Boots", "Rugged waterproof boots"),
    ("Champion Reverse Weave Crew", "Heritage sweatshirt with classic logo"),
    ("Burberry Trench Coat", "Iconic heritage coat"),
    ("H&M Slim Fit Blazer", "Affordable formal wear staple")
]

home = [
    ("Dyson V11 Vacuum", "Cordless vacuum with powerful suction"),
    ("KitchenAid Stand Mixer", "Must-have mixer for baking"),
    ("Instant Pot Duo", "Multi-function pressure cooker"),
    ("Philips Hue Starter Kit", "Smart lighting system"),
    ("Nespresso Vertuo Plus", "Single-serve espresso and coffee maker"),
    ("iRobot Roomba i7+", "Self-emptying robot vacuum"),
    ("Brita Water Pitcher", "Water filter pitcher for clean drinking"),
    ("Amazon Echo Show 8", "Smart display with Alexa"),
    ("Sony HT-G700 Soundbar", "Immersive 3D audio for living room"),
    ("Weber Spirit II E-310", "Propane gas grill for outdoor cooking"),
    ("Casper Original Mattress", "Popular bed-in-a-box memory foam"),
    ("Nest Learning Thermostat", "Smart thermostat that saves energy"),
    ("Anova Precision Cooker", "Immersion circulator for sous vide"),
    ("Eufy Video Doorbell", "Smart doorbell with 2K resolution"),
    ("Le Creuset Dutch Oven", "Enamel cast-iron for braising and soups"),
    ("OXO 12-Piece Container Set", "Airtight food storage for kitchen"),
    ("SodaStream Terra", "Make sparkling water at home"),
    ("IKEA Lack Coffee Table", "Minimalist table for living room"),
    ("All-Clad Fry Pan Set", "Durable stainless steel cookware"),
    ("Shark Air Purifier", "Removes allergens and dust")
]

sports = [
    ("Wilson Evolution Basketball", "Official size indoor basketball"),
    ("Yonex Nanoray Badminton Racket", "Lightweight racket for quick maneuvers"),
    ("Titleist Pro V1 Golf Balls", "Premium golf balls for distance and control"),
    ("Peloton Bike", "Indoor cycling bike with digital classes"),
    ("Bowflex SelectTech 552", "Adjustable dumbbells for weight training"),
    ("Nike Mercurial Soccer Cleats", "Lightweight boots for speed on the pitch"),
    ("Wilson NFL Football", "Official-size leather football"),
    ("Under Armour UA Hustle Backpack", "Sports backpack with durable build"),
    ("Speedo Vanquisher Goggles", "Anti-fog swim goggles for competition"),
    ("Franklin Table Tennis Set", "Starter set with paddles and net"),
    ("Wilson Tennis Balls (3-pack)", "Pressurized balls for all courts"),
    ("CamelBak Hydration Pack", "Hydration backpack for running or hiking"),
    ("Reebok Yoga Mat", "Thick cushioning for yoga and stretching"),
    ("Fit Simplify Resistance Bands", "Set of loop bands for workouts"),
    ("Adidas F50 Shin Guards", "Lightweight protection for soccer"),
    ("Garmin Edge 530", "Cycling computer with GPS"),
    ("On Running Cloudflow", "Lightweight running shoes with Helion foam"),
    ("Rollerblade Zetrablade Skates", "Inline skates for beginners"),
    ("Huffy Hardtail Mountain Bike", "Entry-level MTB for casual trails"),
    ("Spalding Pro Slam Hoop System", "Adjustable outdoor basketball hoop")
]

beauty = [
    ("Clinique Moisture Surge", "Lightweight gel-cream for hydration"),
    ("Estée Lauder Double Wear", "Long-lasting liquid foundation"),
    ("Urban Decay Naked Palette", "Versatile eyeshadow palette"),
    ("Olaplex No.3 Hair Perfector", "Repairing treatment for damaged hair"),
    ("Neutrogena Hydro Boost", "Hyaluronic acid water gel"),
    ("Garnier Micellar Water", "All-in-one makeup remover"),
    ("Maybelline Lash Sensational", "Volumizing mascara for full lashes"),
    ("The Ordinary Niacinamide 10%", "Serum for blemish-prone skin"),
    ("CeraVe Hydrating Cleanser", "Gentle cleanser for normal to dry skin"),
    ("MAC Ruby Woo Lipstick", "Iconic red matte lipstick"),
    ("L'Oréal True Match Foundation", "Wide-range foundation for different skin"),
    ("Batiste Dry Shampoo", "Quick fix for oily roots and fresh hair"),
    ("Cetaphil Gentle Skin Cleanser", "Sensitive-skin friendly cleanser"),
    ("Tresemmé Keratin Smooth Shampoo", "Control frizz and add shine"),
    ("Dove Body Wash", "Moisturizing body cleanser"),
    ("Secret Aluminum-Free Deodorant", "Gentle formula for sensitive skin"),
    ("Aveeno Daily Moisturizing Lotion", "Nourishing oatmeal lotion"),
    ("Pixi Glow Tonic", "Exfoliating toner for brighter skin"),
    ("Revlon ColorStay Eyeliner", "Long-lasting pencil eyeliner"),
    ("Neutrogena Ultra Sheer Sunscreen", "Broad-spectrum sun protection")
]

client.drop_database("sho")
db = client["sho"]
collection = db["products"]

data = []
for name, desc in electronics:
    pid = str(uuid.uuid4())[:8]
    price = round(random.uniform(50, 2000), 2)
    inv = random.randint(1, 150)
    data.append({
        "product_id": pid,
        "name": name,
        "category": "Electronics",
        "description": desc,
        "price": price,
        "likes_count": 0,
        "image_url": "https://via.placeholder.com/200.png?text=" + name.replace(" ","+"),
        "inventory": inv
    })

for name, desc in fashion:
    pid = str(uuid.uuid4())[:8]
    price = round(random.uniform(10, 500), 2)
    inv = random.randint(1, 150)
    data.append({
        "product_id": pid,
        "name": name,
        "category": "Fashion",
        "description": desc,
        "price": price,
        "likes_count": 0,
        "image_url": "https://via.placeholder.com/200.png?text=" + name.replace(" ","+"),
        "inventory": inv
    })

for name, desc in home:
    pid = str(uuid.uuid4())[:8]
    price = round(random.uniform(15, 800), 2)
    inv = random.randint(1, 150)
    data.append({
        "product_id": pid,
        "name": name,
        "category": "Home",
        "description": desc,
        "price": price,
        "likes_count": 0,
        "image_url": "https://via.placeholder.com/200.png?text=" + name.replace(" ","+"),
        "inventory": inv
    })

for name, desc in sports:
    pid = str(uuid.uuid4())[:8]
    price = round(random.uniform(8, 400), 2)
    inv = random.randint(1, 150)
    data.append({
        "product_id": pid,
        "name": name,
        "category": "Sports",
        "description": desc,
        "price": price,
        "likes_count": 0,
        "image_url": "https://via.placeholder.com/200.png?text=" + name.replace(" ","+"),
        "inventory": inv
    })

for name, desc in beauty:
    pid = str(uuid.uuid4())[:8]
    price = round(random.uniform(5, 200), 2)
    inv = random.randint(1, 150)
    data.append({
        "product_id": pid,
        "name": name,
        "category": "Beauty",
        "description": desc,
        "price": price,
        "likes_count": 0,
        "image_url": "https://via.placeholder.com/200.png?text=" + name.replace(" ","+"),
        "inventory": inv
    })
print(data)
collection.insert_many(data)
print("Inserted", len(data), "products.")
