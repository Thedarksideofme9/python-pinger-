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
import argparse  # for command line arguments
import ssl
from datetime import datetime

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
        "RED": '\033[37m',  # Adjusted for better visibility on light backgrounds
        "GREEN": '\033[92m',  # changed from 32
        "YELLOW": '\033[93m',  # changed from 33
        "BLUE": '\033[94m',  # changed from 34
        "MAGENTA": '\033[95m',  # changed from 35
        "CYAN": '\033[96m'  # changed from 36
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
    "color_theme": "default",  # Add color theme setting
    "primary_dns": "",  # Initialize primary DNS
    "secondary_dns": "" # Initialize secondary DNS
}
SETTINGS_FILE = "pinger_settings.json"  # File to save settings

# Version Information
VERSION = "V1.4"  #Increment version number

# Load Settings Function
def load_settings():
    """Loads settings from the settings file or returns default settings."""
    try:
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
            # Ensure new default settings are added if missing from loaded file
            for key, value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
            return settings
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
        # Check if custom DNS is set and apply it if on Linux/Termux (more complex for Windows/macOS)
        # Note: This is a simplified approach. Proper DNS modification is OS-dependent and often requires root/admin.
        # For a user-level Python script, direct DNS server usage for `socket.gethostbyname` is not straightforward.
        # This implementation primarily influences how *this script* resolves hostnames if it were to use socket.gethostbyname directly.
        # For the `ping` command itself, system DNS settings are usually respected.
        if platform.system().lower() in ['linux', 'darwin'] and (SETTINGS.get("primary_dns") or SETTINGS.get("secondary_dns")):
            # This part is illustrative. Actually forcing `ping` to use specific DNS requires deeper OS integration
            # or pre-configuring `/etc/resolv.conf` (which needs root).
            # For `socket.gethostbyname`, we could use `dnspython` library for custom resolvers.
            pass # We'll rely on the OS's DNS settings for the ping command for simplicity.

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


def get_certificate_info(hostname):
    """Retrieves certificate information from a server."""
    context = ssl.create_default_context()
    try:
        # Use custom DNS if available for name resolution before connecting
        # Note: For this to truly use custom DNS, you'd typically need to
        # use a library like `dnspython` for resolution, or manually resolve
        # to IP using `socket.gethostbyname` if system-wide DNS is modified.
        # Here, `socket.create_connection` relies on system DNS, but if a custom
        # DNS is configured *system-wide*, it will be used.
        with socket.create_connection((hostname, 443), timeout=5) as sock:  # HTTPS port
            with context.wrap_socket(sock, server_hostname=hostname) as ssocket:
                cert = ssocket.getpeercert()
                return cert
    except socket.gaierror:
        print(f"{RED}Could not resolve hostname '{hostname}'.{RESET}")
        return None
    except (socket.timeout, ssl.SSLError, OSError) as e:
        print(f"{RED}Failed to retrieve certificate for {hostname}: {e}{RESET}")
        return None


def calculate_certificate_lifetime(cert):
    """Calculates the remaining lifetime of a certificate."""
    if not cert:
        return None

    try:
        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        remaining_time = not_after - datetime.datetime.now(datetime.timezone.utc)
        return remaining_time
    except (ValueError, KeyError) as e:
        print(f"{RED}Error calculating certificate lifetime: {e}{RESET}")
        return None

def get_certificate_name(cert):
    """Extracts the certificate name (commonName) from the certificate."""
    if not cert:
        return "Unknown"
    try:
        for entry in cert['subject']:
            for attribute in entry:
                if attribute[0] == 'commonName':
                    return attribute[1]
        return "Unknown"
    except KeyError:
        return "Unknown"

