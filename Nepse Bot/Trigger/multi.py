#!/usr/bin/env python3
import time
import os
import json
import asyncio
import multiprocessing
import signal
import sys
import logging
import random
import subprocess
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Setup logging
logging.basicConfig(
    filename='nepse_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_display():
    """Setup virtual display for headless operation with better error handling"""
    # Clean up any existing display locks to avoid conflicts
    for i in range(99, 110):
        lock_file = f"/tmp/.X{i}-lock"
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print(f"Removed existing display lock: {lock_file}")
            except:
                print(f"Could not remove lock file: {lock_file}")
    
    # Use a random display number to avoid conflicts
    display_num = random.randint(99, 200)
    os.environ['DISPLAY'] = f':{display_num}'
    
    # Start Xvfb with increased error checking
    try:
        cmd = f"Xvfb :{display_num} -screen 0 1920x1080x24 -ac"
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)  # Give it time to start
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"Xvfb failed to start: {stderr.decode()}")
            return False
            
        print(f"Virtual display initialized on :{display_num}")
        return True
    except Exception as e:
        print(f"Error setting up display: {e}")
        return False

class NepseScraper:
    def __init__(self, broker_number):
        self.broker_number = broker_number
        self.base_url = f"https://tms{broker_number}.nepsetms.com.np"
        self.login_url = f"{self.base_url}/login"
        self.order_entry_url = f"{self.base_url}/tms/me/memberclientorderentry"
        self.max_retries = 3
        self.retry_delay = 3
        self.is_logged_in = False
        self.order_placed = False
        self.trigger_monitor_running = False
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Firefox driver with robust error handling"""
        print("Setting up Firefox driver...")
        try:
            # Firefox options
            options = Options()
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.manager.showWhenStarting", False)
            options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")
            
            # Additional settings to make Firefox more stable
            options.set_preference("dom.webnotifications.enabled", False)
            options.set_preference("app.update.enabled", False)
            options.set_preference("browser.tabs.remote.autostart", False)
            options.set_preference("browser.tabs.remote.autostart.2", False)
            
            # Initialize driver with increased timeout
            print("Initializing Firefox driver...")
            self.driver = webdriver.Firefox(options=options)
            self.driver.set_page_load_timeout(60)
            self.wait = WebDriverWait(self.driver, 30)
            print("Firefox driver initialized successfully")
            return True
        except Exception as e:
            print(f"Error initializing Firefox driver: {e}")
            return False
            
    def manual_captcha_entry(self):
        """Save captcha for manual entry"""
        try:
            # Take screenshot of the page
            self.driver.save_screenshot("captcha_page.png")
            print("\n📸 CAPTCHA IMAGE SAVED! Please check captcha_page.png")
            print("Enter the captcha text as shown in the image:")
            captcha_text = input("Captcha: ")
            return captcha_text
        except Exception as e:
            print(f"Error in manual captcha: {e}")
            return None
            
    def login(self, username, password):
        """Login with manual captcha entry"""
        try:
            print(f"Navigating to {self.login_url}...")
            self.driver.get(self.login_url)
            time.sleep(3)
            
            # Take screenshot to verify page loaded
            self.driver.save_screenshot("login_screen.png")
            print("Login screen screenshot saved as login_screen.png")
            
            # Enter username
            print(f"Entering username: {username}")
            username_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Client Code/ User Name']"))
            )
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(1)
            
            # Enter password
            print("Entering password...")
            password_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Password']"))
            )
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)
            
            # Get captcha via manual entry
            print("Getting captcha via manual entry...")
            captcha_text = self.manual_captcha_entry()
            if not captcha_text:
                raise Exception("Failed to get captcha text")
                
            # Enter captcha
            print(f"Entering captcha: {captcha_text}")
            captcha_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Enter Captcha']"))
            )
            captcha_field.clear()
            time.sleep(0.5)
            captcha_field.send_keys(captcha_text)
            time.sleep(1)
            
            # Click login button
            print("Clicking login button...")
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.btn.btn-primary"))
            )
            login_button.click()
            
            # Wait for login result
            print("Waiting for login response...")
            time.sleep(5)
            
            # Save screenshot after login attempt
            self.driver.save_screenshot("after_login.png")
            print("After login screenshot saved as after_login.png")
            
            # Check if login successful
            current_url = self.driver.current_url
            print(f"Current URL: {current_url}")
            
            if "/login" not in current_url:
                print("✅ Login successful!")
                self.is_logged_in = True
                return True
            else:
                print("❌ Login failed.")
                return False
        except Exception as e:
            print(f"Error during login: {e}")
            return False
            
    def login_with_retries(self, username, password):
        """Login with limited retries"""
        attempt = 1
        while attempt <= self.max_retries:
            print(f"\nLogin attempt {attempt} of {self.max_retries}...")
            
            try:
                success = self.login(username, password)
                if success:
                    print(f"Successfully logged in on attempt {attempt}!")
                    return True
                    
                print(f"Login attempt {attempt} failed. Retrying...")
                self.driver.delete_all_cookies()
                self.driver.refresh()
                time.sleep(self.retry_delay)
                
            except Exception as e:
                print(f"Error during login attempt {attempt}: {e}")
                if attempt < self.max_retries:
                    print("Retrying...")
                    time.sleep(self.retry_delay)
                    try:
                        self.driver.refresh()
                    except:
                        pass
            
            attempt += 1
            
        print(f"Failed to login after {self.max_retries} attempts")
        return False

    def prepare_order_form(self, action, symbol, quantity, price, trigger_price):
        """Prepare order form with the given details"""
        try:
            # Store values for later use
            self.action = action
            self.symbol = symbol
            self.quantity = quantity
            self.price = price
            self.trigger_price = trigger_price
            
            # Navigate to order entry page
            print("Navigating to order entry page...")
            self.driver.get(self.order_entry_url)
            time.sleep(3)
            self.driver.save_screenshot("order_page.png")
            
            # Set buy/sell option
            if action == "buy":
                print("Setting action to BUY")
                buy_element = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "label.xtoggler-btn-wrapper:nth-of-type(3)"))
                )
                self.driver.execute_script("arguments[0].click();", buy_element)
            else:
                print("Setting action to SELL")
                sell_element = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "label.xtoggler-btn-wrapper:first-of-type"))
                )
                self.driver.execute_script("arguments[0].click();", sell_element)
                
            # Enter stock symbol
            print(f"Entering symbol: {symbol}")
            symbol_field = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.order__form--name input"))
            )
            symbol_field.clear()
            symbol_field.send_keys(symbol)
            time.sleep(1)
            
            # Enter quantity
            print(f"Entering quantity: {quantity}")
            qty_field = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.order__form--qty input"))
            )
            qty_field.clear()
            qty_field.send_keys(quantity)
            time.sleep(1)
            
            # Locate price field for later use
            self.price_field = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.order__form--price input"))
            )
            
            # Locate submit button for later use
            print("Locating submit button...")
            try:
                self.submit_button = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn.btn-sm.btn-primary"))
                )
                print("Submit button found")
            except Exception as e:
                print(f"Error finding submit button: {e}")
                self.driver.save_screenshot("button_error.png")
                return False
                
            # Take screenshot for verification
            self.driver.save_screenshot("order_form_ready.png")
            print("Order form prepared and ready for trigger monitoring")
            return True
            
        except Exception as e:
            print(f"Error during order preparation: {e}")
            return False
            
    def place_order(self):
        """Place order with the set price"""
        try:
            # Enter price
            print(f"Entering price: {self.price}")
            self.price_field.clear()
            self.price_field.send_keys(self.price)
            time.sleep(0.5)
            
            # Click submit button
            print("Clicking submit button...")
            self.driver.execute_script("arguments[0].click();", self.submit_button)
            
            # Wait for confirmation dialog if it appears
            try:
                confirm_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".confirm-button, .modal button.btn-primary"))
                )
                print("Clicking confirmation dialog...")
                self.driver.execute_script("arguments[0].click();", confirm_button)
            except:
                print("No confirmation dialog appeared")
                
            self.order_placed = True
            print("✅ Order placed successfully!")
            
            # Take screenshot for verification
            self.driver.save_screenshot("order_placed.png")
            print("Screenshot saved as order_placed.png")
            
            return True
            
        except Exception as e:
            print(f"Error placing order: {e}")
            self.driver.save_screenshot("order_error.png")
            return False
            
    def get_ltp_from_ui(self):
        """Get Last Traded Price from UI"""
        try:
            # Try different methods to get the LTP
            try:
                ltp_element = self.driver.find_element(By.XPATH, "//label[contains(text(), 'LTP')]/following-sibling::div")
                ltp_text = ltp_element.text.strip()
                return float(ltp_text)
            except:
                try:
                    ltp_element = self.driver.find_element(By.CSS_SELECTOR, ".ltp, .price-value")
                    ltp_text = ltp_element.text.strip()
                    return float(ltp_text)
                except:
                    # Last resort - use JavaScript
                    ltp_value = self.driver.execute_script("""
                        // Try finding LTP in different ways
                        var labels = document.querySelectorAll('label');
                        for (var i = 0; i < labels.length; i++) {
                            if (labels[i].textContent.includes('LTP')) {
                                var parent = labels[i].parentElement;
                                return parseFloat(parent.textContent.replace('LTP', '').trim());
                            }
                        }
                        return null;
                    """)
                    return ltp_value
        except Exception as e:
            print(f"Error getting LTP: {e}")
            return None
                
    def start_trigger_monitor(self):
        """Start trigger price monitor"""
        if self.trigger_monitor_running:
            return
            
        self.trigger_monitor_running = True
        
        def monitor_thread():
            try:
                print(f"Starting trigger monitor for {self.symbol}")
                print(f"Target trigger price: {self.trigger_price}")
                
                check_interval = 1  # seconds between checks
                trigger_price_float = float(self.trigger_price)
                
                while not self.order_placed:
                    current_price = self.get_ltp_from_ui()
                    
                    if current_price:
                        print(f"Current price: {current_price} | Target: {self.trigger_price}")
                        
                        if current_price >= trigger_price_float:
                            print(f"\n🚨 TRIGGER PRICE REACHED: {current_price} >= {self.trigger_price}")
                            print(f"Placing order at price: {self.price}...")
                            
                            self.place_order()
                            break
                            
                    time.sleep(check_interval)
                    
            except Exception as e:
                print(f"Monitor error: {e}")
            finally:
                self.trigger_monitor_running = False
                
        # Start monitoring in a thread
        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()
        
    def close(self):
        """Close browser and clean up"""
        try:
            if self.is_logged_in:
                print("Logging out...")
                try:
                    self.driver.get(f"{self.base_url}/logout")
                    time.sleep(1)
                except:
                    pass
        except:
            pass
        finally:
            print("Closing browser...")
            try:
                self.driver.quit()
            except:
                pass


def run_scraper(broker_number, username, password, action, symbol, quantity, order_price, trigger_price, trigger_pct, exit_event):
    """Run a single trigger monitor"""
    scraper = None
    try:
        print(f"\n==== Nepse TMS Auto-Trade System - {trigger_pct}% Trigger ====")
        print(f"Watching for trigger price: {trigger_price}")
        print(f"Will place order at price: {order_price} when triggered")
        
        # Initialize the scraper
        scraper = NepseScraper(broker_number)
        
        # Login
        print(f"\nAttempting to log in to broker {broker_number}...")
        success = scraper.login_with_retries(username, password)
        
        if success:
            print(f"\n✅ Login successful for {trigger_pct}% trigger monitor!")
            
            # Prepare order form
            print(f"\nPreparing order form for {action.upper()} {quantity} {symbol}")
            print(f"When price reaches {trigger_price} ({trigger_pct}%), will order at {order_price}")
            
            prepared = scraper.prepare_order_form(action, symbol, quantity, order_price, trigger_price)
            
            if prepared:
                print(f"\n✅ {trigger_pct}% trigger system ready!")
                print(f"Monitoring {symbol} to reach {trigger_price}...")
                
                # Start monitoring
                scraper.start_trigger_monitor()
                
                # Monitor until order placed or exit event set
                while not scraper.order_placed and not exit_event.is_set():
                    time.sleep(0.5)
                    
                if scraper.order_placed:
                    print(f"\n🎉 Order execution successful at {trigger_pct}% trigger!")
                    print(f"Order placed at price: {order_price}")
                
                elif exit_event.is_set():
                    print(f"\nSystem shutdown requested. Closing {trigger_pct}% monitor.")
            else:
                print(f"Failed to prepare order form for {trigger_pct}% trigger")
        else:
            print(f"Login failed for {trigger_pct}% trigger monitor")
    
    except Exception as e:
        print(f"Error in {trigger_pct}% trigger scraper: {e}")
    finally:
        # Always close the scraper to clean up resources
        if scraper is not None:
            try:
                scraper.close()
            except Exception as e:
                print(f"Error closing scraper: {e}")
        print(f"{trigger_pct}% trigger monitor closed")


def calculate_stepping_prices(base_price):
    """Calculate trigger and order prices for stepping strategy"""
    base = float(base_price)
    
    # Define trigger percentages
    trigger_percentages = [2, 4, 6, 8]
    additional_percentage = 2  # Each order is 2% above its trigger price
    
    # Calculate trigger prices - truncate to 1 decimal
    trigger_prices = {}
    for pct in trigger_percentages:
        exact_value = base * (1 + pct/100)
        truncated_value = int(exact_value * 10) / 10  # Truncate to 1 decimal
        trigger_prices[pct] = truncated_value
    
    # Create trigger-order pairs
    pairs = []
    for pct in trigger_percentages:
        trigger_price = trigger_prices[pct]
        exact_order_value = trigger_price * (1 + additional_percentage/100)
        truncated_order_value = int(exact_order_value * 10) / 10  # Truncate to 1 decimal
        order_price = truncated_order_value
        
        pairs.append({
            "trigger_pct": pct,
            "trigger_price": trigger_price,
            "order_price": order_price,
            "order_pct": f"{pct}+{additional_percentage}%"
        })
    
    return pairs


def load_config_from_env():
    """Load configuration from environment variables"""
    try:
        config = {
            "broker_number": os.environ.get("NEPSE_BROKER_NUMBER"),
            "username": os.environ.get("NEPSE_USERNAME"),
            "password": os.environ.get("NEPSE_PASSWORD"),
            "action": os.environ.get("NEPSE_ACTION"),
            "symbol": os.environ.get("NEPSE_SYMBOL"),
            "quantity": os.environ.get("NEPSE_QUANTITY"),
            "base_price": os.environ.get("NEPSE_BASE_PRICE"),
            "auto_confirm": os.environ.get("NEPSE_AUTO_CONFIRM", "false").lower() == "true"
        }
        
        # Check for missing variables
        missing = []
        for key in ["broker_number", "username", "password", "action", "symbol", "quantity", "base_price"]:
            if not config.get(key):
                missing.append(key)
                
        if missing:
            print(f"Missing required environment variables: {', '.join(missing)}")
            print("Please set them before running this script")
            return None
            
        return config
    except Exception as e:
        print(f"Error loading environment config: {e}")
        return None


def load_config_from_file(config_file='config.json'):
    """Load configuration from a JSON file (fallback)"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"Configuration loaded from {config_file}")
        return config
    except Exception as e:
        print(f"Error loading config file: {e}")
        return None


