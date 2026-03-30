import os, shutil, datetime
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()
STORAGE_PATH = "storage"
TRASH_PATH = "trash"
os.makedirs(STORAGE_PATH, exist_ok=True)
os.makedirs(TRASH_PATH, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

from pydantic import BaseModel

class MoveRequest(BaseModel):
    name: str
    current_folder: str
    target_folder: str

@app.get("/api/list-folders")
async def list_folders():
    # Restituisce "root" + tutte le sottocartelle esistenti
    folder_list = ["root"]
    for root, dirs, files in os.walk(STORAGE_PATH):
        for d in dirs:
            # Calcoliamo il percorso relativo rispetto a STORAGE_PATH
            rel_p = os.path.relpath(os.path.join(root, d), STORAGE_PATH)
            folder_list.append(rel_p.replace("\\", "/"))
    return folder_list

@app.post("/api/move")
async def move_item(data: MoveRequest):
    src_dir = os.path.join(STORAGE_PATH, data.current_folder.lstrip("/"))
    dst_dir = STORAGE_PATH if data.target_folder == "root" else os.path.join(STORAGE_PATH, data.target_folder.lstrip("/"))
    
    src = os.path.join(src_dir, data.name)
    dst = os.path.join(dst_dir, data.name)

    if os.path.exists(src):
        # Protezione: non spostare una cartella dentro se stessa
        if os.path.abspath(dst_dir).startswith(os.path.abspath(src)):
            return {"status": "error", "message": "Non puoi spostare una cartella dentro se stessa!"}
        
        # Se il file esiste già a destinazione, aggiungiamo un timestamp
        if os.path.exists(dst):
            dst = os.path.join(dst_dir, f"copy_{int(datetime.datetime.now().timestamp())}_{data.name}")
        
        shutil.move(src, dst)
        return {"status": "ok"}
    return {"status": "error", "message": "File sorgente non trovato"}

class RenameRequest(BaseModel):
    old_name: str
    new_name: str
    folder: str

class FolderCreate(BaseModel):
    name: str

def get_items(path):
    items = []
    if not os.path.exists(path): return items
    for name in os.listdir(path):
        full_p = os.path.join(path, name)
        stats = os.stat(full_p)
        items.append({
            "name": name, "is_dir": os.path.isdir(full_p),
            "size": f"{stats.st_size / 1024:.1f} KB" if not os.path.isdir(full_p) else "-",
            "date": datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
        })
    return sorted(items, key=lambda x: not x['is_dir'])

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/files/{view}")
async def list_files(view: str, folder: str = ""):
    base = STORAGE_PATH if view == "drive" else TRASH_PATH
    target = os.path.normpath(os.path.join(base, folder.lstrip("/")))
    return get_items(target)

@app.post("/api/rename")
async def rename_item(data: RenameRequest):
    folder_path = os.path.join(STORAGE_PATH, data.folder.lstrip("/"))
    os.rename(os.path.join(folder_path, data.old_name), os.path.join(folder_path, data.new_name))
    return {"status": "ok"}

@app.get("/api/move-to-trash")
async def move_to_trash(name: str, folder: str = ""):
    src = os.path.join(STORAGE_PATH, folder.lstrip("/"), name)
    dst = os.path.join(TRASH_PATH, name)
    if os.path.exists(src):
        if os.path.exists(dst): dst = os.path.join(TRASH_PATH, f"{int(datetime.datetime.now().timestamp())}_{name}")
        shutil.move(src, dst)
    return {"status": "ok"}

@app.get("/api/empty-trash")
async def empty_trash():
    for n in os.listdir(TRASH_PATH):
        p = os.path.join(TRASH_PATH, n)
        if os.path.isdir(p): shutil.rmtree(p)
        else: os.remove(p)
    return {"status": "ok"}

@app.post("/api/create-folder")
async def create_folder(data: FolderCreate):
    os.makedirs(os.path.join(STORAGE_PATH, data.name.lstrip("/")), exist_ok=True)
    return {"status": "ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...), currentFolder: str = ""):
    target = os.path.join(STORAGE_PATH, currentFolder.lstrip("/"))
    os.makedirs(target, exist_ok=True)
    with open(os.path.join(target, file.filename), "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "ok"}

@app.get("/api/download")
async def download(filename: str, folder: str = ""):
    return FileResponse(os.path.join(STORAGE_PATH, folder.lstrip("/"), filename), filename=filename)