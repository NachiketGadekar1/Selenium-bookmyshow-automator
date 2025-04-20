import time
import re
import os
import datetime
from datetime import datetime, time as dt_time # Use alias for time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException

# --- Constants ---
BASE_URL = "https://in.bookmyshow.com/movies/"
DEFAULT_TIMEOUT = 15  # Default wait time for elements
DATE_SELECTION_TIMEOUT = 10 # Wait time specifically for date element
THEATRE_TIMEOUT = 10 # Wait time for theatre/showtime elements
SEAT_QTY_TIMEOUT = 10 # Wait time for seat quantity elements
PROFILE_FOLDER_NAME = "bms_chrome_profile" # Folder to store persistent profile
SEAT_SELECTION_TIMEOUT = 20 # Timeout for finding seats and the pay button
SEAT_QTY_TIMEOUT = 15 # Increase slightly if needed
SEAT_SELECTION_TIMEOUT = 25 # Timeout for the overall seat selection process
PAY_BUTTON_CHECK_TIMEOUT = 3 # Short timeout for checking if pay button appears after a click
MAX_SEAT_CLICK_ATTEMPTS = 50 # Max number of different seats to try clicking
ACCEPT_TC_TIMEOUT = 15      # Timeout for the T&C Accept button
SUMMARY_PROCEED_TIMEOUT = 40 # Timeout for the Summary Proceed button
CONTACT_DETAILS_TIMEOUT = 20 # Timeout for contact details section
PAYMENT_OPTION_TIMEOUT = 25  # Timeout for payment options to load/be clickable
UPI_PAYMENT_TIMEOUT = 30 # Timeout for entering UPI details and clicking final pay
REFRESH_INTERVAL_SECONDS = 300 # e.g., 300 seconds = 5 minutes
BOOK_BUTTON_CHECK_TIMEOUT = 10 # Shorter timeout specifically for checking if book button exists


# --- Configuration ---
CHROMIUM_BINARY_PATH = "/usr/bin/chromium-browser" #<-- ADJUST THIS IF NEEDED or set to None

# --- Helper Functions ---

def parse_time_string(time_str: str) -> dt_time | None:
    """Parses a time string (HH:MM AM/PM or HH:MM) into a datetime.time object."""
    time_str = time_str.strip().upper()
    formats_to_try = ["%I:%M %p", "%H:%M", "%I:%M%p"]
    for fmt in formats_to_try:
        try:
            if ('%I' in fmt) and (':' in time_str):
                 parts = time_str.split(':')
                 if len(parts[0]) == 1 and ('AM' in time_str or 'PM' in time_str):
                      time_str_padded = f"0{time_str}"
                      try: return datetime.strptime(time_str_padded, fmt).time()
                      except ValueError: pass
            return datetime.strptime(time_str, fmt).time()
        except ValueError: continue
    print(f"Error: Could not parse time string '{time_str}'. Use 'HH:MM' or 'HH:MM AM/PM'.")
    return None

# --- Core Functions ---

def setup_driver(profile_dir_name: str, binary_path: str | None = None) -> uc.Chrome | None:
    """Initializes undetected-chromedriver with a persistent profile."""
    driver = None
    try:
        print("Setting up undetected-chromedriver with persistent profile...")
        options = uc.ChromeOptions()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        profile_path = os.path.join(script_dir, profile_dir_name)
        print(f"Using profile directory: {profile_path}")
        options.add_argument(f'--user-data-dir={profile_path}')
        if binary_path:
            print(f"Setting binary location: {binary_path}")
            options.binary_location = binary_path
        options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = uc.Chrome(options=options, use_subprocess=True)
        print("WebDriver initialized successfully.")
        return driver
    except Exception as e:
        print(f"\n--- Error setting up WebDriver: {e} ---")
        if "cannot find chrome binary" in str(e).lower() and not binary_path: print("Hint: Auto-detection failed. Try setting CHROMIUM_BINARY_PATH.")
        elif "session not created" in str(e).lower() and "version" in str(e).lower(): print("Hint: Version mismatch? Ensure uc is updated.")
        return None

def navigate_to_movie(driver: uc.Chrome, location_slug: str, movie_code: str) -> bool:
    """Navigates to the movie page and checks for blocks."""
    try:
        target_url = f"{BASE_URL}{location_slug}/{movie_code}"
        print(f"\nNavigating to: {target_url}")
        driver.get(target_url)
        print(f"Page navigation initiated.")
        time.sleep(3)
        page_title = driver.title
        print(f"Page Title after pause: {page_title}")
        page_title_lower = page_title.lower()
        current_url_lower = driver.current_url.lower()
        if "challenge" in current_url_lower or "cloudflare" in page_title_lower or "just a moment" in page_title_lower :
             print("\n*** WARNING: Cloudflare challenge or block page detected! ***")
             return False
        elif "403 forbidden" in page_title_lower:
             print("\n*** WARNING: Received a 403 Forbidden error - likely blocked. ***")
             return False
        elif "page not found" in page_title_lower or "oops" in page_title_lower:
             print("\n*** WARNING: Page not found or error page detected. Check location/movie code. ***")
             return False
        else:
            print("Page loaded without immediate signs of blocking.")
            return True
    except Exception as e:
        print(f"\n--- Error during navigation: {e} ---")
        return False