def get_encryption_type(hostname):
    """Determines the encryption type used by a server (TLS version)."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssocket:
                return ssocket.version()
    except socket.gaierror:
        return "Unknown - Could not resolve hostname"
    except ssl.SSLError as e:
        if "PROTOCOL_NOT_SUPPORTED" in str(e):
            return "None - Server does not support SSL/TLS"
        return f"Unknown - SSL Error: {e}"
    except OSError as e:
        return f"Unknown - OS Error: {e}"
    except Exception as e:
        return f"Unknown - Error: {e}"

def display_server_status(hostname):
    """Displays the status of a given server with color, country, ping time, certificate info, and encryption type."""
    country = get_country(hostname)
    avg_ping_time = ping(hostname, count=1)  # Get the ping time
    cert = get_certificate_info(hostname)
    encryption_type = get_encryption_type(hostname)

    if avg_ping_time is not None:
        status_color = GREEN
        status_text = f"Available - Ping: {avg_ping_time:.2f} ms"
    else:
        status_color = RED
        status_text = "Unavailable"

    print(f"  - {hostname} ({country}) - {status_color}{status_text}{RESET}")

    if cert:
        cert_name = get_certificate_name(cert)
        print(f"    {GREEN}Certificate Name: {cert_name}{RESET}")

        lifetime = calculate_certificate_lifetime(cert)
        if lifetime:
            print(f"    {GREEN}Certificate Lifetime: {lifetime}{RESET}")
        else:
            print(f"    {YELLOW}Could not determine certificate lifetime.{RESET}")
    else:
        print(f"    {YELLOW}Could not retrieve certificate information.{RESET}")

    print(f"    {CYAN}Encryption Type: {encryption_type}{RESET}")

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
        print(f"  {i + 1}. {key} ({value})")
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

def analyze_http_headers(hostname):
    """Retrieves and analyzes HTTP headers from a given hostname."""
    try:
        response = requests.get(f"http://{hostname}", timeout=5, allow_redirects=True)
        headers = response.headers
        print(f"{GREEN}\n--- HTTP Headers for {hostname} ---{RESET}")
        for key, value in headers.items():
            print(f"  {key}: {value}")
        print(f"  Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"{RED}Failed to retrieve HTTP headers for {hostname}: {e}{RESET}")

def display_settings_menu():
    """Displays the settings menu."""
    print(f"{MAGENTA}\nSettings Menu:{RESET}")
    print("  1. Ping Connection Tweaks")
    print("  2. Show Device Specs")
    print("  3. Change Color Theme")  # Added color theme setting
    print("  4. Wi-Fi Speed Test")  # add speed test
    print("  5. Version Info")
    print("  6. Resolve Hostname")  # added resolve hostname
    print("  7. Analyze HTTP Headers")  #New Analysis
    print("  8. Custom DNS Server") #add custom dns
    print("  9. Back to Main Menu")

def get_settings_menu_choice():
    """Gets the user's choice from the settings menu."""
    while True:
        display_settings_menu()
        choice = input("> ")
        if choice in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):  # added 5
            return choice
        else:
            print("Invalid choice. Please try again.")

def display_custom_dns_menu():
    """Displays the Custom DNS Server menu."""
    print(f"{CYAN}\nCustom DNS Server Settings:{RESET}")
    print("  1. Set Primary DNS Server")
    print("  2. Set Secondary DNS Server")
    print("  3. View Current DNS Servers")  #Display them
    print("  4. Reset to Default DNS Servers")
    print("  5. Back to Settings Menu")

def get_custom_dns_menu_choice():
    """Gets the user's choice from the Custom DNS Server menu."""
    global SETTINGS
    while True:
        display_custom_dns_menu()
        choice = input("> ")
        if choice in ("1", "2", "3", "4", "5"):
            return choice
        else:
            print("Invalid choice. Please try again.")

def set_custom_dns(dns_type):
    """Sets a custom DNS server (primary or secondary)."""
    global SETTINGS
    while True:
        new_dns = input(f"Enter new {dns_type} DNS server IP address: ")
        try:
            socket.inet_aton(new_dns)  # Validate IP address format
            # Store the custom DNS in settings
            SETTINGS[f"{dns_type}_dns"] = new_dns  # ex: primary_dns
            save_settings(SETTINGS)
            print(f"{GREEN}{dns_type.capitalize()} DNS server set to {new_dns}{RESET}")
            break
        except socket.error:
            print(f"{RED}Invalid IP address format. Please try again.{RESET}")
        except Exception as e:
            print(f"{RED}An error occurred: {e}{RESET}")

def view_current_dns_servers():
    """Displays the currently configured DNS servers."""
    primary_dns = SETTINGS.get("primary_dns", "Not Set")
    secondary_dns = SETTINGS.get("secondary_dns", "Not Set")

    print(f"{YELLOW}\nCurrent DNS Servers:{RESET}")
    print(f"  Primary DNS: {primary_dns}")
    print(f"  Secondary DNS: {secondary_dns}")

def reset_default_dns_servers():
     """Resets the DNS servers to empty values (effectively using system defaults)."""
     global SETTINGS
     SETTINGS["primary_dns"] = ""
     SETTINGS["secondary_dns"] = ""
     save_settings(SETTINGS)
     print(f"{GREEN}DNS servers reset to default (system-configured).{RESET}")

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
        print(f"  {i + 1}. {theme.capitalize()} Theme")  # More Dynamic theme listing
    print(f"  {len(themes) + 1}. Custom Theme (Advanced)")
    print(f"  {len(themes) + 2}. Back to Settings Menu")  # Back option
    print("\nEnter the number of the theme you want to use:")  # Prompt change

def get_color_theme_menu_choice():
    """Gets the user's choice from the color theme menu."""
    global SETTINGS  # Access the global settings
    while True:
        display_color_theme_menu()
        choice = input("> ")
        themes = list(COLOR_PALETTES.keys())

        if choice.isdigit():  # Only accept int, prevent errors
            choice_num = int(choice)  # Convert to int
            if 1 <= choice_num <= len(themes):  # Make sure selection is within the list
                selected_theme = themes[choice_num - 1]  # Minus one as start at 1
                SETTINGS["color_theme"] = selected_theme
                apply_color_theme(SETTINGS["color_theme"])  # Apply theme immediately
                save_settings(SETTINGS)  # Save the updated settings
                print(f"{GREEN}Color theme set to {selected_theme.capitalize()}.{RESET}")  # Feedback
                return  # Exit the loop
            elif choice_num == len(themes) + 1:  # Custom Theme
                set_custom_theme()  # Call the custom theme function
                return  # Return to settings menu
            elif choice_num == len(themes) + 2:  # +2 is "back"
                return  # Back to Settings Menu
            else:
                print(f"{RED}Invalid theme number. Please try again.{RESET}")  # Inform invalid choice
        else:
            print(f"{RED}Invalid input. Please try again.{RESET}")  # Tell user needs to put number

