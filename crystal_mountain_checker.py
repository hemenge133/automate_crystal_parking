from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time
import beepy
import os
import argparse
import datetime
import threading
import re
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def play_alert():
    """Play alert sound multiple times"""
    try:
        for _ in range(10):  # Play 10 times
            beepy.beep(sound=1)
            time.sleep(1)
    except Exception as e:
        # Fallback to system bell if beepy fails
        print(f"\a")  # System bell
        print(f"(Alert sound unavailable: {e})")

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

def date_invalid(target_date):
    """Check if the given date is in the past"""
    today = datetime.date.today()
    next_week = today + datetime.timedelta(days=7)

    return target_date < today or target_date > next_week

def find_calendar_element(driver, target_date):
    """Find the calendar element for the given date"""
    # Format for calendar element: calendar_YYYY-MM
    calendar_id = f'calendar_{target_date.year}-{target_date.month:02d}'
    print(f"Looking for calendar with ID: {calendar_id}")
    
    try:
        # Wait for the calendar to be visible
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, calendar_id))
        )
        
        # Find all day elements in the target month
        day_elements = driver.find_elements(By.CSS_SELECTOR, f'#{calendar_id} > div')
        
        # Find the element corresponding to the target day
        # First try to find by exact text match (most reliable)
        for element in day_elements:
            try:
                day_text = element.text.strip()
                # Check if the text is exactly the day number we're looking for
                if day_text and day_text.isdigit() and int(day_text) == target_date.day:
                    return element
            except:
                continue
        
        # If not found by text, try matching by data-date attribute
        # Format: 2026-03-08T08:00:00.000Z - extract the day part properly
        for element in day_elements:
            try:
                data_date = element.get_attribute('data-date')
                if data_date:
                    # Parse ISO date format: 2026-03-08T08:00:00.000Z
                    # Extract day from YYYY-MM-DD part
                    date_parts = data_date.split('T')[0].split('-')
                    if len(date_parts) == 3:
                        element_day = int(date_parts[2])
                        if element_day == target_date.day:
                            return element
            except:
                continue
                
        # If we get here, the day wasn't found but the calendar month exists
        print(f"Warning: Day {target_date.day} not found in calendar {calendar_id}.")
        return None
            
    except (TimeoutException, NoSuchElementException):
        print(f"Calendar for {target_date.month}/{target_date.year} is not available.")
        print("Crystal Mountain may not have opened reservations for this month yet.")
        return None