def click_book_tickets(driver: uc.Chrome, timeout: int = BOOK_BUTTON_CHECK_TIMEOUT) -> bool | None:
    """
    Finds and clicks the 'Book tickets' button.
    If the button isn't found within the timeout (TimeoutException), returns None.
    Returns False for other errors during the process.
    Returns True if successfully clicked.

    Args:
        driver: The initialized WebDriver instance.
        timeout: Maximum time to wait specifically for the button check.

    Returns:
        True if clicked successfully.
        None if button not found after timeout (likely upcoming).
        False if another error occurred during the check/click attempt.
    """
    print("\nLooking for the 'Book tickets' button...")
    book_button_locator = (By.XPATH, "//button[.//span[contains(text(), 'Book tickets')]]")

    try:
        wait = WebDriverWait(driver, timeout)
        # Wait for the button to be present first
        wait.until(EC.presence_of_element_located(book_button_locator))
        # Now wait for it to be clickable
        book_button = wait.until(EC.element_to_be_clickable(book_button_locator))

        print("Button found and clickable. Clicking...")
        # Scroll and click using JavaScript for robustness
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", book_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", book_button)
        print("Clicked 'Book tickets'.")
        return True # Signal successful click

    except TimeoutException:
        # This is the expected case for an upcoming movie
        print(f"'Book tickets' button not found or not clickable within {timeout} seconds.")
        return None # Signal button not found (likely upcoming)

    except Exception as e:
        # Any other error during finding/clicking is unexpected
        print(f"\n--- Error interacting with 'Book tickets' button: {e} ---")
        return False # Signal an actual error occurred

def select_show_date(driver: uc.Chrome, date_input_str: str, timeout: int = DATE_SELECTION_TIMEOUT) -> bool:
    """Finds and clicks the date element corresponding to the provided input."""
    print("\n--- Date Selection ---")
    try:
        # Basic parsing (already validated in main)
        parts = date_input_str.split()
        month_abbr, day_str = parts[0], parts[1]
        month_map = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
        month_num = month_map[month_abbr]
        day_num = int(day_str)
        day_num_padded = f"{day_num:02d}"
        current_year = datetime.now().year
        current_month = datetime.now().month
        if int(month_num) < current_month: current_year += 1
        print(f"Assuming year: {current_year}")
        target_date_id = f"{current_year}{month_num}{day_num_padded}"
        print(f"Looking for date element with ID: {target_date_id}")

        # Find and click
        date_locator = (By.ID, target_date_id)
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located(date_locator))
        date_element = wait.until(EC.element_to_be_clickable(date_locator))
        print(f"Found date '{date_input_str}'. Clicking...")
        driver.execute_script("arguments[0].scrollIntoView(true);", date_element)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", date_element)
        print("Clicked the date.")
        time.sleep(2) # Wait for theatre list refresh
        return True
    except (ValueError, KeyError) as parse_error:
        print(f"Error processing date input '{date_input_str}': {parse_error}")
        return False
    except TimeoutException:
        print(f"\n--- ERROR: Date '{date_input_str}' (ID: {target_date_id}) not found/clickable within {timeout}s. ---")
        return False
    except Exception as e:
        print(f"\n--- Error during date selection: {e} ---")
        return False

