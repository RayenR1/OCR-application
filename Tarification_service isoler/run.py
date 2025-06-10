#github:@YassineBenMaktouf | linkedin :Yassine Ben Maktouf

# run_ocr.py
from app import config
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=True)