def set_custom_theme():
    """Allows the user to define a custom color theme."""
    global SETTINGS, COLOR_PALETTES
    print(f"{YELLOW}\n--- Custom Color Theme Configuration ---{RESET}")
    print(f"{YELLOW}Enter ANSI color codes (e.g., \\033[91m) or 'default' to use default for each color.{RESET}")

    custom_theme = {}
    for color_name in ["RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN"]:
        while True:
            color_code = input(f"Enter color code for {color_name} (or 'default'): ")
            if color_code.lower() == "default":
                color_code = COLOR_PALETTES["default"][color_name]
                break
            elif re.match(r"^\033\[\d+m$", color_code):  # Regex for valid ANSI code
                break
            else:
                print(f"{RED}Invalid ANSI color code. Please try again or enter 'default'.{RESET}")

        custom_theme[color_name] = color_code

    theme_name = input("Enter a name for your custom theme: ")
    COLOR_PALETTES[theme_name] = custom_theme  # Add to color palettes

    SETTINGS["color_theme"] = theme_name
    apply_color_theme(theme_name)
    save_settings(SETTINGS)  # Save settings

    print(f"{GREEN}Custom theme '{theme_name}' saved and applied.{RESET}")

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

def analyze_http_headers(hostname):
    """Retrieves and analyzes HTTP headers from a given hostname."""
    try:
        response = requests.get(f"http://{hostname}", timeout=5, allow_redirects=True)
        headers = response.headers
        print(f"{GREEN}\n--- HTTP Headers for {hostname} ---{RESET}")
        for key, value in headers.items():
            print(f"  {key}: {value}")
        print(f"  Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"{RED}Failed to retrieve HTTP headers for {hostname}: {e}{RESET}")

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

                # Display certificate information
                cert = get_certificate_info(server)
                if cert:
                    cert_name = get_certificate_name(cert)
                    print(f"    {GREEN}Certificate Name: {cert_name}{RESET}")

                    lifetime = calculate_certificate_lifetime(cert)
                    if lifetime:
                        print(f"    {GREEN}Certificate Lifetime: {lifetime}{RESET}")
                    else:
                        print(f"    {YELLOW}Could not determine certificate lifetime.{RESET}")
                else:
                    print(f"    {YELLOW}Could not retrieve certificate information.{RESET}")

                encryption_type = get_encryption_type(server)
                print(f"    {CYAN}Encryption Type: {encryption_type}{RESET}")

            else:
                print("Returning to main menu.")
        elif choice == "2":  # Search for a Custom Hostname/IP
            hostname = input("Enter hostname/IP to search: ")
            avg_ping_time = ping(hostname, count=SETTINGS["ping_count"])  # Use settings ping count
            if avg_ping_time:
                print(f"{GREEN}Ping to {hostname} successful. Avg Ping Time: {avg_ping_time:.2f} ms{RESET}")
            else:
                print(f"{RED}Ping to {hostname} failed.{RESET}")

            # Display certificate information
            cert = get_certificate_info(hostname)
            if cert:
                cert_name = get_certificate_name(cert)
                print(f"    {GREEN}Certificate Name: {cert_name}{RESET}")

                lifetime = calculate_certificate_lifetime(cert)
                if lifetime:
                    print(f"    {GREEN}Certificate Lifetime: {lifetime}{RESET}")
                else:
                    print(f"    {YELLOW}Could not determine certificate lifetime.{RESET}")
            else:
                print(f"    {YELLOW}Could not retrieve certificate information.{RESET}")

            encryption_type = get_encryption_type(hostname)
            print(f"    {CYAN}Encryption Type: {encryption_type}{RESET}")


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
            elif settings_choice == "4":  # Wi-Fi Speed Test
                perform_speed_test()  # Run Speedtest
            elif settings_choice == "5":  # show version
                display_version_info()  # Shows versions
            elif settings_choice == "6":  # resolve
                resolve_hostname()
            elif settings_choice == "7": # Analyze Headers
                hostname = input("Enter hostname to analyze HTTP headers: ")
                analyze_http_headers(hostname)
            elif settings_choice == "8": # Custom DNS Server
                dns_choice = get_custom_dns_menu_choice()
                if dns_choice == "1":
                    set_custom_dns("primary")
                elif dns_choice == "2":
                    set_custom_dns("secondary")
                elif dns_choice == "3":
                    view_current_dns_servers()
                elif dns_choice == "4":
                    reset_default_dns_servers()
                elif dns_choice == "5":
                    pass # Back to settings menu
            elif settings_choice == "9":  # Back to main menu
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
