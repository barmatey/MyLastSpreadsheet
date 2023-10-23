import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.report.infrastructure.router import router_report, router_source, router_wire
from src.spreadsheet.infrastructure.router import router_sheet

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_report)
app.include_router(router_source)
app.include_router(router_wire)
app.include_router(router_sheet)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9999)
