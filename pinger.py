#!/usr/bin/env python3

import subprocess
import platform
import sys
import socket
import requests
import random
import time
import os
import re
import json  # For saving settings
import select
import textwrap
import traceback
import argparse # for command line arguments

# ANSI color codes
RESET = '\033[0m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'

# Color Palettes - Define different color combinations
COLOR_PALETTES = {
    "default": {
        "RED": '\033[91m',
        "GREEN": '\033[92m',
        "YELLOW": '\033[93m',
        "BLUE": '\033[94m',
        "MAGENTA": '\033[95m',
        "CYAN": '\033[96m'
    },
    "dark": {
        "RED": '\033[31m',
        "GREEN": '\033[32m',
        "YELLOW": '\033[33m',
        "BLUE": '\033[34m',
        "MAGENTA": '\033[35m',
        "CYAN": '\033[36m'
    },
    "light": {
        "RED": '\033[31m',
        "GREEN": '\033[32m',
        "YELLOW": '\033[33m',
        "BLUE": '\033[34m',
        "MAGENTA": '\033[35m',
        "CYAN": '\033[36m'
    },
    "pastel": {
    "RED": '\033[95m',
    "GREEN": '\033[96m',
    "YELLOW": '\033[93m',
    "BLUE": '\033[94m',
    "MAGENTA": '\033[91m',
    "CYAN": '\033[92m'
    }
    }
}

# ASCII art for "Random Pinger" in large red text
ASCII_ART = f"""{COLOR_PALETTES["default"]["RED"]}
  __  __ _       _       ____  ____
 |  \/  (_)_ __ | |_    / ___||  _ \
 | |\/| | | '_ \| __|   \___ \| |_) |
 | |  | | | | | | |_    ___) |  __/
 |_|  |_|_|_| |_|\__|  |____/|_|
{RESET}
"""

# Define a list of pre-defined servers
SERVERS = {
    "google": "google.com",
    "cloudflare": "1.1.1.1",
    "opendns": "208.67.222.222",
    "localhost": "127.0.0.1",
    "example": "example.com",
    "microsoft": "microsoft.com"
}

# Default Settings and Settings File
DEFAULT_SETTINGS = {
    "ping_count": 4,
    "color_theme": "default"  # Add color theme setting
}
SETTINGS_FILE = "pinger_settings.json"  # File to save settings

# Version Information
VERSION = "V1.2"


# Load Settings Function
def load_settings():
    """Loads settings from the settings file or returns default settings."""
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return DEFAULT_SETTINGS
    except json.JSONDecodeError:
        print(f"{RED}Error decoding settings file. Using default settings.{RESET}")
        return DEFAULT_SETTINGS


# Save Settings Function
def save_settings(settings):
    """Saves settings to the settings file."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)  # Save with indentation for readability
    except Exception as e:
        print(f"{RED}Error saving settings: {e}{RESET}")


# Function to apply the color theme
def apply_color_theme(theme):
    """Applies a color theme based on the selected theme name."""
    global RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, RESET

    if theme in COLOR_PALETTES:
        palette = COLOR_PALETTES[theme]  # Use the chosen theme
        RED = palette["RED"]
        GREEN = palette["GREEN"]
        YELLOW = palette["YELLOW"]
        BLUE = palette["BLUE"]
        MAGENTA = palette["MAGENTA"]
        CYAN = palette["CYAN"]
        # RESET = '\033[0m' This does not need to be adjusted
        print(f"{GREEN}Color theme set to {theme}.{RESET}")  # Confirm the them has been updated
    else:
        print(f"{RED}Invalid theme: {theme}. Using default.{RESET}")
        apply_color_theme("default")

# Load Settings at Startup
SETTINGS = load_settings()
PING_COUNT = SETTINGS["ping_count"]  # LOAD GLOBAL PING COUNT
apply_color_theme(SETTINGS["color_theme"])  # Apply the color theme to the current color codes

def get_country(hostname):
    """Gets the country of a hostname using the ipinfo.io API."""
    try:
        ip_address = socket.gethostbyname(hostname)  # Resolve hostname to IP
        response = requests.get(f"https://ipinfo.io/{ip_address}/country")
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "Unknown"
    except (socket.gaierror, requests.exceptions.RequestException):
        return "Unknown"

def ping(hostname, count=4):
    """
    Pings a host and returns the average ping time in milliseconds.

    Args:
        hostname (str): The hostname or IP address to ping.
        count (int): The number of ping packets to send.

    Returns:
        float: The average ping time in milliseconds, or None if the ping fails.
    """

    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, str(count), hostname]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            output = stdout.decode()
            # Regex to extract ping times from each line
            ping_times = re.findall(r'time=([\d.]+)\s?ms', output)

            if ping_times:
                ping_times = [float(time) for time in ping_times]
                avg_ping_time = sum(ping_times) / len(ping_times)
                return avg_ping_time
            else:
                return None  # No ping times found in output
        else:
            print(f"Ping failed with error code: {process.returncode}")
            print(stderr.decode())
            return None

    except OSError as e:
        print(f"Error executing ping command: {e}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Ping failed: {e}")
        return None

def display_server_status(hostname):
    """Displays the status of a given server with color, country, and ping time."""
    country = get_country(hostname)
    avg_ping_time = ping(hostname, count=1)  # Get the ping time

    if avg_ping_time is not None:
        status_color = GREEN
        status_text = f"Available - Ping: {avg_ping_time:.2f} ms"
    else:
        status_color = RED
        status_text = "Unavailable"

    print(f"  - {hostname} ({country}) - {status_color}{status_text}{RESET}")

def display_main_menu():
    """Displays the main menu with options."""
    print(f"{BLUE}\nMain Menu:{RESET}")
    print("  1. Ping a Predefined Server")
    print("  2. Search for a Custom Hostname/IP")
    print("  3. Randomly Ping a Server")
    print("  4. List Available Servers with Status")
    print("  5. Settings")
    print("  6. Exit")

def get_main_menu_choice():
    """Gets the user's choice from the main menu."""
    while True:
        display_main_menu()
        choice = input("> ")
        if choice in ("1", "2", "3", "4", "5", "6"):
            return choice
        else:
            print("Invalid choice. Please try again.")

