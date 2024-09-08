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

if [ ! -f "bot-db.db" ]; then
    echo "Creating database and tables..."

    # Create the database and tables using SQLite commands
    sqlite3 bot-db.db <<EOF
CREATE TABLE IF NOT EXISTS user_message (
    user_id INTEGER,
    username TEXT,
    message TEXT,
    persian_date TEXT
);

CREATE TABLE IF NOT EXISTS oncall_staff (
    user_id INTEGER PRIMARY KEY,
    username TEXT
);

CREATE TABLE IF NOT EXISTS user_state (
    user_id INTEGER PRIMARY KEY,
    state TEXT NOT NULL,
    message TEXT
);

CREATE TABLE IF NOT EXISTS bot_owner (
    user_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS bot_api_token (
    token TEXT
);
EOF

    echo "Database and tables created successfully."
else
    echo "Database already exists."
fi

# Function to get user input with validation
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

# Prompt for user input
BOT_API_TOKEN=$(get_user_input "Please enter your Telegram Bot API token: ")
ADMIN_USER_ID=$(get_user_input "Please enter the admin Telegram user ID: ")

# Store the API token and admin user ID in the database
sqlite3 bot-db.db "INSERT OR REPLACE INTO bot_api_token (token) VALUES ('$BOT_API_TOKEN');"
sqlite3 bot-db.db "INSERT OR REPLACE INTO bot_owner (user_id) VALUES ('$ADMIN_USER_ID');"

# Run Docker Compose
sudo docker compose up -d

echo "Installation complete! The bot is now running. Enjoy it ;)"
