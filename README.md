# Setting Up Solar Billing Management System

## Code Deployment and Configuration

1. Install the following packages on the GCP server:

    ```bash
    sudo apt-get update
    sudo apt-get install git -y
    sudo apt-get install python3-pip python3-venv -y
    ```

2. Clone the repository and navigate to the project directory:

    ```bash
    git clone https://github.com/AlaskanTuna/billing-management-system.git
    cd billing-management-system
    ```

3. Create virtual environment at the root directory:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

4. Create `.env` file at root directory with the following format:
    > **Note:** The provided credentials is for the central database table that collects energy readings from all customers.

    ```bash
    # DATABASE CREDENTIALS
    DB_HOST = ""
    DB_PORT = ""
    DB_NAME = ""
    DB_TABLE_NAME = ""
    DB_USERNAME = ""
    DB_PASSWORD = ""

    # SECRET KEYS

    API_SECRET_KEY = ""
    ```

## Hosting the Webapp on GCP

1. Create the `systemd` file with the following content:

    ```bash
    sudo nano /etc/systemd/system/sbms.service

    # Inside the file
    [Unit]
    Description=Solar Billing Management System
    After=network.target

    [Service]
    User=[your_user] 
    Group=[your_group]
    WorkingDirectory=/home/[your_user]/billing-management-system
    Environment="PATH=/home/[your_user]/billing-management-system/venv/bin"
    ExecStart=/home/[your_user]/billing-management-system/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 src.webapp:app
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

2. Reload `systemd` and start the service:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl start sbms
    sudo systemctl enable sbms

    # Check the status of the service
    sudo systemctl status sbms --no-pager -l

    # View continuous logs of the service
    sudo journalctl -u sbms -f
    ```