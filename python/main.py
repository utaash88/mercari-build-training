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

db_path = pathlib.Path(__file__).parent.resolve() /"mercari.sqlite3.new"
images = pathlib.Path(__file__).parent.resolve() /"images"
items_json_path = pathlib.Path(__file__).parent.resolve() / "items.json"

def initialize_database():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            image_name TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_item_db(name, category, image_name):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO items (name, category, image_name) VALUES (?, ?, ?)", (name, category, image_name))
    conn.commit()
    conn.close() 

@app.get("/")
async def root():
    return {"message": "Hello, world!"}


  
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
    """ cur.execute("SELECT id FROM categories WHERE name = ?", (category,))
    category_result = cur.fetchone()

    if not category_result:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
        conn.commit()
        category_id = cur.lastrowid
    else:
        category_id = category_result[0]

    cur.execute("INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?)", (name, category_name, image_filename))
    conn.commit() """

    save_item_db(name, category, image_filename)

    # 新しいアイテムをJSONファイルに追加
    new_item = {"name": name, "category": category, "image_name": image_filename}
    with open(items_json_path, "r+") as f:
        items = json.load(f)
        items.append(new_item)
        f.seek(0)
        json.dump(items, f, indent=4)

    return {"message": f"item received: {name}, {category}, {image_filename}"}


@app.get("/items")
def get_items():
    """ # JSONファイルからアイテムを読み込み
    with open(items_json_path, "r") as f:
        items = json.load(f)
    return items """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT items.id, items.name, categories.name as category, items.image_name
        FROM items
        INNER JOIN categories ON items.category_id = categories.id
    """)
    items = cur.fetchall()

    conn.close()

    # 取得したデータを適切な形式に整形して返す
    formatted_items = []
    for item in items:
        formatted_item = {
            "id": item[0],
            "name": item[1],
            "category": item[2],
            "image_name": item[3]
        }
        formatted_items.append(formatted_item)

    return formatted_items
    
@app.get("/image/{image_name}")
async def get_image(image_name):
    #image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"
    return FileResponse(image)
  
  
@app.get("/search/{search_item}")
def search_item(search_item:str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, category, image_name FROM items WHERE name LIKE ?",("%"+search_item+"%",))
    items= cur.fetchall()
    conn.commit()
    conn.close()
    return {"items":items}

