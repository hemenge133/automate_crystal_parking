from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
import beepy
import os
import argparse
import datetime
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def play_alert():
    """Play alert sound multiple times"""
    for _ in range(10):  # Play 10 times
        beepy.beep(sound=1)
        time.sleep(1)

def parse_date(date_str):
    """Parse date string in MM/DD or MM/DD/YYYY format"""
    # Check if date is in MM/DD format or MM/DD/YYYY format
    if re.match(r'^\d{1,2}/\d{1,2}$', date_str):
        # MM/DD format, assume current year
        month, day = map(int, date_str.split('/'))
        year = datetime.datetime.now().year
    elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        # MM/DD/YYYY format
        month, day, year = map(int, date_str.split('/'))
    else:
        raise ValueError("Invalid date format. Please use MM/DD or MM/DD/YYYY")
    
    # Validate the date
    try:
        date = datetime.date(year, month, day)
        return date
    except ValueError as e:
        raise ValueError(f"Invalid date: {e}")

def find_calendar_element(driver, target_date):
    """Find the calendar element for the given date"""
    # Format for calendar element: calendar_YYYY-MM
    calendar_id = f'calendar_{target_date.year}-{target_date.month:02d}'
    print(f"Looking for calendar with ID: {calendar_id}")
    
    # Wait for the calendar to be visible
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, calendar_id))
    )
    
    # Find all day elements in the target month
    day_elements = driver.find_elements(By.CSS_SELECTOR, f'#{calendar_id} > div')
    
    # Find the element corresponding to the target day
    for element in day_elements:
        try:
            # Each day has a data-date attribute or text content with the day
            if element.get_attribute('data-date'):
                element_date = element.get_attribute('data-date')
                if str(target_date.day) in element_date:
                    return element
            
            # If no data-date attribute, check the text content
            if element.text and element.text.strip().isdigit():
                if int(element.text.strip()) == target_date.day:
                    return element
        except:
            continue
    
    # If we can't find the exact day, try finding by child span with the day number
    for element in day_elements:
        try:
            day_text = element.text.strip()
            if day_text and day_text.isdigit() and int(day_text) == target_date.day:
                return element
        except:
            continue
            
    raise ValueError(f"Could not find calendar element for {target_date.month}/{target_date.day}/{target_date.year}")

def check_parking_availability(date_str=None):
    # Get credentials from environment variables
    username = os.getenv('CRYSTAL_USERNAME')
    password = os.getenv('CRYSTAL_PASSWORD')
    
    if not username or not password:
        raise ValueError("Missing credentials in .env file. Please set CRYSTAL_USERNAME and CRYSTAL_PASSWORD")
    
    # Parse date if provided
    target_date = None
    if date_str:
        target_date = parse_date(date_str)
        print(f"Checking availability for: {target_date.month}/{target_date.day}/{target_date.year}")
    else:
        print("No date specified, using default date from the script")
    
    # Set up Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    
    # Initialize the driver
    driver = webdriver.Chrome(options=options)
    
    try:
        print("Starting the parking checker...")
        # Navigate to the login page
        driver.get('https://parking.crystalmountainresort.com/login/')
        print("Loaded login page")
        
        # Wait for and click the first button
        first_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/div/div[1]/button[1]'))
        )
        first_button.click()
        
        # Fill in username and password
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/div/div[2]/form[1]/div[2]/div/input[1]'))
        )
        password_field = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div/div[2]/form[1]/div[2]/div/input[2]')
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Submit the form
        password_field.submit()
        
        # Wait after login
        time.sleep(2)
        
        while True:
            try:
                # Navigate to main page
                print("Navigating to main page...")
                driver.get('https://parking.crystalmountainresort.com/')
                time.sleep(2)  # Wait for page load
                
                # Find and click the calendar date
                if target_date:
                    print(f"Looking for date: {target_date.month}/{target_date.day}/{target_date.year}")
                    calendar_element = find_calendar_element(driver, target_date)
                    print(f"Found calendar element, clicking...")
                    calendar_element.click()
                else:
                    # Default to the original calendar date if no date provided
                    print("Using default date selector...")
                    calendar_date = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '#calendar_2025-03 > div:nth-child(29)'))
                    )
                    calendar_date.click()
                
                # Wait for page load after click
                time.sleep(2)
                
                # Wait for the parking status div
                target_div = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/div[5]/div/div[1]'))
                )
                
                # Wait a moment for any dynamic content to load
                time.sleep(1)
                
                # Try multiple times to get the text in case of stale element
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        div_text = target_div.text.upper()  # Convert to uppercase for case-insensitive comparison
                        break
                    except StaleElementReferenceException:
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(1)
                        target_div = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/div[5]/div/div[1]'))
                        )
                
                current_time = time.strftime("%H:%M:%S")
                print(f"[{current_time}] Current text: {div_text}")  # Debug output
                
                if "SOLD OUT" in div_text or "Car Parking: SOLD OUT" in div_text:
                    print(f"[{current_time}] Still sold out. Waiting 5 seconds before checking again...")
                    time.sleep(5)  # Wait 5 seconds before rechecking
                    driver.refresh()
                    time.sleep(2)  # Wait for page to load
                    continue
                else:
                    print("\n🎉 FOUND AVAILABLE PARKING! 🎉")
                    print("Browser window will remain open so you can complete the reservation.")
                    print("Press Ctrl+C in this terminal to stop the script.")
                    
                    # Play alert sound
                    play_alert()
                    
                    # Keep the browser window open indefinitely
                    while True:
                        time.sleep(1)
                    
            except TimeoutException:
                current_time = time.strftime("%H:%M:%S")
                print(f"[{current_time}] Timeout occurred. Refreshing...")
                driver.refresh()
                time.sleep(2)
                continue
            except StaleElementReferenceException:
                current_time = time.strftime("%H:%M:%S")
                print(f"[{current_time}] Page was updating, retrying...")
                time.sleep(2)
                continue
            except Exception as e:
                current_time = time.strftime("%H:%M:%S")
                print(f"[{current_time}] Unexpected error: {str(e)}")
                print("Refreshing page...")
                driver.refresh()
                time.sleep(2)
                continue
                
    except KeyboardInterrupt:
        print("\nScript stopped by user. Closing browser...")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Error details:", str(e))
    finally:
        driver.quit()

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Check Crystal Mountain parking availability')
    parser.add_argument('--date', type=str, help='Date to check in MM/DD or MM/DD/YYYY format')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the checker with the provided date
    check_parking_availability(args.date) 