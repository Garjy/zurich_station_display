# Zurich Bus Display for Raspberry Pi

A fullscreen desktop application that displays real-time bus information for any selected bus/tram stop in Zurich, Switzerland.

## Features

- Real-time bus departure times from configured station
- Automatically refreshes every 30 seconds
- Fullscreen display optimized for 3.5-inch touchscreen
- Shows departure time, bus line number, destination, and platform
- Displays countdown in minutes until departure
- Dark theme for easy visibility

## Requirements

- Raspberry Pi (any model)
- 3.5-inch LCD Touchscreen
- Python 3.7 or higher
- Internet connection

## Installation

### 1. Install Dependencies

```bash
cd zurich_bus_display
pip3 install -r requirements.txt
```

### 2. Make the Script Executable

```bash
chmod +x bus_display.py
```

### 3. Test the Application

```bash
python3 bus_display.py
```

## Configuration

Before running the application, you need to find the correct station name.

### Find Your Station

The default station "Paradplatz" may not exist. Use the station finder tool:

```bash
python3 find_station.py "your station name"
```

Examples:
```bash
python3 find_station.py "Zürich HB"
python3 find_station.py "Bellevue"
python3 find_station.py "Paradeplatz"
```

### Configure Your Station

Once you find your station, edit the `config.ini` file:

```ini
[Station]
name = Zürich, Bellevue

[Display]
refresh_interval = 30
max_buses = 20

[Transport]
type = bus
```

Configuration options:
- **Station name**: The exact station name from the finder tool
- **Refresh interval**: How often to fetch new data (in seconds)
- **Max buses**: Maximum number of buses to display
- **Transport type**: Filter by type (bus, tram, train, ship) or "all" for everything

## Usage

### Manual Start

```bash
python3 /path/to/zurich_bus_display/bus_display.py
```

### Keyboard Shortcuts

- **ESC**: Exit fullscreen mode
- **F11**: Enter fullscreen mode

### Auto-Start on Boot

To make the application start automatically when the Raspberry Pi boots:

1. Copy the systemd service file:
```bash
sudo cp bus-display.service /etc/systemd/system/
```

2. Edit the service file to match your setup:
```bash
sudo nano /etc/systemd/system/bus-display.service
```

Update the paths and username as needed.

3. Enable and start the service:
```bash
sudo systemctl enable bus-display.service
sudo systemctl start bus-display.service
```

4. Check the status:
```bash
sudo systemctl status bus-display.service
```

## Customization

All customization can be done through the `config.ini` file:

### Change Station

1. Find your station using the finder tool:
```bash
python3 find_station.py "Station Name"
```

2. Edit `config.ini`:
```ini
[Station]
name = Zürich, Bellevue
```

### Adjust Refresh Interval

Edit the refresh interval in `config.ini` (in seconds):

```ini
[Display]
refresh_interval = 60
```

### Filter Different Transport Types

Change the transport type in `config.ini`:

```ini
[Transport]
# For only buses
type = bus

# For buses and trams
type = bus,tram

# For all transport types
type = all
```

Available types: `bus`, `tram`, `train`, `ship`, `cableway`

### Adjust Maximum Buses Displayed

Change the max_buses setting in `config.ini`:

```ini
[Display]
max_buses = 30
```

### Adjust Display Size

The application automatically adapts to your screen size. For better visibility on small screens, you can adjust font sizes in the `bus_display.py` file in the `create_widgets` method.

### Create custom service to run at startup sudo nano 
/etc/systemd/system/zurich-station-display.service 

Paste this (edit  User= and the script path as needed):
```ini
[Unit]
Description=Zurich station display
After=network-online.target graphical.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment=DISPLAY=:0
ExecStart=/usr/bin/python3 /home/pi/zurich_station_display/bus_display.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Display Issues

If the display doesn't appear correctly on your touchscreen:

1. Make sure X11 is running:
```bash
export DISPLAY=:0
python3 bus_display.py
```

2. Check your screen resolution:
```bash
xrandr
```

### API Connection Issues

If you see "Error" messages:

1. Check your internet connection
2. Verify the station name is correct
3. Test the API manually:
```bash
curl "http://transport.opendata.ch/v1/stationboard?station=Paradeplatz&transportations[]=bus&limit=5"
```

### No Buses Showing

This could mean:
- No buses are scheduled for the current time
- The station name is incorrect
- Try removing the transport filter to see all types

## API Information

This application uses the free Transport API for Switzerland:
- **API**: http://transport.opendata.ch/
- **Documentation**: https://transport.opendata.ch/docs.html
- **Data**: Real-time public transport data for Switzerland

## License

MIT License - Feel free to modify and use as needed.
