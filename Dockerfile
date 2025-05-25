FROM python:3.12.3

WORKDIR /srv

COPY ./requirements.txt /srv/requirements.txt
RUN pip install -r /srv/requirements.txt

COPY ./ /srv/
ENV PATH "$PATH:/srv/scripts"