def select_theatre_and_time(driver: uc.Chrome, theatre_name: str, start_time_str: str, end_time_str: str, timeout: int = THEATRE_TIMEOUT) -> bool:
    """Finds the specified theatre and clicks the first showtime within the given time range."""
    print("\n--- Theatre and Time Selection ---")
    print(f"Looking for Theatre: '{theatre_name}'")
    print(f"Desired Time Range: {start_time_str} - {end_time_str}")
    start_time = parse_time_string(start_time_str)
    end_time = parse_time_string(end_time_str)
    if start_time is None or end_time is None: return False
    if start_time > end_time: print("Warning: Start time > End time.")

    try:
        # Locate Theatre Block
        theatre_name_locator = (By.XPATH, f"//div[contains(@class, 'hvoTNx')]")
        wait = WebDriverWait(driver, timeout)
        driver.execute_script("window.scrollBy(0, 500);") # Scroll to load theatres
        time.sleep(1)
        wait.until(EC.presence_of_element_located(theatre_name_locator))
        time.sleep(1)

        # Find specific theatre name element
        safe_theatre_name = theatre_name.replace("'", "\\'").replace('"', '\\"')
        theatre_name_element_xpath = f"//div[contains(@class, 'hvoTNx') and normalize-space(text())='{safe_theatre_name}']"
        print(f"Using XPath for name: {theatre_name_element_xpath}")
        theatre_name_element = driver.find_element(By.XPATH, theatre_name_element_xpath)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", theatre_name_element)
        time.sleep(0.5)

        # Find ancestor block containing showtimes
        theatre_block_xpath = "./ancestor::div[contains(@class, 'sc-e8nk8f-3')][1]"
        print(f"Looking for theatre block using XPath: {theatre_block_xpath} relative to name")
        theatre_block = theatre_name_element.find_element(By.XPATH, theatre_block_xpath)
        print(f"Found theatre block for '{theatre_name}'. Searching showtimes...")

        # Find Showtimes within block
        showtime_locator = (By.XPATH, ".//div[contains(@class, 'sc-1vhizuf-2')]")
        WebDriverWait(theatre_block, 5).until(EC.presence_of_element_located(showtime_locator))
        showtime_elements = theatre_block.find_elements(*showtime_locator)
        if not showtime_elements:
            print(f"No showtime elements found for '{theatre_name}'.")
            return False

        # Iterate and Click Matching Showtime
        showtime_clicked = False
        for i, showtime_element in enumerate(showtime_elements):
            try:
                showtime_text = showtime_element.text.strip()
                if not showtime_text: continue
                print(f"  Checking showtime: {showtime_text}")
                current_show_time = parse_time_string(showtime_text)

                if current_show_time and (start_time <= current_show_time <= end_time):
                    print(f"  Found matching showtime: {showtime_text}. Clicking...")
                    clickable_showtime = wait.until(EC.element_to_be_clickable(showtime_element))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickable_showtime)
                    time.sleep(0.5)
                    # Use JS click as it might be more reliable for these elements
                    driver.execute_script("arguments[0].click();", clickable_showtime)
                    print(f"  Successfully clicked showtime: {showtime_text}")
                    showtime_clicked = True
                    break
                elif not current_show_time: print(f"    -> Could not parse time: {showtime_text}")

            except StaleElementReferenceException:
                 print(f"  Warning: Showtime element {i} became stale. Skipping.")
                 continue
            except Exception as loop_error:
                 print(f"  Error processing showtime '{showtime_text}': {loop_error}")
                 continue

        if not showtime_clicked:
            print(f"\n--- No showtimes found for '{theatre_name}' in range {start_time_str}-{end_time_str}. ---")
            return False
        return True

    except NoSuchElementException:
        print(f"\n--- ERROR: Could not find theatre named '{theatre_name}'. Check spelling/capitalization. ---")
        return False
    except TimeoutException:
         print(f"\n--- ERROR: Timed out waiting for theatre/showtime elements for '{theatre_name}'. ---")
         return False
    except Exception as e:
        print(f"\n--- Error during theatre/time selection for '{theatre_name}': {e} ---")
        import traceback; traceback.print_exc()
        return False

def select_seat_quantity(driver: uc.Chrome, num_seats: int, timeout: int = SEAT_QTY_TIMEOUT) -> bool:
    """
    Selects the desired number of seats from the quantity selection pop-up.
    Waits specifically for the number element to be clickable.

    Args:
        driver: The initialized WebDriver instance.
        num_seats: The number of seats to select (typically 1-10).
        timeout: Maximum time to wait for elements.

    Returns:
        True if the quantity was selected and confirmed, False otherwise.
    """
    print("\n--- Seat Quantity Selection ---")
    print(f"Selecting quantity: {num_seats}")

    try:
        wait = WebDriverWait(driver, timeout)
        qty_item_id = f"pop_{num_seats}"
        qty_item_locator = (By.ID, qty_item_id)
        select_seats_button_locator = (By.ID, "proceed-Qty") # Changed to div ID

        # --- Wait for the specific quantity list item to be present and clickable ---
        # It implicitly waits for the container list as well
        print(f"Waiting for quantity item '{qty_item_id}' to be clickable...")
        try:
            qty_element = wait.until(EC.element_to_be_clickable(qty_item_locator))
            print(f"Found clickable quantity '{num_seats}' (ID: {qty_item_id}).")
        except TimeoutException:
             print(f"\n--- ERROR: Timed out waiting for the seat quantity number '{num_seats}' (ID: {qty_item_id}) to be clickable within {timeout}s. ---")
             print("       Is the quantity pop-up visible and does it contain this number?")
             # You could try taking a screenshot here for debugging
             # driver.save_screenshot("screenshot_qty_timeout.png")
             return False

        # --- Click the specific quantity ---
        try:
            print(f"Attempting standard click on quantity '{num_seats}'...")
            # Scroll into view just in case, although wait should handle it
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", qty_element)
            time.sleep(0.5) # Brief pause before click
            qty_element.click()
            print(f"Clicked quantity '{num_seats}' using standard click.")
        except ElementClickInterceptedException:
            print("Standard click intercepted. Trying JavaScript click...")
            try:
                driver.execute_script("arguments[0].click();", qty_element)
                print(f"Clicked quantity '{num_seats}' using JavaScript click.")
            except Exception as js_e:
                print(f"\n--- ERROR: Both standard and JavaScript clicks failed for quantity '{num_seats}': {js_e} ---")
                return False
        except Exception as e:
             print(f"\n--- ERROR: Failed to click quantity '{num_seats}': {e} ---")
             return False

        time.sleep(1) # Pause after clicking quantity for any UI updates

        # --- Locate and Click the "Select Seats" button ---
        print("Looking for 'Select Seats' button (ID: proceed-Qty)...")
        try:
            select_button = wait.until(EC.element_to_be_clickable(select_seats_button_locator))
            print("Found 'Select Seats' button. Clicking...")
            driver.execute_script("arguments[0].click();", select_button) # JS click often better for divs acting as buttons
            print("Clicked 'Select Seats' button.")
            return True
        except TimeoutException:
            print(f"\n--- ERROR: Timed out waiting for 'Select Seats' button (ID: proceed-Qty) to be clickable within {timeout}s. ---")
            # driver.save_screenshot("screenshot_select_seats_timeout.png")
            return False
        except Exception as e:
             print(f"\n--- ERROR: Failed to click 'Select Seats' button: {e} ---")
             return False

    # Keep general exception handlers
    except NoSuchElementException: # Should be caught by specific waits now, but keep as fallback
        print(f"\n--- ERROR: Could not find seat quantity element (Item ID: {qty_item_id} or Button ID: proceed-Qty). ---")
        return False
    except Exception as e:
        print(f"\n--- Unexpected Error during seat quantity selection: {e} ---")
        import traceback; traceback.print_exc()
        return False
