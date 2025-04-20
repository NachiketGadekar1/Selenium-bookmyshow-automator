# Selenium BookMyShow Automator

## Description

This Python script automates the process of booking movie tickets on BookMyShow. It navigates the website, waits for bookings to open (for upcoming movies), selects the desired date, theatre, showtime, number of seats, preferred seats (based on availability), enters contact details, and initiates payment via UPI (requires manual approval).

**Disclaimer:** This script is for educational purposes only. Automating website interactions may be against the Terms of Service of BookMyShow. Use responsibly and at your own risk. Website changes can break the script's functionality.

## Features

* **Upcoming Movie Monitoring:** Waits for the "Book Tickets" button to appear for upcoming movies, refreshing the page at regular intervals.
* **Date Selection:** Selects the specified show date.
* **Theatre & Time Selection:** Finds the specified theatre and selects the first available showtime within a given time range.
* **Seat Quantity:** Selects the required number of seats.
* **Seat Selection:** Attempts to find and select the required number of consecutive available seats.
* **Contact Details:** Automatically enters the provided mobile number.
* **UPI Payment Initiation:** Selects PhonePe UPI and enters the provided UPI details to initiate the payment request (requires manual approval on the PhonePe app).
* **Persistent Profile:** Uses `undetected-chromedriver` with a persistent Chrome/Chromium user profile to potentially stay logged in and reduce bot detection issues.
* **Configurable Timeouts & Intervals:** Allows adjusting wait times and the refresh interval for upcoming movies.

## Prerequisites

* **Python 3.x:** Download from [python.org](https://www.python.org/)
* **Google Chrome or Chromium:** The script uses `undetected-chromedriver`. Ensure you have a compatible browser installed.
* **PIP:** Python package installer (usually comes with Python).

## Setup & Installation

1.  **Clone the Repository (Optional):**
    ```bash
    git clone <your-repository-url>
    cd <your-project-directory>
    ```
2.  **Install Dependencies:**
    Make sure you have your `requirements.txt` file in the project directory. Then run:
    ```bash
    pip install -r requirements.txt
    ```
    *(This assumes your `requirements.txt` includes `undetected-chromedriver`, `selenium`, etc.)*

3.  **Browser & WebDriver:**
    * `undetected-chromedriver` attempts to automatically download the correct ChromeDriver version matching your installed Chrome/Chromium browser.
    * **Important:** If auto-detection fails, or if you use Chromium on Linux, you might need to specify the browser's binary path.

4.  **Persistent Profile:**
    * The script creates a folder (default: `bms_chrome_profile`) in the same directory as the script to store browser profile data (cookies, sessions, etc.).
    * On the first run, you might need to log in to BookMyShow manually within the browser window opened by the script. Subsequent runs should use the saved profile data.

## Configuration

Open the Python script (`open_bms.py`) and adjust the following constants near the top if needed:

* `CHROMIUM_BINARY_PATH`: Set the full path to your Chrome/Chromium executable if `undetected-chromedriver` cannot find it automatically (e.g., `/usr/bin/chromium-browser` on some Linux systems). Set to `None` to rely on auto-detection.
* `PROFILE_FOLDER_NAME`: Change the name of the folder used for the persistent browser profile.
* `DEFAULT_TIMEOUT`, `DATE_SELECTION_TIMEOUT`, etc.: Adjust the wait times (in seconds) for various elements if the script fails due to elements not loading fast enough.
* `REFRESH_INTERVAL_SECONDS`: Time (in seconds) between page refreshes when monitoring an upcoming movie (default is 300 seconds / 5 minutes).
* `BOOK_BUTTON_CHECK_TIMEOUT`: Specific timeout (in seconds) used when checking if the "Book Tickets" button exists.

## Usage

1.  Navigate to your project directory in the terminal.
2.  Run the script using:
    ```bash
    python your_script_name.py
    ```
3.  The script will prompt you to enter the following details:
    * **Location Slug:** The part of the BookMyShow URL specific to your city (e.g., `mumbai`, `bangalore`).
    * **Movie Code:** The unique code for the movie found in its BookMyShow URL (e.g., `ET00308787`).
    * **Date:** The desired date in `MMM DD` format (e.g., `APR 20`).
    * **Theatre Name:** The *exact* name of the theatre as listed on BookMyShow.
    * **Earliest Showtime:** The start of your desired time window (e.g., `6:00 PM`, `18:00`).
    * **Latest Showtime:** The end of your desired time window (e.g., `8:30 PM`, `20:30`).
    * **Number of Seats:** How many seats to book (1-10).
    * **Mobile Number:** Your 10-digit phone number.
    * **UPI Username:** The part of your UPI ID *before* the `@`.
    * **UPI Handle:** The part of your UPI ID *after* the `@` (e.g., `okhdfcbank`, `ybl`, `axl`).

4.  The script will open a browser window and perform the automated steps. Observe the terminal output for progress and potential errors.
5.  If payment is initiated via UPI, you will need to **manually approve the transaction** in your UPI app (PhonePe in this case).

## Workflow

1.  Sets up `undetected-chromedriver` with a persistent profile.
2.  Navigates to the specific movie page.
3.  **Checks for "Book Tickets" button:**
    * If found, clicks it and proceeds.
    * If not found, enters a loop: waits (`REFRESH_INTERVAL_SECONDS`), refreshes the page, and checks again until the button appears.
4.  Selects the specified date.
5.  Scrolls and finds the target theatre.
6.  Finds and clicks the first showtime within the specified time range for that theatre.
7.  Selects the required number of seats from the quantity pop-up.
8.  Attempts to select the required number of available seats on the layout page.
9.  Clicks the initial "Pay" button.
10. Accepts the Terms & Conditions.
11. Clicks "Proceed" on the booking summary page.
12. Enters the provided mobile number and clicks "Continue".
13. Selects PhonePe UPI as the payment method.
14. Enters the UPI username and handle.
15. Clicks the final "MAKE PAYMENT" button.
16. Waits for manual UPI approval.

## Important Notes & Limitations

* **Website Structure Dependent:** BookMyShow frequently updates its website structure. Changes to element IDs, classes, or layouts **will break** this script. Locators (XPaths, IDs) may need frequent updates.
* **Bot Detection:** While `undetected-chromedriver` helps, BookMyShow employs anti-bot measures (like Cloudflare challenges or internal checks). The script might still be detected and blocked, requiring manual intervention or failing altogether.
* **Error Handling:** The script includes basic error handling, but edge cases or unexpected page states might cause failures.
* **UPI Payment:** The script only *initiates* the UPI payment. **You must manually approve the payment request in your UPI app.**
* **Ethical Use:** Use this script responsibly and ethically. Do not use it for scalping or activities that violate BookMyShow's Terms of Service.

## License

MIT License
