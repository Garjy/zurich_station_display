#!/bin/bash
# Installation script for Zurich Bus Display

echo "=========================================="
echo "Zurich Bus Display - Installation Script"
echo "=========================================="
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies"
    exit 1
fi

# Make the script executable
echo "Making bus_display.py executable..."
chmod +x "$SCRIPT_DIR/bus_display.py"

echo ""
echo "Installation complete!"
echo ""
echo "To run the application:"
echo "  python3 $SCRIPT_DIR/bus_display.py"
echo ""
echo "To enable auto-start on boot:"
echo "  1. Edit bus-display.service and update paths"
echo "  2. sudo cp $SCRIPT_DIR/bus-display.service /etc/systemd/system/"
echo "  3. sudo systemctl enable bus-display.service"
echo "  4. sudo systemctl start bus-display.service"
echo ""
