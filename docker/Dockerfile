FROM python:3.12-bookworm

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y \
    && pip install -r requirements.txt

COPY . /flash_cards
RUN cd /flash_cards \
    && python manage.py migrate
WORKDIR "flash_cards"
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]