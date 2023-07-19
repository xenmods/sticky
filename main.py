import traceback
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import typing
import json
from fastapi.templating import Jinja2Templates
from pathlib import Path
from threading import Thread
from pydantic import BaseModel
import shortuuid
from database import *
from araby_ai import Chat
import os

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(docs_url=None)
app.mount("/static", StaticFiles(directory=r"./"), name="static")
templates = Jinja2Templates(directory=r"./templates")


class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")


class Paste(BaseModel):
    content: str
    pasteID: str
    controlID: str

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
    pasteID = content.pasteID or shortuuid.uuid()[:8]
    controlID = content.controlID or shortuuid.uuid()[:6]
    try:
        return create_paste(
            pasteID=pasteID, controlID=controlID, content=content.content
        )
    except:
        print(traceback.format_exc())

@app.post("/save")
async def paste(content: Save):
    try:
        data = edit_paste(content.pasteID, content.editID, content.content)
        return data
    except:
        print(traceback.format_exc())
        return data

@app.get("/get")
async def getpaste(pasteID, request: Request):
    return RedirectResponse(f"https://sticky-xenmods.koyeb.app/{pasteID}")


@app.get("/help")
async def helppage(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse("assets/favicon.ico")

@app.get('/logo.png', include_in_schema=False)
async def logo():
    return FileResponse("assets/logo.png")

@app.get('/download')
async def downloadSticky(id: str, background_tasks: BackgroundTasks):
    contents = get_paste(id)
    file_path = f"tmp/{id}.md"
    with open(file_path, 'w') as f:
        f.write(contents)
    background_tasks.add_task(delete_file, file_path)
    return FileResponse(file_path)

@app.get('/edit')
async def downloadSticky(id: str, request: Request):
    contents = get_paste(id)
    return templates.TemplateResponse(
        "edit.html", {"request": request, "StickyID": id, "content": contents}
    )


@app.api_route("/{sticky_id:path}", methods=["GET"])
async def getpaste(sticky_id: str, request: Request):
    if paste := get_paste(sticky_id):
        title = Chat.GPT(f"I will give you a text. You don't need context. just generate a < 10 title for this. This will be used as a title for this page. If you cannot responde just say 'Text'. The text: {paste}")
        return templates.TemplateResponse(
            "paste.html", {"request": request, "StickyID": sticky_id, "content": paste, "title": title}
        )
    else:
        return templates.TemplateResponse("404.html", {"request": request})



def run():
    uvicorn.run(app, port=Config.PORT)
    # uvicorn.run(app)


def webservice():
    server = Thread(target=run)
    server.start()


run()
