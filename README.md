# Random Pinger

This is a simple command-line tool written in Python for pinging servers, displaying network information, and performing speed tests. It's designed to run in a Termux environment (Android) but may also work on other Linux systems.

## Features

*   Pings predefined servers or custom hostnames.
*   Displays the status (availability, country, ping time) of servers.
*   Randomly pings servers from a list.
*   Displays device specifications (CPU, RAM, OS, etc.).
*   Performs a Wi-Fi speed test (download and upload speed, ping).
*   Color theming (customizable terminal colors).

## Requirements

*   **Termux:** This script is primarily designed for Termux on Android.
*   **Python 3:** Make sure you have Python 3 installed in Termux. You can install it using:

    ```bash
    pkg install python
    ```

*   **pip:** Python's package installer. Usually comes with Python. If not, install with:

    ```bash
    pkg install python-pip
    ```

*   **Required Python Packages:** Install these using `pip`:

    ```bash
    pip install requests beautifulsoup4 speedtest-cli
    ```

    or

    ```bash
    pip3 install requests beautifulsoup4 speedtest-cli
    ```

    Make sure you use the `pip` command that corresponds to your Python 3 installation.

*   **`usbutils` (Optional):** Required for the "Detect USB Dongle" feature. Install in Termux with:

    ```bash
    pkg install usbutils
    ```

## Installation Instructions

1.  **Clone the Repository:**

    If you're downloading this from GitHub, clone the repository to your Termux environment:

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install Dependencies:**

    Install the required Python packages using `pip`:

    ```bash
    pip install requests beautifulsoup4 speedtest-cli
    ```

    Or, if `pip` is not working, use the Termux package manager:

    ```bash
    pkg install python-requests python-beautifulsoup4
    pip install speedtest-cli  # speedtest-cli may still need pip
    ```

3.  **Make the Script Executable:**

    Give the script execute permissions:

    ```bash
    chmod +x pinger.py
    ```

## Usage

1.  **Run the Script:**

    From the Termux terminal, run the script:

    ```bash
    python3 pinger.py

    ```

2.  **Follow the Menu:**

    The script will display a menu of options. Use the number keys to select an option and press Enter.

## Settings

The settings menu allows you to:

*   **Change Color Theme:** Select a different color scheme for the terminal output.
*   **Ping Connection Tweaks:** Adjust the number of ping packets sent.
*   **Show Device Specs:** View information about your device's hardware and software.
*   **Wi-Fi Speed Test:** Measure your internet connection speed.

## Notes

*   This script is designed to be run in a Termux environment.
*   The "Detect USB Dongle" feature may not work on all devices and requires the `usbutils` package.
*   The "Show Device Specs" feature relies on Linux-specific files and may not work on other operating systems.
*   Accurate country detection depends on the `ipinfo.io` API being available and having accurate data.
*   The script has been removed any functions that causes errors

## License

This project is licensed under the [Apache2.0 ](LICENSE) - see the `LICENSE` file for details.