# --- Core Functions ---
# ... (select_seat_quantity function) ...

def select_seats_and_pay(driver: uc.Chrome, num_seats_to_select: int, timeout: int = SEAT_SELECTION_TIMEOUT) -> bool:
    """
    Selects seats by clicking one available seat and checking if the 'Pay'
    button activates (indicating auto-selection worked). Retries with different
    seats if needed.

    Args:
        driver: The initialized WebDriver instance.
        num_seats_to_select: The number of seats required (used for logging).
        timeout: Max time for the overall process including finding seats initially.

    Returns:
        True if seats were selected and pay button clicked, False otherwise.
    """
    print("\n--- Seat Selection (Auto-Select Strategy) ---")
    print(f"Trying to select {num_seats_to_select} seats by clicking one and checking...")

    pay_button_locator = (By.ID, "btmcntbook")
    available_seat_locator = (By.XPATH, "//div[contains(@class, 'seatI')]/a[contains(@class, '_available')]")
    main_wait = WebDriverWait(driver, timeout)
    # Short wait specifically for checking the pay button after each click
    check_wait = WebDriverWait(driver, PAY_BUTTON_CHECK_TIMEOUT)

    try:
        # --- Wait for the seat layout and find initial available seats ---
        print("Waiting for available seats to appear...")
        try:
            main_wait.until(EC.presence_of_element_located(available_seat_locator))
            print("Seat layout detected. Finding available seats...")
            time.sleep(2) # Allow dynamic elements to settle
            available_seat_elements = driver.find_elements(*available_seat_locator)
        except TimeoutException:
             print(f"\n--- ERROR: Timed out waiting for any available seats to appear within {timeout}s. ---")
             return False


        if not available_seat_elements:
            print("\n--- ERROR: No available seat elements found on the page. ---")
            return False

        print(f"Found {len(available_seat_elements)} initially available seat elements.")

        # --- Loop through available seats, click one, check pay button ---
        pay_button_found_and_clickable = False
        tried_seat_ids = set() # Keep track of seats we already tried

        for attempt in range(min(MAX_SEAT_CLICK_ATTEMPTS, len(available_seat_elements))):
            # --- Select a seat to try ---
            # Simple strategy: iterate through the list found initially.
            # More complex: Re-find elements, parse IDs, prioritize middle rows etc.
            # Let's stick to the initial list for now.
            seat_link = available_seat_elements[attempt] # This might go stale, better to re-find based on ID if possible

            try:
                # --- Get Seat ID --- Find parent div and get ID
                parent_div = seat_link.find_element(By.XPATH, "./parent::div")
                seat_id = parent_div.get_attribute("id")

                if not seat_id or '_' not in seat_id:
                    print(f"  Attempt {attempt+1}: Skipping seat - invalid or missing ID.")
                    continue

                if seat_id in tried_seat_ids:
                     print(f"  Attempt {attempt+1}: Skipping seat {seat_id} - already tried.")
                     continue

                print(f"\nAttempt {attempt+1}/{MAX_SEAT_CLICK_ATTEMPTS}: Trying seat ID: {seat_id}")
                tried_seat_ids.add(seat_id)

                # --- Click the seat using JavaScript ---
                # Re-locate element just before clicking for freshness
                current_seat_link = driver.find_element(By.XPATH, f"//div[@id='{seat_id}']/a")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", current_seat_link)
                time.sleep(0.3)
                driver.execute_script(f"fnSelectSeat('{seat_id}');")
                print(f"  Clicked seat {seat_id}. Waiting {PAY_BUTTON_CHECK_TIMEOUT}s for Pay button...")
                time.sleep(0.5) # Small pause for JS execution

                # --- Check if Pay button is now clickable ---
                try:
                    pay_button = check_wait.until(EC.element_to_be_clickable(pay_button_locator))
                    print(f"  SUCCESS: Pay button (ID: {pay_button_locator[1]}) is now clickable after clicking {seat_id}.")
                    pay_button_found_and_clickable = True
                    # Click the pay button now that we know it's ready
                    print("  Clicking the 'Pay' button...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", pay_button)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", pay_button)
                    print("  Clicked 'Pay' button.")
                    break # Exit the attempt loop

                except TimeoutException:
                    print(f"  Pay button not clickable after clicking {seat_id}. Trying next seat...")
                    # Optional: Add code here to explicitly clear selection if necessary
                    # clear_button = driver.find_elements(By.XPATH, "//a[contains(@onclick, 'fnClearSel')]")
                    # if clear_button and clear_button[0].is_displayed():
                    #    print("  Clearing selection...")
                    #    clear_button[0].click()
                    #    time.sleep(0.5)
                    continue # Continue to the next attempt

            except StaleElementReferenceException:
                print(f"  Attempt {attempt+1}: StaleElementReferenceException for seat {seat_id}. Skipping.")
                # Remove ID if it was added, as the element ref was bad
                if seat_id and seat_id in tried_seat_ids: tried_seat_ids.remove(seat_id)
                continue
            except NoSuchElementException:
                 print(f"  Attempt {attempt+1}: NoSuchElementException trying to process seat {seat_id}. Maybe it changed?")
                 if seat_id and seat_id in tried_seat_ids: tried_seat_ids.remove(seat_id)
                 continue
            except Exception as click_error:
                print(f"  Attempt {attempt+1}: Error clicking or checking seat {seat_id}: {click_error}")
                continue # Try next seat

        # --- Final Check ---
        if pay_button_found_and_clickable:
            print("\nSeat selection successful and 'Pay' button clicked.")
            return True
        else:
            print(f"\n--- ERROR: Failed to select {num_seats_to_select} seats and activate Pay button after {attempt+1} attempts. ---")
            return False

    except Exception as e:
        print(f"\n--- Unexpected Error during seat selection/pay: {e} ---")
        import traceback; traceback.print_exc()
        return False

