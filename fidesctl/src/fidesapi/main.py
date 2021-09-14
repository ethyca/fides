from fastapi import FastAPI
import uvicorn

fidesapi = FastAPI()


def main():
    uvicorn.run(fidesapi, host="127.0.0.1", port="8000", debug=True)


if __name__ == "__main__":
    main()
