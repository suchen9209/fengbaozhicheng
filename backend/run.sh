#!/bin/bash

# Create necessary directories
mkdir -p data logs uploads

# Run the FastAPI application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