def accept_terms_and_conditions(driver: uc.Chrome, timeout: int = ACCEPT_TC_TIMEOUT) -> bool:
    """
    Finds and clicks the 'Accept' button on the Terms & Conditions pop-up/page.

    Args:
        driver: The initialized WebDriver instance.
        timeout: Maximum time to wait for the button.

    Returns:
        True if the button was clicked, False otherwise.
    """
    print("\n--- Terms & Conditions Acceptance ---")
    accept_button_locator = (By.ID, "btnPopupAccept")

    try:
        wait = WebDriverWait(driver, timeout)
        print(f"Waiting for T&C 'Accept' button (ID: {accept_button_locator[1]}) to be clickable...")
        accept_button = wait.until(EC.element_to_be_clickable(accept_button_locator))

        print("Found 'Accept' button. Clicking...")
        driver.execute_script("arguments[0].scrollIntoView(true);", accept_button) # Scroll just in case
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", accept_button) # JS click is reliable for divs
        print("Clicked T&C 'Accept' button.")
        return True

    except TimeoutException:
        print(f"\n--- ERROR: Timed out waiting for T&C 'Accept' button (ID: {accept_button_locator[1]}) within {timeout}s. ---")
        # driver.save_screenshot("screenshot_tc_timeout.png")
        return False
    except NoSuchElementException:
        print(f"\n--- ERROR: Could not find T&C 'Accept' button (ID: {accept_button_locator[1]}). ---")
        return False
    except Exception as e:
        print(f"\n--- Error clicking T&C 'Accept' button: {e} ---")
        import traceback; traceback.print_exc()
        return False

def proceed_on_summary(driver: uc.Chrome, timeout: int = SUMMARY_PROCEED_TIMEOUT) -> bool:
    """
    Finds and clicks the 'Proceed' button on the booking summary page.

    Args:
        driver: The initialized WebDriver instance.
        timeout: Maximum time to wait for the button.

    Returns:
        True if the button was clicked, False otherwise.
    """
    print("\n--- Booking Summary ---")
    proceed_button_locator = (By.ID, "prePay") # The div with onclick='fnPrePay()'

    try:
        wait = WebDriverWait(driver, timeout)
        print(f"Waiting for Summary 'Proceed' button (ID: {proceed_button_locator[1]}) to be clickable...")
        # Ensure it's visible first, then clickable, as it might change state
        wait.until(EC.visibility_of_element_located(proceed_button_locator))
        proceed_button = wait.until(EC.element_to_be_clickable(proceed_button_locator))

        print("Found 'Proceed' button. Clicking...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", proceed_button) # Scroll
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", proceed_button) # JS click for the div
        print("Clicked Summary 'Proceed' button.")
        return True

    except TimeoutException:
        print(f"\n--- ERROR: Timed out waiting for Summary 'Proceed' button (ID: {proceed_button_locator[1]}) to be clickable within {timeout}s. ---")
        # Check if the disabled button is present instead?
        try:
            disabled_btn = driver.find_element(By.ID, "btnseatdisab")
            if disabled_btn.is_displayed():
                print("      (Note: 'Please wait...' button is visible instead.)")
        except: # Ignore if disabled button isn't found
             pass
        # driver.save_screenshot("screenshot_summary_timeout.png")
        return False
    except NoSuchElementException:
        print(f"\n--- ERROR: Could not find Summary 'Proceed' button (ID: {proceed_button_locator[1]}). ---")
        return False
    except Exception as e:
        print(f"\n--- Error clicking Summary 'Proceed' button: {e} ---")
        import traceback; traceback.print_exc()
        return False

