import tornado.ioloop
import tornado.web

from datetime import timedelta
import requests
import time
import json

from pms7003 import Pms7003Thread

import logging
import sys


class ValueHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(sensor.measurements)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        m = sensor.measurements

        self.render(
            "main.html", pollutants=list(m.keys()), values=[m["pm10"], m["pm2_5"]]
        )


def make_app():

    handlers = [(r"/measurements/?", ValueHandler), (r"/?", MainHandler)]

    return tornado.web.Application(handlers, debug=True)


def send_measurement():
    try:
        logging.debug(str(sensor.measurements))
        request_fields = {}
        request_fields["timestamp"] = time.time()
        request_fields["values"] = sensor.measurements
        r = requests.post(
            config["uri"] + "/nodes/" + config["node_id"] + "/measurements/",
            headers={"Content-Type": "application/json"},
            json=request_fields,
            timeout=3,
        )
    except requests.exceptions.ConnectionError as e:
        logging.error(e)
        logging.error("Connection error. Backend down?")
    finally:
        tornado.ioloop.IOLoop.instance().add_timeout(
            timedelta(seconds=1), send_measurement
        )


if __name__ == "__main__":

    # get config
    with open("/home/pi/smokey/config.json", "r") as f:
        config = json.loads(f.read())

    # setup logging
    if config["log_file"]:
        logging.basicConfig(
            filename=config["log_file"],
            level=logging.DEBUG,
            format="%(asctime)-15s %(levelname)s %(message)s",
        )
    else:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.DEBUG,
            format="%(asctime)-15s %(levelname)s %(message)s",
        )

    # run application
    with Pms7003Thread(config["serial_port"]) as sensor:
        send_measurement()
        app = make_app()
        app.listen(8888)
        tornado.ioloop.IOLoop.current().start()
