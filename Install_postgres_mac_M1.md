
Installation and Setup Steps

    1.  Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    2.  Install PostgreSQL 14 via Homebrew

brew install postgresql@14


    3.  Initialize the Homebrew Environment (if not already done)
Add Homebrew to your shell environment:

echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"


    4.  Start PostgreSQL via Homebrew Services

brew services start postgresql@14

Verify:

brew services list

Ensure postgresql@14 shows as “started” or similar.

    5.  Stop Existing Postgres Services (If Needed)
If you need to stop and manage Postgres manually:

brew services stop postgresql@14


    6.  (Re)Initialize the PostgreSQL Data Directory
If you need to start fresh and the directory already exists, remove it first:

sudo rm -rf /usr/local/var/postgres

Then recreate it and set correct permissions:

sudo mkdir -p /usr/local/var/postgres
sudo chown -R $(whoami) /usr/local/var/postgres
chmod 700 /usr/local/var/postgres

Now initialize:

initdb -D /usr/local/var/postgres

This should complete without permission errors.

    7.  Start PostgreSQL Server Manually (If Not Using brew services)

pg_ctl -D /usr/local/var/postgres start

Or, if you prefer Brew services:

brew services start postgresql@14


    8.  Verify the PostgreSQL Server is Running

pg_ctl -D /usr/local/var/postgres status

Or simply try:

psql postgres

If you connect successfully, the server is running.

    9.  Create postgres Role with Password and Superuser Privileges
Once in psql (using psql postgres):

CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD '<password>';

Replace <password> with your desired password.
Then create a database:

CREATE DATABASE vectordb;


    10. Install pgvector Extension

cd /tmp
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

After installing, connect to your vectordb database:

psql --host localhost --username postgres --dbname vectordb

Enable the vector extension:

CREATE EXTENSION IF NOT EXISTS vector;

This should successfully load pgvector into vectordb.

Troubleshooting Steps

    1.  Permission Errors During initdb
If you see error: could not change permissions of directory ...: Operation not permitted, ensure the directory /usr/local/var/postgres is owned by your user and has correct permissions:

sudo chown -R $(whoami) /usr/local/var/postgres
chmod 700 /usr/local/var/postgres

Then run:

initdb -D /usr/local/var/postgres


    2.  Cannot Run initdb as root
If you run initdb with sudo or as root, it will fail. Run initdb as the non-root user who will own the server process.
    3.  Directory Already Exists
If initdb complains the directory is not empty, remove it if you want a fresh start:

sudo rm -rf /usr/local/var/postgres

Then recreate, adjust permissions, and re-run initdb.

    4.  Postgres Service Conflicts
If you have multiple versions of PostgreSQL running (e.g., different ports), ensure only one instance is running on port 5432, or adjust postgresql.conf to use a different port. Use:

lsof -i :5432

to identify processes occupying port 5432, and stop or kill as needed.

    5.  Check Server Status and Logs
If pg_ctl indicates a failure, check the log file you passed with -l logfile or inspect /usr/local/var/postgres/server.log if it exists. This may provide clues on what’s wrong.