def enter_contact_details(driver: uc.Chrome, phone_number: str, timeout: int = CONTACT_DETAILS_TIMEOUT) -> bool:
    """
    Enters the mobile number on the payment page and clicks Continue.

    Args:
        driver: The initialized WebDriver instance.
        phone_number: The 10-digit phone number string.
        timeout: Maximum time to wait for elements.

    Returns:
        True if details entered and continue clicked, False otherwise.
    """
    print("\n--- Entering Contact Details ---")
    mobile_input_locator = (By.ID, "txtMobile")
    # This XPath targets the 'Continue' link within the specific div
    continue_button_locator = (By.XPATH, "//div[@id='dContinueContactSec']/a[contains(@onclick, 'pay.fnValUserDetails')]")

    try:
        wait = WebDriverWait(driver, timeout)

        # --- Enter Mobile Number ---
        print(f"Waiting for mobile number input (ID: {mobile_input_locator[1]})...")
        mobile_input = wait.until(EC.visibility_of_element_located(mobile_input_locator))
        print("Found mobile input. Clearing and entering number...")
        mobile_input.clear() # Clear any default value like +91
        time.sleep(0.3)
        mobile_input.send_keys(phone_number)
        print(f"Entered phone number: {phone_number}")
        time.sleep(0.5) # Pause after sending keys

        # --- Click Continue Button ---
        print(f"Waiting for contact details 'Continue' button to be clickable...")
        continue_button = wait.until(EC.element_to_be_clickable(continue_button_locator))
        print("Found 'Continue' button. Clicking...")
        # Use JS click as it's an <a> tag with complex onclick
        driver.execute_script("arguments[0].click();", continue_button)
        # Alternative JS execution (less preferred):
        # driver.execute_script("pay.fnValUserDetails('decodePlus');")
        print("Clicked contact details 'Continue' button.")
        return True

    except TimeoutException:
        print(f"\n--- ERROR: Timed out waiting for contact details elements (Input or Continue button) within {timeout}s. ---")
        # driver.save_screenshot("screenshot_contact_timeout.png")
        return False
    except NoSuchElementException:
        print(f"\n--- ERROR: Could not find contact details elements (Input ID: {mobile_input_locator[1]} or Continue button). ---")
        return False
    except Exception as e:
        print(f"\n--- Error entering contact details or clicking continue: {e} ---")
        import traceback; traceback.print_exc()
        return False

def select_phonepe_upi(driver: uc.Chrome, timeout: int = PAYMENT_OPTION_TIMEOUT) -> bool:
    """
    Selects PhonePe UPI as the payment method.

    Args:
        driver: The initialized WebDriver instance.
        timeout: Maximum time to wait for the payment option.

    Returns:
        True if PhonePe was selected, False otherwise.
    """
    print("\n--- Selecting Payment Method ---")
    # This XPath targets the label based on the specific onclick JS call for PhonePe UPI
    phonepe_label_locator = (By.XPATH, "//label[contains(@onclick, \"pay.fnSetUPI\") and contains(@onclick, \"'PHONEPE'\")]")

    try:
        wait = WebDriverWait(driver, timeout)
        print("Waiting for UPI options to load and PhonePe label to be clickable...")
        # Wait for the general UPI section maybe? Or directly for the label.
        # Let's wait directly for the label to be clickable.
        phonepe_label = wait.until(EC.element_to_be_clickable(phonepe_label_locator))

        print("Found PhonePe UPI label. Clicking...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", phonepe_label) # Scroll to it
        time.sleep(0.5)
        # Standard click should work on labels, but JS is also safe
        phonepe_label.click()
        # driver.execute_script("arguments[0].click();", phonepe_label)
        print("Clicked PhonePe UPI label.")
        return True

    except TimeoutException:
        print(f"\n--- ERROR: Timed out waiting for PhonePe UPI option to be clickable within {timeout}s. ---")
        print("       Is the UPI payment section visible? Has PhonePe loaded?")
        # driver.save_screenshot("screenshot_phonepe_timeout.png")
        return False
    except NoSuchElementException:
        print(f"\n--- ERROR: Could not find the PhonePe UPI label element. Check XPath. ---")
        return False
    except Exception as e:
        print(f"\n--- Error selecting PhonePe UPI option: {e} ---")
        import traceback; traceback.print_exc()
        return False

