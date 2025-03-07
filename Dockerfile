FROM python:3-alpine

WORKDIR /usr/src/app

COPY "requirements.txt" "plex-find-fixmatch.py" .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./plex-find-fixmatch.py" ]
