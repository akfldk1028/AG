#!/usr/bin/env python
"""Start AutoGen Studio with CORS enabled for Auto-Claude"""
import os
import sys

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = r"D:\Data\25_ACE\AG\autogen_a2a_kit\.env"
load_dotenv(env_path)
print(f"Loaded environment from: {env_path}")
print(f"OPENAI_API_KEY set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")

# Add the package to path
sys.path.insert(0, r"D:\Data\25_ACE\AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio")
# AG_Cohub (Claude Max OAuth 모델 지원)
sys.path.insert(0, r"D:\Data\25_ACE\AG\autogen_a2a_kit")

# Set working directory
os.chdir(r"D:\Data\25_ACE\AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio")

# Start the server
from autogenstudio.web.app import app
import uvicorn

if __name__ == "__main__":
    print("Starting AutoGen Studio on port 8081...")
    print("CORS enabled for: localhost:5173 (Auto-Claude)")
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="info")