def main():
    # Setup virtual display
    if not setup_display():
        print("Failed to setup virtual display. Exiting.")
        return
    
    # Setup logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f'nepse_bot_{timestamp}.log'
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info(f"Starting Nepse bot, log file: {log_filename}")
    
    # Handle interruptions gracefully
    def signal_handler(sig, frame):
        print("\nCleaning up and exiting...")
        exit_event.set()
        for process in processes:
            if process.is_alive():
                process.join(timeout=5)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load configuration (try env first, then file)
    config = load_config_from_env() or load_config_from_file()
    if not config:
        print("Failed to load configuration. Exiting.")
        return
    
    print("\n==== Nepse TMS Stepping Trigger Trade System ====")
    print("\nThis system uses a stepping strategy:")
    print("1. When price reaches 2% trigger → Places order at 4% price")
    print("2. When price reaches 4% trigger → Places order at 6% price")
    print("3. When price reaches 6% trigger → Places order at 8% price")
    print("4. When price reaches 8% trigger → Places order at 10% price")
    
    # Extract config values
    broker_number = config['broker_number']
    username = config['username']
    password = config['password']
    action = config['action']
    symbol = config['symbol']
    quantity = config['quantity']
    base_price = config['base_price']
    
    # Print configuration summary
    print("\n==== Configuration Summary ====")
    print(f"Broker: {broker_number}")
    print(f"Username: {username}")
    print(f"Action: {action}")
    print(f"Symbol: {symbol}")
    print(f"Quantity: {quantity}")
    print(f"Base price: {base_price}")
    
    # Calculate trigger-order price pairs
    price_pairs = calculate_stepping_prices(base_price)
    
    print("\n==== Trigger and Order Price Summary ====")
    print(f"Base price: {base_price}")
    for pair in price_pairs:
        print(f"When {pair['trigger_pct']}% trigger ({pair['trigger_price']}) is reached → Will order at {pair['order_pct']} price ({pair['order_price']})")
    
    # Confirm before proceeding
    if not config.get('auto_confirm', False):
        confirmation = input("\nDo you want to proceed with these settings? (y/n): ").strip().lower()
        if confirmation != 'y':
            print("Operation cancelled by user.")
            return
    else:
        print("\nAuto-confirm enabled. Proceeding automatically...")
    
    # Create shared event for process coordination
    exit_event = multiprocessing.Event()
    
    # Create and start processes
    processes = []
    
    # Launch all monitors with appropriate delays
    for i, pair in enumerate(price_pairs):
        if not exit_event.is_set():
            print(f"\nLaunching {pair['trigger_pct']}% trigger monitor...")
            p = multiprocessing.Process(
                target=run_scraper,
                args=(broker_number, username, password, action, symbol, quantity, 
                      str(pair['order_price']), str(pair['trigger_price']), pair['trigger_pct'], exit_event)
            )
            processes.append(p)
            p.start()
            
            # Wait before starting next process
            if i < len(price_pairs) - 1:
                time.sleep(10)  # Longer delay to avoid login conflicts
    
    # Wait for all processes to complete
    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print("\nUser interrupted. Shutting down all monitors...")
        exit_event.set()
        for process in processes:
            if process.is_alive():
                process.join(timeout=5)
    
    print("\nAll monitors have completed. Trading session finished.")


if __name__ == "__main__":
    main()