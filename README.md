# Event management API
- The code is written in Python `FastAPI` backend development framework with `RESTful` APIs and testing using `pytest`.
- If you are using postman, you can access the my postman collection for current project by importing `Event Management.postman_collection.json` to your postman
- I have used SQLite database which is `default` database in FastAPI
- `events.db` is being used for local and `test.db` is for testing.
- `test` directory is used for test case files
- `app` is the main directory for the code

## To run the program
- Create a python `venv(virtual environment)`
- run `pip install -r requirements.txt`
- run `uvicorn app.main:app --reload` or `runap.bat`
- go to `https://localhost:8000/docs` to access the swagger documentation
- to run the test cases run `pytest'
- to get the test coverage for your code run `pytest --cov=app --cov-report=html`, it will give html files report in `htmlcov` folder


