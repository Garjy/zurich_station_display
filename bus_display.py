#!/usr/bin/env python3
"""
Zurich Bus Display for Raspberry Pi
Displays real-time bus information for Mannessplatz stop in fullscreen mode
"""

import tkinter as tk
from tkinter import ttk
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
        self.root.configure(bg='#1a1a1a')

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
        # Title
        title_frame = tk.Frame(self.root, bg='#2d2d2d')
        title_frame.pack(fill=tk.X, pady=5)

        title_label = tk.Label(
            title_frame,
            text=f"🚌 {self.station_name}",
            font=('Arial', 16, 'bold'),
            bg='#2d2d2d',
            fg='#ffffff'
        )
        title_label.pack(pady=5)

        # Current time
        self.time_label = tk.Label(
            title_frame,
            text="",
            font=('Arial', 10),
            bg='#2d2d2d',
            fg='#cccccc'
        )
        self.time_label.pack()

        # Separator
        separator = tk.Frame(self.root, height=2, bg='#444444')
        separator.pack(fill=tk.X, padx=10)

        # Header row
        header_frame = tk.Frame(self.root, bg='#1a1a1a')
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        headers = [
            ("Time", 0.2),
            ("Line", 0.15),
            ("Destination", 0.5),
            ("Platform", 0.15)
        ]

        for text, width in headers:
            label = tk.Label(
                header_frame,
                text=text,
                font=('Arial', 10, 'bold'),
                bg='#1a1a1a',
                fg='#888888',
                anchor='w'
            )
            label.pack(side=tk.LEFT, fill=tk.X, expand=True,
                      padx=2, ipadx=int(width * 100))

        # Scrollable frame for bus list
        self.canvas = tk.Canvas(self.root, bg='#1a1a1a', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#1a1a1a')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.scrollbar.pack(side="right", fill="y")

        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Loading...",
            font=('Arial', 8),
            bg='#2d2d2d',
            fg='#888888'
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

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
        # Update current time
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=current_time)

        # Clear existing bus entries
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Check if station was found
        if 'station' in data and data['station'] is None:
            error_label = tk.Label(
                self.scrollable_frame,
                text=f"Station '{self.station_name}' not found!",
                font=('Arial', 14, 'bold'),
                bg='#1a1a1a',
                fg='#ff5555'
            )
            error_label.pack(pady=20)

            help_label = tk.Label(
                self.scrollable_frame,
                text="Use find_station.py to search for the correct station name",
                font=('Arial', 10),
                bg='#1a1a1a',
                fg='#888888'
            )
            help_label.pack(pady=10)

            self.status_label.config(text=f"Station not found: {self.station_name}", fg='#ff5555')
            return

        # Check if we have data
        if 'stationboard' not in data or not data['stationboard']:
            no_data_label = tk.Label(
                self.scrollable_frame,
                text="No buses scheduled",
                font=('Arial', 12),
                bg='#1a1a1a',
                fg='#888888'
            )
            no_data_label.pack(pady=20)
            self.status_label.config(text=f"Last updated: {current_time} - No data", fg='#888888')
            return

        # Display bus entries
        for i, bus in enumerate(data['stationboard']):
            self.create_bus_entry(bus, i)

        # Update status
        bus_count = len(data['stationboard'])
        self.status_label.config(
            text=f"Last updated: {current_time} - Showing {bus_count} buses",
            fg='#888888'
        )

    def create_bus_entry(self, bus, index):
        """Create a single bus entry row"""
        # Parse departure time
        departure_time = bus['stop']['departure']
        if departure_time:
            dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M")

            # Calculate minutes until departure
            now = datetime.now(dt.tzinfo)
            minutes = int((dt - now).total_seconds() / 60)
            if minutes < 0:
                time_display = time_str
            elif minutes == 0:
                time_display = "Now"
            else:
                time_display = f"{time_str} ({minutes}m)"
        else:
            time_display = "N/A"

        # Get bus information
        line = bus.get('number', 'N/A')
        destination = bus['to']
        platform = bus['stop'].get('platform', '-')

        # Create row frame
        bg_color = '#252525' if index % 2 == 0 else '#1a1a1a'
        row_frame = tk.Frame(self.scrollable_frame, bg=bg_color)
        row_frame.pack(fill=tk.X, pady=2)

        # Time
        time_label = tk.Label(
            row_frame,
            text=time_display,
            font=('Arial', 11, 'bold'),
            bg=bg_color,
            fg='#4CAF50',
            anchor='w',
            width=12
        )
        time_label.pack(side=tk.LEFT, padx=5)

        # Line number
        line_label = tk.Label(
            row_frame,
            text=line,
            font=('Arial', 11, 'bold'),
            bg=bg_color,
            fg='#2196F3',
            anchor='center',
            width=8
        )
        line_label.pack(side=tk.LEFT, padx=5)

        # Destination
        dest_label = tk.Label(
            row_frame,
            text=destination,
            font=('Arial', 10),
            bg=bg_color,
            fg='#ffffff',
            anchor='w'
        )
        dest_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Platform
        platform_label = tk.Label(
            row_frame,
            text=platform,
            font=('Arial', 10),
            bg=bg_color,
            fg='#FFA726',
            anchor='center',
            width=8
        )
        platform_label.pack(side=tk.LEFT, padx=5)

    def show_error(self, error_msg):
        """Display error message"""
        self.status_label.config(text=error_msg, fg='#ff5555')

        # Clear existing entries
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        error_label = tk.Label(
            self.scrollable_frame,
            text=f"⚠️ {error_msg}",
            font=('Arial', 11),
            bg='#1a1a1a',
            fg='#ff5555'
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
