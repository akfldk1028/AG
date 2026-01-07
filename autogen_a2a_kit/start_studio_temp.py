import sys
import os

# Add autogen-studio to path
studio_path = r"D:\Data\22_AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio"
sys.path.insert(0, studio_path)
os.chdir(studio_path)

from autogenstudio.web.app import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081)