def display_server_menu():
    """Displays the server menu."""
    print(f"{CYAN}\nAvailable Servers:{RESET}")
    for i, (key, value) in enumerate(SERVERS.items()):
        print(f"  {i+1}. {key} ({value})")
    print("\nEnter the number of the server you want to ping, or '0' to go back:")

def get_server_menu_choice():
    """Gets the user's choice from the server menu."""
    while True:
        display_server_menu()
        choice = input("> ")
        if choice == '0':
            return None  # Go back to main menu
        try:
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(SERVERS):
                return list(SERVERS.values())[choice_index]
            else:
                print("Invalid server number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def random_ping():
    """Randomly pings a server from the list."""
    hostname = random.choice(list(SERVERS.values()))
    print(f"{YELLOW}Randomly selected: {hostname}{RESET}")
    display_server_status(hostname)  # Show the status of the randomly selected server

    avg_ping_time = ping(hostname, count=SETTINGS["ping_count"])  # Use settings for ping count

    if avg_ping_time:
        print(f"{GREEN}Ping to {hostname} successful. Avg Ping Time: {avg_ping_time:.2f} ms{RESET}")
    else:
        print(f"{RED}Ping to {hostname} failed.{RESET}")

def display_settings_menu():
    """Displays the settings menu."""
    print(f"{MAGENTA}\nSettings Menu:{RESET}")
    print("  1. Ping Connection Tweaks")
    print("  2. Show Device Specs")
    print("  3. Change Color Theme")  # Added color theme setting
    print("  4. Wi-Fi Speed Test")  # add speed test
    print("  5. Version Info")
    print("  6. Resolve Hostname")  # added resolve hostname
    print("  7. Back to Main Menu")

def get_settings_menu_choice():
    """Gets the user's choice from the settings menu."""
    while True:
        display_settings_menu()
        choice = input("> ")
        if choice in ("1", "2", "3", "4", "5", "6", "7"):  # added 5
            return choice
        else:
            print("Invalid choice. Please try again.")

def display_ping_tweaks_menu():
    """Displays the Ping Tweaks menu."""
    print(f"{CYAN}\nPing Connection Tweaks:{RESET}")
    print(f"  Current Ping Count: {SETTINGS['ping_count']}")
    print("  1. Change Ping Count")
    print("  2. Back to Settings Menu")

def get_ping_tweaks_menu_choice():
    """Gets the user's choice from the ping tweaks menu."""
    global SETTINGS  # Access the global settings
    while True:
        display_ping_tweaks_menu()
        choice = input("> ")
        if choice == "1":
            while True:
                try:
                    new_count = int(input("Enter new ping count: "))
                    if new_count > 0:
                        SETTINGS["ping_count"] = new_count
                        save_settings(SETTINGS)  # Save the updated settings
                        print(f"Ping count set to {SETTINGS['ping_count']}")
                        break
                    else:
                        print("Ping count must be greater than 0.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        elif choice == "2":
            return  # Back to Settings Menu
        else:
            print("Invalid choice. Please try again.")

def show_device_specs():
    """Displays device specifications, live RAM and CPU usage."""

    def get_cpu_usage():
        """Gets CPU usage percentage."""
        try:
            output = subprocess.check_output("top -bn1 | grep '^%Cpu(s)' | awk '{print $2 + $4}'", shell=True).decode().strip()
            return float(output)
        except (subprocess.CalledProcessError, ValueError):
            return 0.0

    def get_ram_usage():
        """Gets RAM usage in GB."""
        try:
            output = subprocess.check_output("free -m | awk 'NR==2{print $3}'", shell=True).decode().strip()
            used_memory_mb = int(output)
            return round(used_memory_mb / 1024, 2)  # GB
        except (subprocess.CalledProcessError, ValueError):
            return 0.0

    print(f"{YELLOW}\nDevice Specifications - Press 'q' to quit:{RESET}")
    print(f"  Platform: {platform.system()} {platform.release()}")
    print(f"  Hostname: {socket.gethostname()}")

    try:
        # Get CPU information (Linux/Termux specific)
        with open("/proc/cpuinfo", "r") as f:
            cpu_info = f.read()
            model_name = next((line.split(":")[1].strip() for line in cpu_info.splitlines() if "model name" in line), "N/A")
            print(f"  CPU Model: {model_name}")
    except FileNotFoundError:
        print("  CPU Model: N/A (Could not retrieve CPU info)")

    try:
        # Get Total Memory information (Linux/Termux specific)
        with open("/proc/meminfo", "r") as f:
            mem_info = f.read()
            total_memory_kb = next((line.split(":")[1].strip().replace(" kB", "") for line in mem_info.splitlines() if "MemTotal" in line), "0")
            total_memory_gb = round(int(total_memory_kb) / 1024 / 1024, 2)  # Convert KB to GB
            print(f"  Total Memory: {total_memory_gb} GB")
    except FileNotFoundError:
        print("  Total Memory: N/A (Could not retrieve memory info)")

    print(f"  Python Version: {sys.version}")

    while True:
        cpu_usage = get_cpu_usage()
        ram_usage = get_ram_usage()

        # Create a loading bar for CPU
        cpu_bar = "[" + "#" * int(cpu_usage / 5) + " " * (20 - int(cpu_usage / 5)) + "]"
        print(f"{CYAN}  CPU Usage: {cpu_bar} {cpu_usage:.1f}%{RESET}", end='\r')  # Overwrite the same line
        sys.stdout.flush()

        print(f"{MAGENTA}  RAM Usage: {ram_usage:.2f} GB{RESET}", end='\r')  # Overwrite the same line
        sys.stdout.flush()

        time.sleep(0.5)  # Update every 0.5 seconds

        # Check for user input 'q' to quit
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:  # Check if sys.stdin has data to read
            if sys.stdin.readline().strip().lower() == 'q':
                print("\nReturning to Settings Menu...")
                break  # Exit the loop
        time.sleep(0.5)  # Give time for stdin to fill up to be read

def display_color_theme_menu():
    """Displays the color theme menu."""
    print(f"{CYAN}\nColor Theme Settings:{RESET}")
    print(f"  Current Theme: {SETTINGS['color_theme']}")
    themes = list(COLOR_PALETTES.keys())
    for i, theme in enumerate(themes):
        print(f"  {i+1}. {theme.capitalize()} Theme")  #More Dynamic theme listing
    print(f"  {len(themes)+1}. Back to Settings Menu")  #Back option
    print("\nEnter the number of the theme you want to use:") #Prompt change

def get_color_theme_menu_choice():
    """Gets the user's choice from the color theme menu."""
    global SETTINGS  # Access the global settings
    while True:
        display_color_theme_menu()
        choice = input("> ")
        themes = list(COLOR_PALETTES.keys())

        if choice.isdigit(): #Only accept int, prevent errors
            choice_num = int(choice) #Convert to int
            if 1 <= choice_num <= len(themes): #Make sure selection is within the list
                selected_theme = themes[choice_num-1] #Minus one as start at 1
                SETTINGS["color_theme"] = selected_theme
                apply_color_theme(SETTINGS["color_theme"])  # Apply theme immediately
                save_settings(SETTINGS)  # Save the updated settings
                print(f"{GREEN}Color theme set to {selected_theme.capitalize()}.{RESET}") #Feedback
                return #Exit the loop
            elif choice_num == len(themes)+1: #+1 is "back"
                return  # Back to Settings Menu
            else:
                print(f"{RED}Invalid theme number. Please try again.{RESET}") #Inform invalid choice
        else:
            print(f"{RED}Invalid input. Please try again.{RESET}") #Tell user needs to put number

def perform_speed_test():
    """Performs a speed test using speedtest-cli and displays the results."""
    try:
        # Run speedtest-cli and capture the output
        process = subprocess.Popen(["speedtest", "--simple"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        output = stdout.decode().strip()

        # Parse the output (assuming the format is consistent)
        if output:
            lines = output.split('\n')
            ping = lines[0].split(': ')[1]
            download = lines[1].split(': ')[1]
            upload = lines[2].split(': ')[1]

            # Get the external IP address
            try:
                external_ip = requests.get("https://api.ipify.org").text.strip()
            except requests.exceptions.RequestException:
                external_ip = "Could not retrieve IP address"

            print(f"{GREEN}\n--- Speed Test Results ---{RESET}")
            print(f"  Ping: {ping}")
            print(f"  Download: {download}")
            print(f"  Upload: {upload}")
            print(f"  External IP: {external_ip}{RESET}\n")

        else:
            print(f"{RED}Speed test failed.  Check your internet connection.{RESET}")
            if stderr:
                print(f"{RED}Error output from speedtest-cli:\n{stderr.decode()}{RESET}")

    except FileNotFoundError:
        print(f"{RED}'speedtest' command not found.  Please install speedtest using: pip install speedtest-cli (or apt-get install speedtest-cli if using linux).{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}Error running speedtest: {e}{RESET}")
        print(f"{RED}Command Output: {e.output.decode()}{RESET}")  # Show
    except Exception as e:
        print(f"{RED}An unexpected error occurred: {e}, {traceback.format_exc()}")

def display_version_info():
    """Displays the version information."""
    print(f"{YELLOW}\n--- Version Information ---{RESET}")
    print(f"  Pinger Version: {VERSION}{RESET}\n")

def resolve_hostname():
        """Prompts the user for a hostname and attempts to resolve it to an IP address."""
        hostname = input("Enter hostname to resolve: ")
        try:
            ip_address = socket.gethostbyname(hostname)
            print(f"{GREEN}Hostname '{hostname}' resolves to: {ip_address}{RESET}")
        except socket.gaierror:
            print(f"{RED}Could not resolve hostname '{hostname}'.{RESET}")

def main():
    """Main function to handle menu and ping operations."""

    print(ASCII_ART)  # Print the ASCII art banner

    while True:
        choice = get_main_menu_choice()
        if choice == "1":
            server = get_server_menu_choice()
            if server:
                print(f"Pinging {server}...")
                avg_ping_time = ping(server, count=SETTINGS["ping_count"])  # Use settings ping count
                if avg_ping_time:
                    print(f"{GREEN}Ping to {server} successful. Avg Ping Time: {avg_ping_time:.2f} ms{RESET}")
                else:
                    print(f"{RED}Ping to {server} failed.{RESET}")
            else:
                print("Returning to main menu.")
        elif choice == "2":  # Search for a Custom Hostname/IP
            hostname = input("Enter hostname/IP to search: ")
            avg_ping_time = ping(hostname, count=SETTINGS["ping_count"])  # Use settings ping count
            if avg_ping_time:
                print(f"{GREEN}Ping to {hostname} successful. Avg Ping Time: {avg_ping_time:.2f} ms{RESET}")
            else:
                print(f"{RED}Ping to {hostname} failed.{RESET}")
        elif choice == "3":  # Randomly Ping a Server
            random_ping()
        elif choice == "4":  # List Available Servers with Status
            print(f"{MAGENTA}\nAvailable Servers with Status:{RESET}")
            for hostname in SERVERS.values():
                display_server_status(hostname)
        elif choice == "5":  # Settings
            settings_choice = get_settings_menu_choice()
            if settings_choice == "1":  # Ping Connection Tweaks
                get_ping_tweaks_menu_choice()
            elif settings_choice == "2":  # Show Device Specs
                show_device_specs()
            elif settings_choice == "3":  # Change Color Theme
                get_color_theme_menu_choice()
            elif settings_choice == "4":  # Run Wifi test
                perform_speed_test()  # Run Speedtest
            elif settings_choice == "5":  # show version
                display_version_info() #Shows versions
            elif settings_choice == "6": #resolve
                resolve_hostname()
            elif settings_choice == "7":  # Back to main menu
                pass  # Just return to the main loop

        elif choice == "6":  # Exit
            print("Exiting Random Pinger.")
            sys.exit(0)

if __name__ == "__main__":
    """
    Needs these installed
    pip install requests
    pip install speedtest
    """
    import select
    import traceback

    main()
