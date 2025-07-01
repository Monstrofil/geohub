#!/bin/bash

aerich upgrade

uvicorn main:app --host 0.0.0.0 --port 8000