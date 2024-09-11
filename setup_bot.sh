#!/bin/bash

echo -e "\e[32m

████████  █████  ███    ███       ██████   ██████  ████████ ███████ 
   ██    ██   ██ ████  ████       ██   ██ ██    ██    ██    ██      
   ██    ███████ ██ ████ ██ █████ ██████  ██    ██    ██    ███████ 
   ██    ██   ██ ██  ██  ██       ██   ██ ██    ██    ██         ██ 
   ██    ██   ██ ██      ██       ██████   ██████     ██    ███████ 
                                                                    
\033[0m"

# Update package list
sudo apt-get update

# Install git if not installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Installing Git..."
    sudo apt-get install -y git
else
    echo "Git is already installed."
fi

# Clone the project from GitHub
if [ ! -d "Devops-Oncall-Bot" ]; then
    echo "Cloning the project from GitHub..."
    git clone https://github.com/amsepahvand/Devops-Oncall-Bot.git
else
    echo "Project already cloned."
fi

cd Devops-Oncall-Bot

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker is already installed."
fi

# Install SQLite3 if not installed
if ! command -v sqlite3 &> /dev/null; then
    echo "SQLite3 is not installed. Installing SQLite3..."
    sudo apt-get install -y sqlite3
else
    echo "SQLite3 is already installed."
fi

# Check if the database file exists
if [ ! -f "bot-db.db" ]; then
    echo "Creating database and tables..."

    # Create the database and tables using SQLite commands
    sqlite3 bot-db.db <<EOF
CREATE TABLE IF NOT EXISTS user_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    message TEXT,
    persian_date TEXT,
    status TEXT,
    created_date DATE,
    seen_date DATE,
    assignie TEXT,
    jira_issue_key TEXT
);
CREATE TABLE IF NOT EXISTS jira_ticketing_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jira_base_url TEXT,
    username TEXT,
    password TEXT ,
    send_to_jira INTEGER DEFAULT 0,
    project_key TEXT
);

CREATE TABLE IF NOT EXISTS oncall_staff (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    username TEXT
);

CREATE TABLE IF NOT EXISTS user_state (
    user_id INTEGER PRIMARY KEY,
    state TEXT,
    message TEXT
);

CREATE TABLE IF NOT EXISTS bot_owner (
    user_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS oncall_group (
    group_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS bot_api_token (
    token TEXT
);

CREATE TABLE IF NOT EXISTS schedule_setting (
    setting_value INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS oncall_history (
    name TEXT,
    username TEXT,
    date TEXT UNIQUE
);
EOF

    echo "Database and tables created successfully."
else
    echo "Database already exists."
fi


get_user_input() {
    local prompt="$1"
    local input=""
    local attempts=0
    local max_attempts=3

    while [ $attempts -lt $max_attempts ]; do
        read -p "$prompt" input
        if [[ -n "$input" ]]; then
            echo "$input"
            return
        else
            echo "Input cannot be empty. Please try again."
            attempts=$((attempts + 1))
        fi
    done

    echo "Maximum attempts reached. Exiting installation."
    exit 1
}

BOT_API_TOKEN=$(get_user_input "Please enter your Telegram Bot API token: ")
ADMIN_USER_ID=$(get_user_input "Please enter the admin Telegram user ID: ")
ONCALL_GROUP_ID=$(get_user_input "Please enter the oncall group ID: ")

sqlite3 bot-db.db "INSERT OR REPLACE INTO bot_api_token (token) VALUES ('$BOT_API_TOKEN');"
sqlite3 bot-db.db "INSERT OR REPLACE INTO bot_owner (user_id) VALUES ('$ADMIN_USER_ID');"
sqlite3 bot-db.db "INSERT OR REPLACE INTO oncall_group (group_id) VALUES ('$ONCALL_GROUP_ID');"

sudo docker compose up -d

echo "Installation complete! The bot is now running. Enjoy it ;)"
