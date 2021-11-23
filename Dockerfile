FROM python:3.8
ADD . /queue_manager_new
WORKDIR /queue_manager_new
RUN pip install -r requirements.txt
CMD ["python", "main_threading.py"]
