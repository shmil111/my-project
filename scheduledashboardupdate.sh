#!/bin/bash
# Script to schedule the API status dashboard update via cron

# Get the absolute path of the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
UPDATE_SCRIPT="$SCRIPT_DIR/update_dashboard.sh"

# Make the update script executable if it's not already
if [ ! -x "$UPDATE_SCRIPT" ]; then
    chmod +x "$UPDATE_SCRIPT"
    echo "Made update_dashboard.sh executable"
fi

# Check if the update script exists
if [ ! -f "$UPDATE_SCRIPT" ]; then
    echo "Error: Cannot find update_dashboard.sh at $UPDATE_SCRIPT"
    exit 1
fi

# Create temporary file for the new crontab
TEMP_CRON=$(mktemp)

# Export current crontab
crontab -l > "$TEMP_CRON" 2>/dev/null

# Check if the cron job already exists
if grep -q "update_dashboard.sh" "$TEMP_CRON"; then
    echo "Cron job for API Status Dashboard update already exists."
    echo "Current crontab entry:"
    grep "update_dashboard.sh" "$TEMP_CRON"
else
    # Add the new cron job to run every hour
    echo "# Update API Status Dashboard every hour" >> "$TEMP_CRON"
    echo "0 * * * * $UPDATE_SCRIPT > $SCRIPT_DIR/dashboard_update.log 2>&1" >> "$TEMP_CRON"
    
    # Install the new crontab
    crontab "$TEMP_CRON"
    
    echo "Cron job added to update the API Status Dashboard every hour"
    echo "Next update will run at the top of the next hour"
fi

# Remove the temporary file
rm "$TEMP_CRON"

# Offer to run the update immediately
read -p "Do you want to update the dashboard now? (y/n) " RUN_NOW
if [[ "$RUN_NOW" == "y" || "$RUN_NOW" == "Y" ]]; then
    echo "Running update_dashboard.sh..."
    "$UPDATE_SCRIPT"
    echo "Update completed."
fi 