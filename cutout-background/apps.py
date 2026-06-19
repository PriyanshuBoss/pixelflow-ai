import logging

from flask import Flask

from common.config import Config

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route("/")
def index():
    return "Background Removal Service Ready"

if __name__ == '__main__':
    logger.info(f"Starting Flask application on port {Config.PORT} with debug={Config.DEBUG}")
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
