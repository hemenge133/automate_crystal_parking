from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
import beepy
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def play_alert():
    """Play alert sound multiple times"""
    for _ in range(10):  # Play 10 times
        beepy.beep(sound=1)
        time.sleep(1)

def check_parking_availability():
    # Get credentials from environment variables
    username = os.getenv('CRYSTAL_USERNAME')
    password = os.getenv('CRYSTAL_PASSWORD')
    
    if not username or not password:
        raise ValueError("Missing credentials in .env file. Please set CRYSTAL_USERNAME and CRYSTAL_PASSWORD")
    
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
        
        try:
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
                    
                    # Wait for and click the calendar date using CSS selector
                    print("Looking for calendar date...")
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
                    print(f"Unexpected error: {str(e)}")
                    print("Refreshing page...")
                    driver.refresh()
                    time.sleep(2)
                    continue
                
        except Exception as e:
            print(f"Error finding login button: {str(e)}")
            print("Trying direct XPath as fallback...")
            first_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/div/div[1]/button[1]'))
            )
            first_button.click()
        
        print("Waiting for login form...")
        # Fill in username and password
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"], input[type="email"]'))
        )
        password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
        
        print("Found login form, entering credentials...")
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Submit the form
        password_field.submit()
        print("Submitted login form")
        
        while True:
            try:
                print("\nLooking for navigation elements...")
                # Try to find the calendar or date selection element
                calendar_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a, button, div[role="button"]'))
                )
                
                # Click elements that might lead to the parking selection
                for element in calendar_elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.text.lower()
                            if 'parking' in element_text or 'reserve' in element_text or 'select' in element_text:
                                print(f"Found relevant element with text: {element.text}")
                                element.click()
                                time.sleep(2)
                                break
                    except:
                        continue
                
                print("Looking for parking status...")
                # Look for elements that might contain parking status
                parking_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div'))
                )
                
                found_status = False
                for element in parking_elements:
                    try:
                        if element.is_displayed():
                            text = element.text.upper()
                            if 'PARKING' in text:
                                print(f"Found parking element with text: {text}")
                                found_status = True
                                if "SOLD OUT" in text:
                                    current_time = time.strftime("%H:%M:%S")
                                    print(f"[{current_time}] Still sold out. Waiting 5 seconds before checking again...")
                                    time.sleep(5)
                                    driver.refresh()
                                    time.sleep(2)
                                    break
                                else:
                                    print("\n🎉 FOUND AVAILABLE PARKING! 🎉")
                                    print("Browser window will remain open so you can complete the reservation.")
                                    print("Press Ctrl+C in this terminal to stop the script.")
                                    while True:
                                        time.sleep(1)
                    except:
                        continue
                
                if not found_status:
                    print("Could not find parking status, refreshing...")
                    driver.refresh()
                    time.sleep(2)
                    
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
                print(f"Unexpected error: {str(e)}")
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
    check_parking_availability() 