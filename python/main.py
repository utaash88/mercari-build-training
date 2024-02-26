import os
import sqlite3
import json
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
import hashlib
from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import FileResponse , JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

""" conn=sqlite3.connect(dbname)
cur=conn.cursor() """


""" cur.execute(CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    name TEXT,
    category TEXT,
    image_name TEXT
)) """


logger = logging.getLogger("uvicorn")
logger.level = logging.INFO

origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


db_path = pathlib.Path(__file__).parent/"db"/"mercari.sqlite3"
images = pathlib.Path(__file__).parent/"python"/ "images"
items_json_path = pathlib.Path(__file__).parent.resolve() / "items.json"

#create database

conn = sqlite3.connect(db_path)
cur = conn.cursor()

def create_table():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            image_name TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    conn.commit()
    
create_table()

#def save_image(file,filename):
    #with open(images / filename, "wb") as image:
        #image.write(file)

def save_item_db(name, category, image_name):
    cur.execute("INSERT INTO items (name, category, image_name) VALUES (?, ?, ?)", (name, category, image_name))
    conn.commit()

@app.get("/")
def root():
    return {"message": "Hello, world!"}

""" items_list=[]
@app.post("/items")
def add_item(name: str = Form(...), category:str=Form(...), image:UpladFile = File(...)):
    logger.info(f"Receive item: {name}, category: {category}, image: {image}")
    
    file_content = image.file.read()
    hash_value = hashlib.sha256(file_content).hexdigest()
    image_filename = f"{hash_value}.jpg"
    save_image(file_content, image_filename)

    save_item_db(name, category, image_filename)
    return {"message": f"item received: {name},category:{category}","image_name": image_filename}
 """

 

@app.post("/items")
async def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}, {category}, image: {image.filename}")

    # 画像のハッシュ値を計算してファイル名とする
    contents = await image.read()
    hash_sha256 = hashlib.sha256(contents).hexdigest()
    image_filename = f"{hash_sha256}.jpg"
    image_path = images / image_filename

    # 画像を保存
    with open(image_path, "wb") as f:
        f.write(contents)

    #sqliteに追加
    cur.execute("SELECT id FROM categories WHERE name = ?", (category,))
    category_result = cur.fetchone()

    if not category_result:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
        conn.commit()
        category_id = cur.lastrowid
    else:
        category_id = category_result[0]

    cur.execute("INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?)", (name, category_name, image_filename))
    conn.commit()


    # 新しいアイテムをJSONファイルに追加
    new_item = {"name": name, "category": category, "image_name": image_filename}
    with open(items_json_path, "r+") as f:
        items = json.load(f)
        items.append(new_item)
        f.seek(0)
        json.dump(items, f, indent=4)

    return {"message": f"item received: {name}, {category}, {image_filename}"}




""" @app.get("/items")
def get_items():
    cur.execute("SELECT name, category, image_name FROM items")
    items=cur.fetchall()
    cur.execute("SELECT category_id FROM items INNER JOIN category ON items.category_id=category.id")
    return {"items":items} """


@app.get("/items")
def get_items():
    # JSONファイルからアイテムを読み込み
    with open(items_json_path, "r") as f:
        items = json.load(f)
    return items

@app.get("/image/{image_name}")
async def get_image(image_name):
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)

"""@app.get("/items/{item_id}")
def get_item(item_id: int= Path(..., title="The ID of the item to get")):
    items_data=load_item()
     existing_items = items_data.get("items", [])

    if item_id < len(existing_items):
        item = existing_items[item_id-1]
        return item """

""" @app.get("/search/{search_item}")
def search_item(search_item:str):
    cur.execute("SELECT name, category, image_name FROM items WHERE name LIKE ?",("%"+search_item+"%",))
    items= cur.fetchall()
    return {"items":items}

cur.close()
conn.close() """