def enter_upi_details_and_pay(driver: uc.Chrome, upi_username: str, upi_handle: str, timeout: int = UPI_PAYMENT_TIMEOUT) -> bool:
    """
    Enters the UPI username and handle into their respective fields and
    clicks the 'MAKE PAYMENT' button.

    Args:
        driver: The initialized WebDriver instance.
        upi_username: The part of the UPI ID before the '@'.
        upi_handle: The part of the UPI ID after the '@'.
        timeout: Maximum time to wait for elements.

    Returns:
        True if details entered and payment button clicked, False otherwise.
    """
    print("\n--- Entering UPI Details and Making Payment ---")
    upi_username_locator = (By.ID, "txtUPIId")
    upi_handle_locator = (By.ID, "dUPIVPADrop")
    # More specific locator for the payment button
    make_payment_button_locator = (By.XPATH, "//button[contains(@onclick, \"pay.fnPayUPI('UPI')\") and contains(normalize-space(), 'MAKE PAYMENT')]")
    # Fallback locator if the above fails (less specific)
    # make_payment_button_locator_fallback = (By.XPATH, "//button[@data-role='PayNowButton']")

    try:
        wait = WebDriverWait(driver, timeout)

        # --- Enter UPI Username ---
        print(f"Waiting for UPI username input (ID: {upi_username_locator[1]})...")
        username_input = wait.until(EC.visibility_of_element_located(upi_username_locator))
        print("Found UPI username input. Clearing and entering...")
        username_input.clear()
        time.sleep(0.2)
        username_input.send_keys(upi_username)
        print(f"Entered UPI username: {upi_username}")
        time.sleep(0.3)

        # --- Enter UPI Handle ---
        print(f"Waiting for UPI handle input (ID: {upi_handle_locator[1]})...")
        handle_input = wait.until(EC.visibility_of_element_located(upi_handle_locator))
        print("Found UPI handle input. Clearing and entering...")
        handle_input.clear()
        time.sleep(0.2)
        handle_input.send_keys(upi_handle)
        print(f"Entered UPI handle: {upi_handle}")
        time.sleep(0.5) # Pause after filling fields

        # --- Click Make Payment Button ---
        print("Waiting for 'MAKE PAYMENT' button to be clickable...")
        try:
            pay_button = wait.until(EC.element_to_be_clickable(make_payment_button_locator))
        except TimeoutException:
            print("Primary locator timed out. Trying fallback locator for 'MAKE PAYMENT' button...")
            # Uncomment fallback if needed, but primary is preferred
            # pay_button = wait.until(EC.element_to_be_clickable(make_payment_button_locator_fallback))
            # If fallback is also used and fails, the outer try/except will catch it.
            # For now, let's assume the primary locator is correct and let it fail if not found.
            raise # Re-raise the TimeoutException if primary locator fails


        print("Found 'MAKE PAYMENT' button. Clicking...")
        # Standard click should be fine for a <button>
        pay_button.click()
        # driver.execute_script("arguments[0].click();", pay_button) # JS click as fallback
        print("Clicked 'MAKE PAYMENT' button.")
        return True

    except TimeoutException:
        print(f"\n--- ERROR: Timed out waiting for UPI input fields or 'MAKE PAYMENT' button within {timeout}s. ---")
        # driver.save_screenshot("screenshot_upi_pay_timeout.png")
        return False
    except NoSuchElementException:
        print(f"\n--- ERROR: Could not find UPI input fields or 'MAKE PAYMENT' button. Check IDs/XPath. ---")
        return False
    except Exception as e:
        print(f"\n--- Error entering UPI details or clicking Make Payment: {e} ---")
        import traceback; traceback.print_exc()
        return False

def close_driver(driver: uc.Chrome | None):
    """Safely quits the WebDriver instance."""
    if driver:
        print("\nClosing the browser...")
        try: driver.quit()
        except Exception as e: print(f"Error closing driver: {e}")
        finally: print("Browser closed.") # Print even if quit fails

# --- Main Execution ---

