from fastapi import FastAPI, UploadFile, File
from sites import SITES
from scraper import scrape_site
from formatter import format_answer
from translator import translate_bn
from image_tools import analyze_image

app = FastAPI(title="Cyber AI Assistant")

@app.get("/")
def home():

    return {
        "app": "Cyber AI",
        "developer": "Khaled Mahmud",
        "sites": len(SITES)
    }


@app.get("/sites")
def list_sites():

    return SITES


@app.get("/ask")
def ask(q: str, mode: str = "short"):

    collected = []

    for site in SITES:

        url = SITES[site]["url"]
        data = scrape_site(url)

        if data:
            collected.append(data)

    combined = " ".join(collected)

    formatted = format_answer(combined, mode)

    bangla = translate_bn(formatted)

    return {
        "question": q,
        "answer_en": formatted,
        "answer_bn": bangla,
        "sources": list(SITES.keys())
    }


@app.post("/image")
async def upload_image(file: UploadFile = File(...)):

    result = await analyze_image(file)

    return {
        "filename": file.filename,
        "analysis": result
    }


@app.get("/about")
def about():

    return {
        "app": "Cyber AI",
        "developer": "Khaled Mahmud",
        "description": "Cyber Security AI learning assistant"
    }
