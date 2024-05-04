#!/bin/bash

# Define the database path
DATABASE="accounts.db"

# Check if the database already exists
if [ -f "$DATABASE" ]; then
    echo "Database already exists."
else
    echo "Creating database and setting up the structure."

    # Create the database and the accounts table
    sqlite3 $DATABASE <<EOF
CREATE TABLE accounts (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    inventory TEXT
);
EOF

    echo "Database created and table set up successfully."
fi

