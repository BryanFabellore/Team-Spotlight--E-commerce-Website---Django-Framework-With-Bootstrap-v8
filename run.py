import subprocess
import sys
import os

# Replace 'env' with the actual name of your virtual environment if it's different
venv_path = "D:\\Projects\\SOFTDEV\\FCHUB-REVISIONV6\\venv"
web_directory = "D:\\Projects\\SOFTDEV\\FCHUB-REVISIONV6\\web"

# Activate the virtual environment
activate_command = f"{venv_path}\\Scripts\\activate"

try:
    subprocess.run(activate_command, shell=True, check=True)
except subprocess.CalledProcessError:
    sys.exit("Error: Failed to activate the virtual environment. Check the path to your virtual environment.")

# Change to the web directory
os.chdir(web_directory)

# Run the Django development server
runserver_command = "py manage.py runserver"

try:
    subprocess.run(runserver_command, shell=True, check=True)
except subprocess.CalledProcessError:
    sys.exit("Error: Failed to run the Django development server. Make sure Django is installed in your virtual environment.")
