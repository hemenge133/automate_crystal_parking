# Crystal Mountain Parking Checker

An automated tool to check for parking availability at Crystal Mountain Resort. The script will continuously monitor parking availability for a specified date and alert you when a spot becomes available.

## Features

- Automatic login and date selection
- Continuous monitoring with automatic refresh
- Audio alerts when parking becomes available
- Support for custom date selection
- Secure credential management using environment variables

## Requirements

- Python 3.7+
- Chrome browser
- ChromeDriver (matching your Chrome version)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd crystal-mountain-checker
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project directory with your Crystal Mountain credentials:
```
CRYSTAL_USERNAME=your_username
CRYSTAL_PASSWORD=your_password
```

## Usage

### Basic Usage
Run the script with a specific date:
```bash
python crystal_mountain_checker.py --date MM/DD
```
or
```bash
python crystal_mountain_checker.py --date MM/DD/YYYY
```

### Date Format Examples
- March 15, 2024: `--date 3/15` or `--date 3/15/2024`
- December 25, 2024: `--date 12/25` or `--date 12/25/2024`

If no date is provided, the script will use a default date (currently set to March 29, 2025).

### Examples
```bash
# Check for March 15th of the current year
python crystal_mountain_checker.py --date 3/15

# Check for December 25th, 2024
python crystal_mountain_checker.py --date 12/25/2024

# Use default date
python crystal_mountain_checker.py
```

## How It Works

1. The script logs into your Crystal Mountain account
2. Navigates to the parking reservation page
3. Selects the specified date
4. Continuously checks for parking availability
5. When parking becomes available:
   - Plays an audio alert
   - Keeps the browser window open
   - Displays a success message
6. You can complete the reservation manually in the browser window

## Alerts

- The script will play 10 beeps when parking becomes available
- The browser window will remain open so you can complete the reservation
- Press Ctrl+C in the terminal to stop the script

## Security

- Credentials are stored in a `.env` file (not committed to version control)
- The `.gitignore` file is configured to exclude the `.env` file
- Never share your `.env` file or commit it to version control

## Troubleshooting

If you encounter issues:

1. Make sure your Chrome browser and ChromeDriver versions match
2. Verify your Crystal Mountain credentials in the `.env` file
3. Check that the date format is correct (MM/DD or MM/DD/YYYY)
4. Ensure you have a stable internet connection

## Known Limitations

- The script requires Chrome browser
- Date selection is limited to available calendar dates
- Audio alerts require system audio support
- The script must be stopped manually (Ctrl+C) when finished

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
