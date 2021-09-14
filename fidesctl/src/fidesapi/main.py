from fastapi import FastAPI
import uvicorn

fidesapi = FastAPI()


@fidesapi.get("/")
async def root():
    return {"message": "Hello, World"}


def main():
    uvicorn.run("main:fidesapi", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    main()
