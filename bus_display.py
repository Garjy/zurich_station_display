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
from PIL import Image, ImageTk
import io
import re


class BusDisplayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Zurich Bus Display")

        # Configure fullscreen
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#2B5DA0', cursor='none')

        # Zurich line colors (line number: (bg_color, fg_color))
        self.line_colors = {
            # Buses
            '31': ('#E30613', '#FFFFFF'),  # Red
            '32': ('#E30613', '#FFFFFF'),  # Red
            '33': ('#E30613', '#FFFFFF'),  # Red
            '34': ('#E30613', '#FFFFFF'),  # Red
            '61': ('#956B27', '#FFFFFF'),  # Brown
            '62': ('#956B27', '#FFFFFF'),  # Brown
            '64': ('#956B27', '#FFFFFF'),  # Brown
            '69': ('#956B27', '#FFFFFF'),  # Brown
            '72': ('#808080', '#FFFFFF'),  # Gray
            '73': ('#808080', '#FFFFFF'),  # Gray
            '75': ('#808080', '#FFFFFF'),  # Gray
            '76': ('#FFFFFF', '#000000'),  # White background, black text
            '77': ('#FFFFFF', '#000000'),  # White background, black text
            '80': ('#00A651', '#FFFFFF'),  # Green
            '83': ('#00A651', '#FFFFFF'),  # Green
            # Trams
            '2': ('#E30613', '#FFFFFF'),   # Red
            '3': ('#00A651', '#FFFFFF'),   # Green
            '4': ('#0066B3', '#FFFFFF'),   # Blue
            '5': ('#956B27', '#FFFFFF'),   # Brown
            '6': ('#956B27', '#FFFFFF'),   # Brown
            '7': ('#000000', '#FFFFFF'),   # Black
            '8': ('#00A651', '#FFFFFF'),   # Green
            '9': ('#0066B3', '#FFFFFF'),   # Blue
            '10': ('#E30095', '#FFFFFF'),  # Pink
            '11': ('#00A651', '#FFFFFF'),  # Green
            '12': ('#00A651', '#FFFFFF'),  # Green
            '13': ('#FDD204', '#000000'),  # Yellow
            '14': ('#0066B3', '#FFFFFF'),  # Blue
            '15': ('#E30613', '#FFFFFF'),  # Red
            '17': ('#808080', '#FFFFFF'),  # Gray
        }

        # Allow ESC key to exit fullscreen (useful for testing)
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', True))

        # Load transport icons
        self.transport_icons = {}
        self.load_icons()

        # Load configuration
        self.load_config()

        # API Configuration
        self.api_url = "http://transport.opendata.ch/v1/stationboard"

        # Create UI
        self.create_widgets()

        # Start data fetching
        self.running = True
        self.fetch_data()

    def load_icons(self):
        """Load and prepare transport icons from SVG files"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(script_dir, 'icons')

        icon_files = {
            'bus': 'bus-profile-small.svg',
            'tram': 'tram-profile-small.svg',
            'train': 'train-profile-small.svg'
        }

        for icon_name, filename in icon_files.items():
            icon_path = os.path.join(icons_dir, filename)
            try:
                if os.path.exists(icon_path):
                    # Read SVG content
                    with open(icon_path, 'r') as f:
                        svg_content = f.read()

                    # Convert black fill to white for display on blue background
                    svg_content = svg_content.replace('fill="#000"', 'fill="#FFFFFF"')

                    # Try to render SVG using cairosvg if available
                    try:
                        import cairosvg
                        png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'),
                                                     output_width=24, output_height=24)
                        image = Image.open(io.BytesIO(png_data))
                        self.transport_icons[icon_name] = ImageTk.PhotoImage(image)
                    except ImportError:
                        # Fallback: use text icons if cairosvg is not available
                        print(f"Warning: cairosvg not installed, using text icons as fallback")
                        self.transport_icons = None
                        return
            except Exception as e:
                print(f"Error loading icon {icon_name}: {e}")
                self.transport_icons = None
                return

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

            # Skip buses that have already departed
            if minutes < 0:
                return

            if minutes == 0:
                time_display = "Now"
            else:
                time_display = f"in {minutes}'"
        else:
            time_display = "N/A"

        # Get bus information
        line = bus.get('number', 'N/A')
        destination = bus['to']

        # Remove "Zurich"/"Zürich" and any following non-letter characters (spaces, commas, etc.)
        destination = re.sub(r'^Z[üu]rich[^a-zA-ZÀ-ÿ]*', '', destination)

        category = bus.get('category', '')

        # Determine transport icon based on category
        icon_mapping = {
            'B': 'bus',
            'BUS': 'bus',
            'T': 'tram',
            'TRAM': 'tram',
            'S': 'train',
            'IC': 'train',
            'IR': 'train',
            'RE': 'train',
            'EC': 'train',
        }

        # Get the appropriate icon type (default to bus)
        icon_type = icon_mapping.get(category, 'bus')

        # Get line colors from predefined mapping
        if line in self.line_colors:
            line_bg_color, line_fg_color = self.line_colors[line]
        else:
            # Default colors for unknown lines
            line_bg_color = '#7C7C7C'  # Gray
            line_fg_color = '#FF8C00'  # Orange text

        # Alternating blue tints for each row
        row_colors = ['#3366AA', '#2B5DA0']  # Lighter and darker blue
        row_bg = row_colors[index % 2]

        # Create row frame with alternating blue background
        row_frame = tk.Frame(self.scrollable_frame, bg=row_bg)
        row_frame.pack(fill=tk.X, pady=1, padx=10)

        # Transport icon (bus/tram/train)
        if self.transport_icons and icon_type in self.transport_icons:
            # Use image icon
            icon_label = tk.Label(
                row_frame,
                image=self.transport_icons[icon_type],
                bg=row_bg,
                anchor='center',
                width=30
            )
            icon_label.pack(side=tk.LEFT, padx=(5, 5))

        # Line number with line-specific color
        line_frame = tk.Frame(row_frame, bg=line_bg_color, width=60, height=35)
        line_frame.pack(side=tk.LEFT, padx=(5, 10), pady=8)
        line_frame.pack_propagate(False)

        line_label = tk.Label(
            line_frame,
            text=line,
            font=('Arial', 16, 'bold'),
            bg=line_bg_color,
            fg=line_fg_color,
            anchor='center',
            justify=tk.CENTER
        )
        line_label.place(relx=0.5, rely=0.5, anchor='center')

        # Destination
        dest_label = tk.Label(
            row_frame,
            text=destination,
            font=('Arial', 14),
            bg=row_bg,
            fg='#ffffff',
            anchor='w'
        )
        dest_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Departure time
        time_label = tk.Label(
            row_frame,
            text=time_display,
            font=('Arial', 14, 'bold'),
            bg=row_bg,
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
