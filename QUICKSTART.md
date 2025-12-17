# Quick Start Guide

Get your Zurich bus display up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd zurich_bus_display
pip3 install -r requirements.txt
```

Or use the install script:
```bash
./install.sh
```

## Step 2: Find Your Station

Search for your bus stop:

```bash
python3 find_station.py "your station name"
```

Example:
```bash
python3 find_station.py "Zürich HB"
```

## Step 3: Configure

Edit `config.ini` and update the station name:

```ini
[Station]
name = Zürich HB
```

## Step 4: Test

Test the API connection:

```bash
python3 test_api.py
```

If you see bus departures, you're good to go!

## Step 5: Run

Start the fullscreen application:

```bash
python3 bus_display.py
```

Press `ESC` to exit fullscreen mode.

## Optional: Auto-Start on Boot

To run automatically when your Raspberry Pi starts:

1. Edit `bus-display.service` and update paths
2. Install the service:
```bash
sudo cp bus-display.service /etc/systemd/system/
sudo systemctl enable bus-display.service
sudo systemctl start bus-display.service
```

## Troubleshooting

**Station not found?**
- Use `find_station.py` to search for stations
- Try adding "Zürich," before the station name
- Check spelling

**No display?**
```bash
export DISPLAY=:0
python3 bus_display.py
```

**Need help?**
See the full README.md for detailed documentation.
