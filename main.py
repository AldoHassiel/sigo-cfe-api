from fastapi import FastAPI

app = FastAPI(title="SIGO CFE API", version="0.0.1")


@app.get("/")
async def root():
    return {"bienvenido": "a SIGO CFE API"}
