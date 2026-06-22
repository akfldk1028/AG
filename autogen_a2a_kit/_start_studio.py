import sys
sys.argv = ["autogenstudio", "ui", "--port", "8081"]
from autogenstudio.cli import app
app()
