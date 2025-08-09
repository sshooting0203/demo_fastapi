from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {
        "greeting": "Hello, World!",
        "message": "Welcome to Food Analyzer API!",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}