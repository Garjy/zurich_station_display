#!/usr/bin/env python3
"""
Test script to verify the Zurich Transport API works correctly
"""

import requests
import json
from datetime import datetime


def test_api():
    """Test the Transport API for Mannessplatz station"""
    print("=" * 60)
    print("Testing Zurich Transport API")
    print("=" * 60)
    print()

    api_url = "http://transport.opendata.ch/v1/stationboard"
    station_name = "Mannessplatz"

    print(f"Fetching bus data for: {station_name}")
    print(f"API URL: {api_url}")
    print()

    try:
        params = {
            'station': station_name,
            'transportations[]': 'bus',
            'limit': 10
        }

        print("Sending request...")
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        print(f"✓ API request successful!")
        print()

        # Check if station was found
        if 'station' in data and data['station'] is not None:
            station = data['station']
            print(f"Station: {station['name']}")
            print(f"Station ID: {station.get('id', 'N/A')}")
            if 'coordinate' in station:
                print(f"Coordinates: {station['coordinate']['x']}, {station['coordinate']['y']}")
            print()
        elif data.get('station') is None:
            print(f"✗ Station '{station_name}' not found!")
            print()
            print("Use the station finder tool to search for the correct name:")
            print(f"  python3 find_station.py '{station_name}'")
            print()
            print("Or try searching for nearby stations:")
            print("  python3 find_station.py 'Zürich'")
            return False

        # Check stationboard data
        if 'stationboard' in data and data['stationboard']:
            buses = data['stationboard']
            print(f"Found {len(buses)} upcoming buses:")
            print()
            print(f"{'Time':<12} {'Line':<8} {'Destination':<30} {'Platform':<8}")
            print("-" * 60)

            for bus in buses[:10]:
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
                        time_display = f"{time_str} (Now)"
                    else:
                        time_display = f"{time_str} ({minutes}m)"
                else:
                    time_display = "N/A"

                line = bus.get('number', 'N/A')
                destination = bus['to']
                platform = bus['stop'].get('platform', '-')

                print(f"{time_display:<12} {line:<8} {destination:<30} {platform:<8}")

            print()
            print("✓ API test successful!")
            print()
            print("You can now run the full GUI application:")
            print("  python3 bus_display.py")

        else:
            print("⚠ No buses found in the response")
            print()
            print("This could mean:")
            print("  - No buses are scheduled at this time")
            print("  - The station name might be incorrect")
            print()
            print("Response data:")
            print(json.dumps(data, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to API: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check your internet connection")
        print("  2. Try accessing the URL in a browser:")
        print(f"     {api_url}?station={station_name}")
        print("  3. Check if the API is down: https://transport.opendata.ch/")
        return False

    except json.JSONDecodeError as e:
        print(f"✗ Error parsing API response: {e}")
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

    return True


if __name__ == "__main__":
    test_api()
