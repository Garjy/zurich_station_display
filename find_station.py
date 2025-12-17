#!/usr/bin/env python3
"""
Station Finder Tool
Helps you find the correct station name for the bus display app
"""

import requests
import sys


def find_station(query):
    """Search for stations matching the query"""
    print("=" * 60)
    print(f"Searching for stations matching: '{query}'")
    print("=" * 60)
    print()

    api_url = "http://transport.opendata.ch/v1/locations"

    try:
        params = {'query': query}
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if 'stations' in data and data['stations']:
            stations = data['stations']
            print(f"Found {len(stations)} station(s):")
            print()

            for i, station in enumerate(stations, 1):
                name = station.get('name', 'Unknown')
                station_id = station.get('id', 'N/A')
                icon = station.get('icon', 'unknown')

                print(f"{i}. {name}")
                print(f"   ID: {station_id}")
                print(f"   Type: {icon}")

                if station.get('coordinate'):
                    coord = station['coordinate']
                    if coord.get('x') and coord.get('y'):
                        print(f"   Coordinates: {coord['x']}, {coord['y']}")

                print()

            print("=" * 60)
            print("To use a station in the bus display app:")
            print("1. Edit config.ini")
            print("2. Update the station name:")
            print("   [Station]")
            print(f"   name = {stations[0]['name']}")
            print("=" * 60)

        else:
            print("No stations found matching your query.")
            print()
            print("Tips:")
            print("  - Try a broader search term")
            print("  - Check the spelling")
            print("  - Try adding 'Zürich,' before the station name")
            print()
            print("Example searches:")
            print("  python3 find_station.py 'Zürich HB'")
            print("  python3 find_station.py 'Bellevue'")
            print("  python3 find_station.py 'Paradeplatz'")

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 find_station.py 'Station Name'")
        print()
        print("Examples:")
        print("  python3 find_station.py 'Zürich HB'")
        print("  python3 find_station.py 'Bellevue'")
        print("  python3 find_station.py 'Paradeplatz'")
        print("  python3 find_station.py 'Mannesmann'")
        sys.exit(1)

    query = ' '.join(sys.argv[1:])
    find_station(query)
