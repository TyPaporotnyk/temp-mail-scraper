from fastapi import FastAPI

swagger_ui_parameters = {
    "persistAuthorization": True,
    "displayRequestDuration": True,
    "tryItOutEnabled": True,
}

app = FastAPI(
    title="Temp Mail scraper api",
    description="Temp Mail scraper api",
    docs_url="/docs",
    swagger_ui_parameters=swagger_ui_parameters,
)
