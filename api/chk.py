from fastapi import FastAPI

app = FastAPI()


@app.get("/api/chk")
async def check():
    return {"status": "ok", "message": "Standalone routing is working!"}