def main():
    """Main function to orchestrate the script execution."""
    driver = None
    try:
        # --- Get Initial User Input ---
        print("--- BookMyShow Bot ---")
        location_slug = input("Enter location slug: ").lower().strip()
        movie_code = input("Enter movie code: ").strip()
        date_input_str = input(f"Enter date (MMM DD, e.g., {datetime.now().strftime('%b %d').upper()}): ").strip().upper()
        theatre_name = input("Enter EXACT theatre name: ").strip()
        start_time_str = input("Enter EARLIEST showtime (HH:MM AM/PM or HH:MM): ").strip()
        end_time_str = input("Enter LATEST showtime (HH:MM AM/PM or HH:MM): ").strip()
        num_seats_str = input("Enter number of seats (1-10): ").strip()
        phone_number = input("Enter your 10-digit mobile number: ").strip()
        upi_username = input("Enter your UPI username (the part before '@'): ").strip()
        upi_handle = input("Enter your UPI handle (the part after '@', e.g., okhdfcbank, ybl, axl): ").strip()



        # --- Basic Input Validation ---
        if not all([location_slug, movie_code, date_input_str, theatre_name, start_time_str, end_time_str, num_seats_str, phone_number, upi_username, upi_handle]): # Check new inputs
            print("All inputs are required. Exiting.")
            return
        try: # Validate date
            parts = date_input_str.split(); month_map = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
            if len(parts) != 2 or parts[0] not in month_map or not 1 <= int(parts[1]) <= 31: raise ValueError("Invalid Date")
        except Exception as e: print(f"Invalid date format: '{date_input_str}'. Use 'MMM DD'. ({e})"); return
        if parse_time_string(start_time_str) is None or parse_time_string(end_time_str) is None: print("Invalid time format."); return # Validate time
        try: # Validate num_seats
            num_seats = int(num_seats_str)
            if not 1 <= num_seats <= 10: raise ValueError("Seats must be between 1 and 10")
        except ValueError as e: print(f"Invalid number of seats: '{num_seats_str}'. {e}. Exiting."); return
        if not re.fullmatch(r"\d{10}", phone_number):
             print(f"Invalid phone number format: '{phone_number}'. Please enter exactly 10 digits. Exiting.")
             return
        if not re.fullmatch(r"[a-zA-Z0-9.\-_]+", upi_username):
                          print(f"Invalid UPI username format: '{upi_username}'. Contains invalid characters. Exiting.")
                          return
        if not re.fullmatch(r"[a-zA-Z0-9.\-_]+", upi_handle):
                          print(f"Invalid UPI handle format: '{upi_handle}'. Contains invalid characters. Exiting.")
                          return
        if '@' in upi_username or '@' in upi_handle:
                          print("Please enter username and handle separately, without the '@'. Exiting.")
                          return

        # Construct full UPI ID for potential later use/logging if needed
        full_upi_id = f"{upi_username}@{upi_handle}"
        print(f"Using UPI ID: {full_upi_id}") # Optional: Confirm constructed ID

        # --- Setup Driver ---
        driver = setup_driver(PROFILE_FOLDER_NAME, CHROMIUM_BINARY_PATH)
        if not driver: return

        # --- Navigate & Check Initial Load ---
        if not navigate_to_movie(driver, location_slug, movie_code):
             # Handle navigation errors (like 403, 404, Cloudflare)
             print("Exiting due to navigation/initial page load failure.")
             return # Exit if navigation itself failed

        # --- Wait for and Click Book Tickets (with Refresh Loop) ---
        print("\n--- Checking for Booking Availability ---")
        booking_started = False
        while not booking_started:
            # Check for the button and attempt click if found
            button_status = click_book_tickets(driver) # Uses BOOK_BUTTON_CHECK_TIMEOUT

            if button_status is True:
                # Button found and clicked successfully
                print("Booking is open! Proceeding...")
                booking_started = True # Set flag to exit loop
                print("Pausing after clicking 'Book Tickets'...")
                time.sleep(4) # Pause after successful click before next step
                # No 'break' needed, loop condition handles exit

            elif button_status is None:
                # Button not found within timeout (likely upcoming)
                wait_minutes = REFRESH_INTERVAL_SECONDS / 60
                print(f"Booking not yet open. Refreshing page in {wait_minutes:.1f} minutes...")
                time.sleep(REFRESH_INTERVAL_SECONDS)
                print("Refreshing page now...")
                try:
                    driver.refresh()
                    print("Page refreshed. Re-checking for 'Book tickets' button...")
                    time.sleep(5) # Wait for page to reload after refresh
                    # Check if refresh resulted in a block page
                    page_title = driver.title.lower()
                    current_url_lower = driver.current_url.lower()
                    if "challenge" in current_url_lower or "cloudflare" in page_title or "just a moment" in page_title or "403 forbidden" in page_title:
                         print("\n*** WARNING: Block page detected after refresh! Cannot continue monitoring. ***")
                         return # Exit if blocked after refresh
                except Exception as refresh_err:
                     print(f"\n--- Error during page refresh: {refresh_err}. Stopping monitoring. ---")
                     return # Exit if refresh fails
                # Loop continues to check button again

            elif button_status is False:
                # An unexpected error occurred (not Timeout) while checking/clicking
                print("An unexpected error occurred while trying to find/click the 'Book tickets' button. Exiting.")
                return # Exit the script

            # End of while loop iteration

        # --- Select Date --- (Executes only after booking_started is True)
        if not select_show_date(driver, date_input_str): return
        print("Pausing after date selection...")
        time.sleep(3)

        # --- Select Theatre and Time ---
        if not select_theatre_and_time(driver, theatre_name, start_time_str, end_time_str): return
        print("Pausing after selecting showtime...")
        time.sleep(5)

        # --- Select Seat Quantity ---
        if not select_seat_quantity(driver, num_seats):
             return # Exit if quantity selection failed
        print("Pausing after selecting quantity...")
        time.sleep(5)

        # --- Select Seats and Initiate Payment ---
        if not select_seats_and_pay(driver, num_seats):
             return # Exit if seat selection or initial pay click failed
        print("Pausing after clicking initial 'Pay' button...")
        time.sleep(4)

        # --- Accept Terms & Conditions ---
        if not accept_terms_and_conditions(driver):
            return # Exit if T&C accept fails
        print("Pausing after accepting T&C...")
        time.sleep(5)

        # --- Proceed on Booking Summary ---
        if not proceed_on_summary(driver):
            return # Exit if summary proceed fails
        print("Pausing after clicking 'Proceed' on summary...")
        time.sleep(6)

        # --- Enter Contact Details ---
        if not enter_contact_details(driver, phone_number, timeout=CONTACT_DETAILS_TIMEOUT):
            return # Exit if contact details fail
        print("Pausing after entering contact details...")
        time.sleep(4)

        # --- Select PhonePe UPI ---
        if not select_phonepe_upi(driver, timeout=PAYMENT_OPTION_TIMEOUT):
            return # Exit if PhonePe selection fails
        print("Pausing after selecting PhonePe UPI...")
        time.sleep(4)

        # --- Enter UPI Details and Pay ---
        if not enter_upi_details_and_pay(driver, upi_username, upi_handle, timeout=UPI_PAYMENT_TIMEOUT):
             return # Exit if UPI entry or final payment click fails
        print("Pausing after clicking final 'MAKE PAYMENT' button...")
        time.sleep(5)

        # --- Final Success Message ---
        print("\n--- Success! Payment initiated via UPI. ---")
        print("The script has completed its automated steps.")
        print("Check your PhonePe app to approve the payment request.")
        print("Keeping browser open for observation...")
        time.sleep(45) # Keep open longer to observe post-payment status

    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    except Exception as e:
        print(f"\n--- An unexpected error occurred in the main execution flow: {e} ---")
        import traceback
        traceback.print_exc()
    finally:
        # --- Cleanup ---
        close_driver(driver) # Consider adding an option to keep browser open on error


# Make sure the script ends with this check
if __name__ == "__main__":
    main()