def complete_reservation(driver, target_date):
    """Click the parking button and checkout to complete the reservation"""
    try:
        print("Attempting to complete reservation...")
        
        # Wait a moment for any dynamic content to settle
        time.sleep(2)

        # Wait for spot-select to be populated (AJAX fills it after calendar click)
        spot_select = None
        for attempt in range(5):
            try:
                spot_select = driver.find_element(By.ID, 'spot-select')
                buttons = spot_select.find_elements(By.CSS_SELECTOR, '.spot-row')
                if buttons:
                    print(f"✅ Found spot-select with {len(buttons)} spot-row elements")
                    for i, btn in enumerate(buttons):
                        try:
                            data_type = btn.get_attribute('data-type')
                            text = btn.text[:60] if btn.text else "no text"
                            print(f"   Row {i}: data-type={data_type}, text={text}")
                        except Exception as ex:
                            print(f"   Row {i}: error getting attrs: {ex}")
                    break
                else:
                    print(f"   spot-select found but empty, retrying ({attempt+1}/5)...")
            except Exception as e:
                print(f"   spot-select not found, retrying ({attempt+1}/5)...")
            time.sleep(1)
        else:
            print("❌ spot-select never populated after 5 attempts")
        
        # Click the "Reserve car parking" button
        # The actual clickable element is a div with class 'add2cart' and data-type='car'
        parking_button = None
        
        # Try multiple selectors (including fallbacks that don't depend on #spot-select)
        selectors = [
            (By.CSS_SELECTOR, '#spot-select .add2cart[data-type="car"]'),
            (By.CSS_SELECTOR, '#spot-select .spot-row[data-type="car"]'),
            (By.XPATH, '//div[@id="spot-select"]//div[contains(@class, "add2cart") and @data-type="car"]'),
            (By.XPATH, '//div[@id="spot-select"]//div[contains(text(), "Reserve Car Parking")]'),
            # Fallback selectors that don't require #spot-select
            (By.CSS_SELECTOR, '.add2cart[data-type="car"]'),
            (By.CSS_SELECTOR, '.spot-row[data-type="car"]'),
            (By.XPATH, '//div[contains(@class, "add2cart") and @data-type="car"]'),
            (By.XPATH, '//*[contains(text(), "Reserve Car Parking")]'),
            (By.XPATH, '//*[contains(text(), "Reserve car parking")]'),
            (By.XPATH, '//*[contains(text(), "Car Parking") and (contains(@class, "add") or contains(@class, "btn") or contains(@class, "reserve"))]'),
        ]
        
        for by, selector in selectors:
            try:
                parking_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                print(f"✅ Found parking button using: {selector}")
                break
            except:
                continue
        
        if not parking_button:
            print("❌ Could not find parking button with any selector")
            return False
        
        try:
            print(f"Clicking parking button (tag: {parking_button.tag_name})...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parking_button)
            time.sleep(0.5)
            
            # Click using regular click (JavaScript click might bypass the event handler)
            parking_button.click()
            print("✅ Clicked 'Reserve car parking' button")
            time.sleep(3)  # Wait for AJAX call and redirect
            
            # Debug: Check current URL
            current_url = driver.current_url
            print(f"Current URL after clicking reserve: {current_url}")
            
        except Exception as e:
            print(f"❌ Error clicking parking button: {e}")
            return False
        
        # Check if we're back at the calendar page
        calendar_id = f'calendar_{target_date.year}-{target_date.month:02d}'
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, calendar_id))
            )
            print("⚠️ We're back at the calendar page after clicking reserve")
            print("The click may have triggered a page refresh. Will retry...")
            return False
        except:
            # Not at calendar page, good - continue to checkout
            pass
        
        # After adding to cart, we should be redirected to cart page or stay on same page
        # The AJAX call redirects to /cart/ on success
        # Wait for the cart page to load and click checkout
        try:
            # First, select the last option from the form dropdown if it exists
            # XPath: /html/body/div[1]/div[1]/select
            try:
                select_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/select'))
                )
                # Get all options and select the last one
                options = select_element.find_elements(By.TAG_NAME, 'option')
                if len(options) > 0:
                    last_option = options[-1]
                    last_option_text = last_option.text
                    print(f"Found select dropdown with {len(options)} options, selecting last: '{last_option_text}'")
                    last_option.click()
                    time.sleep(1)
                    print("✅ Selected last option from dropdown")
                else:
                    print("Select dropdown found but no options available")
            except Exception as e:
                print(f"Select dropdown not found or error selecting: {e}")
                # Continue anyway, the select might not always be present
            
            # Wait for either the checkout button or cart page elements
            checkout_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="btnCheckout"]'))
            )
            print("Found checkout button, clicking...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkout_button)
            time.sleep(0.5)
            checkout_button.click()
            print("✅ Successfully clicked checkout button!")
            time.sleep(3)  # Wait for checkout page to load
            return True
        except Exception as e:
            print(f"❌ Error clicking checkout button: {e}")
            print("Reserve button was clicked. You may need to click checkout manually.")
            return True  # Return True since we at least tried to reserve
            
    except Exception as e:
        print(f"❌ Error completing reservation: {e}")
        return False

def check_parking_availability(date_str=None):
    # Get credentials from environment variables
    username = os.getenv('CRYSTAL_USERNAME')
    password = os.getenv('CRYSTAL_PASSWORD')
    
    if not username or not password:
        raise ValueError("Missing credentials in .env file. Please set CRYSTAL_USERNAME and CRYSTAL_PASSWORD")
    
    # Parse date if provided
    target_date = None
    if date_str:
        try:
            target_date = parse_date(date_str)
            print(f"Checking availability for: {target_date.month}/{target_date.day}/{target_date.year}")
            
            if date_invalid(target_date):
                print(f"Error: The selected date ({target_date.month}/{target_date.day}/{target_date.year}) is in the past.")
                print("Please select a current or future date.")
                return
                
        except ValueError as e:
            print(f"Error: {e}")
            return
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
        
        # Navigate to main page
        print("Navigating to main page...")
        driver.get('https://parking.crystalmountainresort.com/')
        time.sleep(2)  # Wait for page load
        
        # Find and click the calendar date
        if target_date:
            print(f"Looking for date: {target_date.month}/{target_date.day}/{target_date.year}")
            calendar_element = find_calendar_element(driver, target_date)
            if not calendar_element:
                print("Error: Could not find the requested date in the available calendars.")
                print("Please check if this date is available for booking.")
                return
            
            print(f"Found calendar element, clicking...")
            calendar_element.click()
        else:
            # Default to the original calendar date if no date provided
            print("Using default date selector...")
            try:
                calendar_date = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '#calendar_2025-03 > div:nth-child(29)'))
                )
                calendar_date.click()
            except TimeoutException:
                print("Error: Default date (March 29, 2025) is not available in the calendar.")
                print("Please specify a date using the --date argument.")
                return
        
        # Now begin the monitoring loop
        print("Starting to monitor for parking availability...")
        
        # Track if we need to (re)click the calendar date
        needs_date_click = False
        
        while True:
            try:
                # If we need to click the date (first run or after refresh), find and click it
                if needs_date_click:
                    print("Re-finding and clicking calendar date...")
                    calendar_element = find_calendar_element(driver, target_date)
                    if calendar_element:
                        calendar_element.click()
                        print("Clicked calendar date, waiting for page to load...")
                    else:
                        print("Warning: Could not find calendar date element, retrying...")
                        time.sleep(2)
                        continue
                    needs_date_click = False
                
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
                    needs_date_click = True  # Need to click date after refresh
                    continue
                else:
                    print("\n🎉 FOUND AVAILABLE PARKING! 🎉")
                    
                    # Play alert sound in background (non-blocking)
                    threading.Thread(target=play_alert, daemon=True).start()
                    
                    # Attempt to complete the reservation
                    success = complete_reservation(driver, target_date)
                    
                    if success:
                        print("\n✅ Reservation process initiated successfully!")
                        print("Please check the browser to confirm and complete any remaining steps.")
                        print("Browser window will remain open. Press Ctrl+C to exit.")
                    else:
                        print("\n⚠️ Could not complete reservation automatically.")
                        print("Browser window will remain open for manual completion.")
                        print("Press Ctrl+C to exit.")
                    
                    # Keep the browser window open indefinitely
                    while True:
                        try:
                            time.sleep(1)
                        except KeyboardInterrupt:
                            print("\nScript stopped by user. Closing browser...")
                            return  # Exit the function completely
                    
            except TimeoutException:
                current_time = time.strftime("%H:%M:%S")
                print(f"[{current_time}] Timeout occurred. Refreshing...")
                driver.refresh()
                time.sleep(2)
                needs_date_click = True  # Need to click date after refresh
                continue
            except StaleElementReferenceException:
                current_time = time.strftime("%H:%M:%S")
                print(f"[{current_time}] Page was updating, retrying...")
                time.sleep(2)
                needs_date_click = True  # Need to click date after page update
                continue
            except Exception as e:
                current_time = time.strftime("%H:%M:%S")
                print(f"[{current_time}] Unexpected error: {str(e)}")
                print("Refreshing page...")
                driver.refresh()
                time.sleep(2)
                needs_date_click = True  # Need to click date after refresh
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