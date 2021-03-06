# Copyright (c) 2015 ThoughtWorks
#
# See the file LICENSE for copying permission.

import flask
from openahjo_activity_streams import convert
import requests
import logging
import json

OPENAHJO_URL = 'http://dev.hel.fi/paatokset/v1/agenda_item/?order_by=-last_modified_time'


def create_app(remote_url=OPENAHJO_URL, converter=convert.to_activity_stream):
    logging.basicConfig(level=logging.INFO)
    application = flask.Flask(__name__)
    application.config['REMOTE_URL'] = remote_url
    application.config['CONVERTER'] = converter

    @application.route('/')
    def show_something():
        openahjo_data = requests.get(application.config['REMOTE_URL'])
        converted_data = application.config['CONVERTER'](openahjo_data.json())
        return application.response_class(json.dumps(converted_data), mimetype='application/activity+json')

    return application

application = create_app()
if __name__ == '__main__':
    application.run()
