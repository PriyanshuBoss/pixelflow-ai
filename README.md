# PixelFlow AI

PixelFlow AI is a collection of serverless AI-powered services built on AWS Lambda for image generation, video creation, brand automation, background removal, and trend intelligence.

Each service is designed as an independent Lambda function and can be deployed separately depending on your requirements.

---

## Features

### Brand Studio

Generate brand kits, marketing assets, brand identities, and creative content using AI models and external services.

### Cutout Background

Remove image backgrounds and perform image cleanup operations.

### Image Generation

Generate AI-powered images from prompts using modern multimodal models.

### Trend Intelligence

Analyze market and industry trends to generate insights for brands, creators, and marketers.

### Video Generation

Create AI-generated videos, video advertisements, and marketing content using AI workflows and Google Flow services.

---

## Project Structure

```text
pixelflow-ai
├── brand-studio
├── common
├── cutout-background
├── image-generation
├── trend-intelligence
├── video-generation
├── tests
└── README.md
```

---

## Architecture

This repository contains multiple independent AWS Lambda services.

Each directory represents a standalone Lambda function with its own:

* Source code
* Dependencies
* Environment variables
* Deployment configuration
* Third-party integrations

Services can be developed, deployed, and scaled independently.

---

## Prerequisites

* Python 3.10+
* AWS Lambda
* AWS IAM
* AWS S3
* AWS CloudWatch
* AWS Secrets Manager (recommended)
* Access to required AI providers (depending on the service)

---

## Environment Configuration

This repository does **not** include environment files or credentials.

Each Lambda service requires its own `.env` configuration.

Example:

```env
OPENAI_API_KEY=your_api_key
GEMINI_API_KEY=your_api_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket
```

Create a separate `.env` file inside each service directory:

```text
brand-studio/.env
cutout-background/.env
image-generation/.env
trend-intelligence/.env
video-generation/.env
```

The required variables may differ between services.

---

## Google Service Account Configuration

The `video-generation` service uses Google Flow / Google Cloud services and requires a Google Service Account credential file.

Create a Service Account in Google Cloud and download the JSON credentials file.

Place the file inside the `video-generation` directory:

```text
video-generation
├── google_sa.json
├── lambda_function.py
├── requirements.txt
└── .env
```

Set the credential path using:

```env
GOOGLE_APPLICATION_CREDENTIALS=./google_sa.json
```

### Important

* Generate your own credentials.
* Do not commit `google_sa.json`.
* Use least-privilege permissions.
* Store credentials securely.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/pixelflow-ai.git
cd pixelflow-ai
```

Install dependencies for a specific service:

```bash
cd image-generation
pip install -r requirements.txt
```

Configure the required environment variables and run locally.

---

## Local Development

Example:

```bash
cd image-generation

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
```

Update the `.env` file with your credentials and configuration values.

---

## Deployment

Each folder is intended to be deployed as an independent AWS Lambda function.

Deployment options include:

* AWS Console
* AWS SAM
* AWS CDK
* Terraform
* Serverless Framework

Configure environment variables and IAM permissions before deployment.

---

## Security

Never commit:

```text
.env
*.env
google_sa.json
*.pem
*.key
```

Also avoid committing:

* API keys
* AWS credentials
* Service account credentials
* Production configuration files
* Customer data
* Secrets Manager values

Recommended `.gitignore`:

```gitignore
# Environment
.env
*.env

# Google Credentials
google_sa.json

# Secrets
*.pem
*.key

# Python
__pycache__/
*.pyc

# Virtual Environments
venv/
.envrc
```

---

## Testing

Run tests using:

```bash
pytest
```

Or execute tests within a specific service directory.

---

## Technology Stack

* Python
* AWS Lambda
* AWS S3
* AWS IAM
* Google Cloud
* Google Flow
* OpenAI
* Gemini
* REST APIs

---

## Disclaimer

This repository is provided for educational, experimentation, and demonstration purposes.

Users are responsible for:

* Managing their own cloud resources
* Configuring environment variables
* Securing credentials
* Complying with third-party API terms of service

---

## License

MIT License

```
Copyright (c) 2025 PixelFlow AI
```
