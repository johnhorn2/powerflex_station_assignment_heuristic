FROM python:3.9-slim
RUN mkdir /home/code
WORKDIR /home/code

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
ENTRYPOINT ["streamlit", "run"]
