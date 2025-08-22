#!/bin/bash
gunicorn --bind 0.0.0.0:$PORT render_app:app
