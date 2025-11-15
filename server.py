#!/usr/bin/env python3
"""
FastAPI server for presentation
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

# Serve static files from build directory
app.mount("/", StaticFiles(directory="build", html=True), name="build")
