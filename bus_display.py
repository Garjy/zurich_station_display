#!/usr/bin/env python3
"""
Zurich Bus Display for Raspberry Pi
Displays real-time bus information for Mannessplatz stop in fullscreen mode
"""

import tkinter as tk
import requests
from datetime import datetime
import threading
import time
import configparser
import os


class BusDisplayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Zurich Bus Display")

        # Configure fullscreen
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#2B5DA0')

        # Allow ESC key to exit fullscreen (useful for testing)
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', True))

        # Load configuration
        self.load_config()

        # API Configuration
        self.api_url = "http://transport.opendata.ch/v1/stationboard"

        # Create UI
        self.create_widgets()

        # Start data fetching
        self.running = True
        self.fetch_data()

    def load_config(self):
        """Load configuration from config.ini file"""
        config = configparser.ConfigParser()

        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(script_dir, 'config.ini')

        # Default values
        self.station_name = "Mannessplatz"
        self.refresh_interval = 30
        self.max_buses = 20
        self.transport_type = "bus"

        try:
            if os.path.exists(config_file):
                config.read(config_file)

                # Read station configuration
                if config.has_section('Station'):
                    self.station_name = config.get('Station', 'name', fallback=self.station_name)

                # Read display configuration
                if config.has_section('Display'):
                    self.refresh_interval = config.getint('Display', 'refresh_interval', fallback=self.refresh_interval)
                    self.max_buses = config.getint('Display', 'max_buses', fallback=self.max_buses)

                # Read transport configuration
                if config.has_section('Transport'):
                    transport_type = config.get('Transport', 'type', fallback=self.transport_type).strip()
                    if transport_type.lower() in ['all', '']:
                        self.transport_type = None
                    else:
                        self.transport_type = transport_type

                print(f"Configuration loaded: Station='{self.station_name}', "
                      f"Refresh={self.refresh_interval}s, Transport={self.transport_type}")
            else:
                print(f"Config file not found at {config_file}, using defaults")
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")

    def create_widgets(self):
        """Create the UI components"""
        # Header with time and ZVV logo
        header_frame = tk.Frame(self.root, bg='#C8D7E5', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Time and date on the left side of header
        self.time_label = tk.Label(
            header_frame,
            text="",
            font=('Arial', 24, 'bold'),
            bg='#C8D7E5',
            fg='#2d3e50',
            anchor='w'
        )
        self.time_label.pack(side=tk.LEFT, padx=20, pady=10)

        # ZVV logo placeholder on the right
        zvv_label = tk.Label(
            header_frame,
            text="ZVV",
            font=('Arial', 20, 'bold'),
            bg='#C8D7E5',
            fg='#2d3e50',
            anchor='e'
        )
        zvv_label.pack(side=tk.RIGHT, padx=20, pady=10)

        # Column headers
        column_header_frame = tk.Frame(self.root, bg='#2B4F7C')
        column_header_frame.pack(fill=tk.X, pady=(0, 2))

        headers = [
            ("Linie\nLine", 0.15),
            ("Richtung\nDirection", 0.65),
            ("Abfahrt\nDeparture", 0.2)
        ]

        for text, width in headers:
            label = tk.Label(
                column_header_frame,
                text=text,
                font=('Arial', 11, 'bold'),
                bg='#2B4F7C',
                fg='#ffffff',
                anchor='w',
                justify=tk.LEFT
            )
            label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=8,
                      ipadx=int(width * 50))

        # Bus list frame (no scrollbar)
        self.scrollable_frame = tk.Frame(self.root, bg='#2B5DA0')
        self.scrollable_frame.pack(fill=tk.BOTH, expand=True)

        # Footer with touch screen message
        footer_frame = tk.Frame(self.root, bg='#2B4F7C', height=35)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)

        footer_left = tk.Label(
            footer_frame,
            text="Bitte Bildschirm berühren\nTouchez l'écran s'il vous plaît",
            font=('Arial', 8),
            bg='#2B4F7C',
            fg='#ffffff',
            anchor='w',
            justify=tk.LEFT
        )
        footer_left.pack(side=tk.LEFT, padx=15, pady=3)

        footer_right = tk.Label(
            footer_frame,
            text="Tocca lo schermo, per favore\nPlease touch the screen",
            font=('Arial', 8),
            bg='#2B4F7C',
            fg='#ffffff',
            anchor='e',
            justify=tk.RIGHT
        )
        footer_right.pack(side=tk.RIGHT, padx=15, pady=3)

    def fetch_data(self):
        """Fetch bus data from API in a separate thread"""
        if not self.running:
            return

        def fetch_thread():
            try:
                params = {
                    'station': self.station_name,
                    'limit': self.max_buses
                }

                # Add transport type filter if specified
                if self.transport_type:
                    # Handle multiple transport types
                    if ',' in self.transport_type:
                        for t_type in self.transport_type.split(','):
                            params['transportations[]'] = t_type.strip()
                    else:
                        params['transportations[]'] = self.transport_type

                response = requests.get(self.api_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                # Update UI in main thread
                self.root.after(0, self.update_display, data)

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.root.after(0, self.show_error, error_msg)

        # Start fetch in background thread
        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()

        # Schedule next refresh
        self.root.after(self.refresh_interval * 1000, self.fetch_data)

    def update_display(self, data):
        """Update the display with new bus data"""
        # Update current time and date
        now = datetime.now()
        time_date_str = now.strftime("%H:%M     %d.%m.%Y")
        self.time_label.config(text=time_date_str)

        # Clear existing bus entries
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Check if station was found
        if 'station' in data and data['station'] is None:
            error_label = tk.Label(
                self.scrollable_frame,
                text=f"Station '{self.station_name}' not found!",
                font=('Arial', 14, 'bold'),
                bg='#2B5DA0',
                fg='#ffffff'
            )
            error_label.pack(pady=20)

            help_label = tk.Label(
                self.scrollable_frame,
                text="Use find_station.py to search for the correct station name",
                font=('Arial', 10),
                bg='#2B5DA0',
                fg='#ffffff'
            )
            help_label.pack(pady=10)
            return

        # Check if we have data
        if 'stationboard' not in data or not data['stationboard']:
            no_data_label = tk.Label(
                self.scrollable_frame,
                text="No buses scheduled",
                font=('Arial', 12),
                bg='#2B5DA0',
                fg='#ffffff'
            )
            no_data_label.pack(pady=20)
            return

        # Display bus entries
        for i, bus in enumerate(data['stationboard']):
            self.create_bus_entry(bus, i)

    def create_bus_entry(self, bus, index):
        """Create a single bus entry row"""
        # Parse departure time
        departure_time = bus['stop']['departure']
        if departure_time:
            dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))

            # Calculate minutes until departure
            now = datetime.now(dt.tzinfo)
            minutes = int((dt - now).total_seconds() / 60)
            if minutes <= 0:
                time_display = "in 0'"
            else:
                time_display = f"in {minutes}'"
        else:
            time_display = "N/A"

        # Get bus information
        line = bus.get('number', 'N/A')
        destination = bus['to']

        # Create row frame with blue background
        row_frame = tk.Frame(self.scrollable_frame, bg='#2B5DA0')
        row_frame.pack(fill=tk.X, pady=1, padx=10)

        # Line number with gray box
        line_frame = tk.Frame(row_frame, bg='#7C7C7C', width=60)
        line_frame.pack(side=tk.LEFT, padx=(5, 10), pady=8)
        line_frame.pack_propagate(False)

        line_label = tk.Label(
            line_frame,
            text=line,
            font=('Arial', 14, 'bold'),
            bg='#7C7C7C',
            fg='#000000',
            anchor='center'
        )
        line_label.pack(expand=True, fill=tk.BOTH)

        # Accessibility icon (wheelchair symbol)
        accessibility_label = tk.Label(
            row_frame,
            text="♿",
            font=('Arial', 12),
            bg='#2B5DA0',
            fg='#ffffff',
            anchor='center',
            width=2
        )
        accessibility_label.pack(side=tk.LEFT, padx=(0, 10))

        # Destination
        dest_label = tk.Label(
            row_frame,
            text=destination,
            font=('Arial', 14),
            bg='#2B5DA0',
            fg='#ffffff',
            anchor='w'
        )
        dest_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Departure time
        time_label = tk.Label(
            row_frame,
            text=time_display,
            font=('Arial', 14, 'bold'),
            bg='#2B5DA0',
            fg='#ffffff',
            anchor='e',
            width=10
        )
        time_label.pack(side=tk.RIGHT, padx=10)

    def show_error(self, error_msg):
        """Display error message"""
        # Clear existing entries
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        error_label = tk.Label(
            self.scrollable_frame,
            text=f"{error_msg}",
            font=('Arial', 14),
            bg='#2B5DA0',
            fg='#ffffff'
        )
        error_label.pack(pady=20)

    def on_closing(self):
        """Clean up when closing the application"""
        self.running = False
        self.root.destroy()


def main():
    root = tk.Tk()
    app = BusDisplayApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
