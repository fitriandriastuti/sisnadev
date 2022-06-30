FROM python:3.9

WORKDIR /sisna-app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./app ./app

CMD ["python","./app/main.py"]
#CMD ["uvicorn","app.main:app","--reload","--workers","1","--host","0.0.0.0","--port","8000"]




