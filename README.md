# Parking Checker

## Features
- Automatic login, date selection, checkout
- Continuous monitoring with automatic refresh
- Support for custom date selection

## Requirements

- Python 3.7+
- Chrome browser installed

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

Alternatively, copy and rename the example file:
```bash
cp .env.example .env
```
Then edit the `.env` file with your actual credentials.

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
