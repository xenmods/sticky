from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import shortuuid
from database import *
import os

app = FastAPI(docs_url=None)
app.mount("/static", StaticFiles(directory=r"./"), name="static")
templates = Jinja2Templates(directory=r"./templates")
class Paste(BaseModel):
    content: str
    pasteID: str
class Save(BaseModel):
    content: str
    pasteID: str
    editID: str
def delete_file(file_path):
    os.remove(file_path)
    return

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.post("/paste")
async def paste(content: Paste):
    if not content.pasteID:
        pasteID = shortuuid.uuid()[:8]
    else:
        pasteID = content.pasteID
    controlID = shortuuid.uuid()[:6]
    data = create_paste(
        pasteID=pasteID, controlID=controlID, content=content.content
    )
    return data

@app.post("/save")
async def save_sticky(content: Save):
    data = edit_paste(content.pasteID, content.editID, content.content)
    return data
@app.get("/help")
async def help_page(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse("assets/favicon.ico")

@app.get('/logo.png', include_in_schema=False)
async def logo():
    return FileResponse("assets/logo.png")

@app.get('/download')
async def download_sticky(id: str, background_tasks: BackgroundTasks):
    contents = get_paste(id)
    file_path = f"tmp/{id}.md"
    with open(file_path, 'w') as f:
        f.write(contents)
    background_tasks.add_task(delete_file, file_path)
    return FileResponse(file_path)

@app.get('/edit')
async def edit_sticky(id: str, request: Request):
    contents = get_paste(id)
    return templates.TemplateResponse(
        "edit.html", {"request": request, "StickyID": id, "content": contents}
    )


@app.api_route("/{sticky_id:path}", methods=["GET"])
async def getpaste(sticky_id: str, request: Request):
    paste = get_paste(sticky_id)
    if not paste:
        return templates.TemplateResponse("404.html", {"request": request})
    return templates.TemplateResponse(
        "paste.html", {"request": request, "StickyID": sticky_id, "content": paste}
    )

def run():
    uvicorn.run(app, port=Config.PORT)
    # uvicorn.run(app)

run()
