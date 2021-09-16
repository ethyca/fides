from fastapi import FastAPI
import uvicorn

import crud

fidesapi = FastAPI()

for router in crud.routers:
    fidesapi.include_router(router)


def main():
    uvicorn.run("main:fidesapi", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    main()
