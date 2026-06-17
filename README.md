# Temp Mail scraper

## Environment Setup
Create a `.env` file in the root directory and configure it based on the provided template:
```bash
cp .env.dist .env
```

## Build and Run
Run the following command to build the Docker images and start all services in the background:
```bash
docker compose up -d --build
```

## API Documentation
Once the application is running, you can access the API

## Swagger UI
```
http://127.0.0.1:8000/docs
```

## CAMOUFOX
I decided to use Camoufox because it helps prevent CAPTCHA detection, but for better results it is recommended to run it with a proxy.

## Troubleshooting
If you encounter an `anti_bot_challenge` error, stop the application, complete the CAPTCHA locally on your computer, and then start the application again.
