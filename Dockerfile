FROM python

COPY ./app /app
WORKDIR /app
COPY requirements.txt /requirements.txt
RUN python3 -m pip install -r /requirements.txt
ENTRYPOINT [ "python3" ]
CMD [ "app_wbg.py" ]