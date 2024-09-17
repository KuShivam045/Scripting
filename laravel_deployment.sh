#!/bin/bash

# Define variables
PROJECT_DIR="/home/rigmeds/Downloads/SocioPro/Sociopro_Dev"
BRANCH="dev"
SERVICE_NAME="sociopro.service"

# Add the directory as a safe directory
git config --global --add safe.directory "$PROJECT_DIR"

echo "Navigating to $PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

echo "Stashing untracked files"
git stash push --include-untracked || exit 1

echo "Pulling the latest changes from the remote repository"
git fetch origin "$BRANCH" || exit 1
git pull --rebase origin "$BRANCH" || exit 1
git reset --hard origin/"$BRANCH" || exit 1

echo "Putting the application into maintenance mode"
php artisan down || exit 1

echo "Updating Composer dependencies"
composer install --no-dev --optimize-autoloader || exit 1

echo "Running Laravel optimizations"
php artisan optimize:clear || exit 1

echo "not Running database migrations because project does not have any migration file"
#php artisan migrate --force || exit 1

echo "Restarting the application service"
#sudo systemctl restart "$SERVICE_NAME" || exit 1

echo "Setting proper permissions"
#sudo chown -R www-data:www-data storage bootstrap/cache || exit 1
#sudo chmod -R 775 storage bootstrap/cache || exit 1

echo "Bringing the application back online"
php artisan up || exit 1

echo "Deployment completed successfully."
