import os

class Config:
    """Application configuration settings."""

    # Server settings
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('FLASK_ENV', 'production') == 'development'

    # Storage settings
    IMAGE_DIR = os.environ.get('IMAGE_DIR', './image_dir')
    MAX_IMAGE_DIMENSION = int(os.environ.get('MAX_IMAGE_DIMENSION', 1000))

    # S3 settings
    S3_BUCKET = os.environ.get('S3_BUCKET', 'default-bucket')

    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', './logs')
