import time
import os
import json
import asyncio
import websockets
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import cv2
import numpy as np
import easyocr
from PIL import Image
import io
import base64
import requests
import uuid
import torch
import threading

class NepseScraper:
    def __init__(self, broker_number):
        self.broker_number = broker_number
        self.base_url = f"https://tms{broker_number}.nepsetms.com.np"
        self.login_url = f"{self.base_url}/login"
        self.order_entry_url = f"{self.base_url}/tms/me/memberclientorderentry"
        self.max_retries = 20
        self.retry_delay = 3
        self.setup_driver()
        
        # Create directories for saving images
        os.makedirs("captchas/original", exist_ok=True)
        os.makedirs("captchas/processed", exist_ok=True)
        
        # Enhanced OCR settings
        print("Initializing EasyOCR with enhanced settings...")
        self.reader = easyocr.Reader(
            ['en'],
            gpu=True if torch.cuda.is_available() else False,  # Use GPU if available
            model_storage_directory='./models',
            download_enabled=True,
            recog_network='english_g2'  # Use more accurate model
        )
        
        # For trigger price functionality
        self.is_logged_in = False
        self.order_placed = False
        self.trigger_monitor_running = False
        self.submit_button = None

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def preprocess_captcha_image(self, image_path):
        try:
            # Read image
            image = cv2.imread(image_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Increase image size (upscale) - making it larger for better recognition
            height, width = gray.shape
            upscaled = cv2.resize(gray, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
            
            # Apply multiple preprocessing techniques
            # 1. Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(upscaled, (3, 3), 0)
            
            # 2. Apply adaptive thresholding with different parameters
            binary1 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            binary2 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 5)
            
            # 3. Combine both thresholded images
            combined = cv2.bitwise_and(binary1, binary2)
            
            # 4. Denoise
            denoised = cv2.fastNlMeansDenoising(combined)
            
            # 5. Dilate to make characters thicker
            kernel = np.ones((2,2), np.uint8)
            dilated = cv2.dilate(denoised, kernel, iterations=1)
            
            # 6. Ensure black text on white background
            if np.mean(dilated) < 127:
                dilated = cv2.bitwise_not(dilated)
            
            # 7. Add padding around the image
            padded = cv2.copyMakeBorder(dilated, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255,255,255])
            
            return padded
            
        except Exception as e:
            print(f"Error in preprocessing: {str(e)}")
            return None

    def save_captcha_image(self):
        try:
            print("Locating captcha image...")
            captcha_img = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.form-control.captcha-image-dimension"))
            )
            
            # Get the image source
            img_src = captcha_img.get_attribute('src')
            
            if img_src.startswith('blob:'):
                print("Captcha is a blob URL, taking screenshot...")
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", captcha_img)
                time.sleep(0.5)
                
                # Get element location and size
                location = captcha_img.location_once_scrolled_into_view
                size = captcha_img.size
                
                # Take screenshot
                self.driver.save_screenshot("temp_screenshot.png")
                
                # Get device pixel ratio
                pixel_ratio = self.driver.execute_script('return window.devicePixelRatio;')
                
                # Calculate coordinates
                x = int(location['x'] * pixel_ratio)
                y = int(location['y'] * pixel_ratio)
                width = int(size['width'] * pixel_ratio)
                height = int(size['height'] * pixel_ratio)
                
                # Crop image
                full_img = cv2.imread("temp_screenshot.png")
                captcha = full_img[y:y+height, x:x+width]
                
                # Generate unique filename
                filename = f"captchas/original/captcha_{str(uuid.uuid4())[:8]}.png"
                cv2.imwrite(filename, captcha)
                
                # Clean up
                if os.path.exists("temp_screenshot.png"):
                    os.remove("temp_screenshot.png")
                
                return filename
                
            elif img_src.startswith('data:image'):
                print("Captcha is base64 encoded, decoding...")
                img_data = base64.b64decode(img_src.split(',')[1])
                filename = f"captchas/original/captcha_{str(uuid.uuid4())[:8]}.png"
                
                with open(filename, 'wb') as f:
                    f.write(img_data)
                return filename
                
            else:
                print("Captcha is a direct URL, downloading...")
                response = requests.get(img_src)
                filename = f"captchas/original/captcha_{str(uuid.uuid4())[:8]}.png"
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return filename
                
        except Exception as e:
            print(f"Error saving captcha: {str(e)}")
            return None

    def post_process_captcha(self, text):
        """Clean up common OCR mistakes"""
        common_mistakes = {
            'o': '0',
            'i': '1',
            'l': '1',
            'z': '2',
            's': '5',
            'b': '6',
            'g': '9',
            'q': '9',
            '2':'z',
            '1': 'l',
            'z':'2',
            '9':'g',
            '7':'z'
        }
        
        # Only replace if the character is in a position where we expect a number
        result = list(text)
        for i, char in enumerate(result):
            if char in common_mistakes and (i == 0 or result[i-1].isdigit()):
                result[i] = common_mistakes[char]
        
        return ''.join(result)

    def get_captcha_text(self):
        try:
            # Save the captcha image
            original_image_path = self.save_captcha_image()
            if not original_image_path:
                raise Exception("Failed to save captcha image")
            
            print(f"Saved original captcha to: {original_image_path}")
            
            # Preprocess the image
            processed = self.preprocess_captcha_image(original_image_path)
            if processed is None:
                raise Exception("Failed to preprocess image")
            
            # Save processed version
            processed_path = original_image_path.replace('original', 'processed')
            cv2.imwrite(processed_path, processed)
            
            print(f"Saved processed image to: {processed_path}")
            
            # Try multiple OCR approaches with different parameters
            results = []
            
            # 1. Try with default settings
            results.append(self.reader.readtext(
                original_image_path,
                allowlist='abcdefghijklmnopqrstuvwxyz0123456789',
                batch_size=1,
                detail=0
            ))
            
            # 2. Try with processed image
            results.append(self.reader.readtext(
                processed_path,
                allowlist='abcdefghijklmnopqrstuvwxyz0123456789',
                batch_size=1,
                detail=0
            ))
            
            # 3. Try with different contrast settings
            results.append(self.reader.readtext(
                processed_path,
                allowlist='abcdefghijklmnopqrstuvwxyz0123456789',
                contrast_ths=0.5,
                adjust_contrast=0.5,
                batch_size=1,
                detail=0
            ))
            
            # 4. Try with different paragraph settings
            results.append(self.reader.readtext(
                processed_path,
                allowlist='abcdefghijklmnopqrstuvwxyz0123456789',
                paragraph=True,
                batch_size=1,
                detail=0
            ))
            
            print("All OCR results:", results)
            
            # Process all results
            all_texts = []
            for result in results:
                if result:
                    text = ''.join(result).lower().strip()
                    if text:
                        all_texts.append(text)
            
            print("Processed texts:", all_texts)
            
            if not all_texts:
                raise Exception("No text detected in captcha")
            
            # Select the best result based on length and character composition
            def score_text(text):
                # Prefer longer texts
                length_score = len(text)
                # Prefer texts with a mix of letters and numbers
                has_letters = any(c.isalpha() for c in text)
                has_numbers = any(c.isdigit() for c in text)
                mix_score = 2 if (has_letters and has_numbers) else 1
                return length_score * mix_score
            
            best_text = max(all_texts, key=score_text)
            best_text = self.post_process_captcha(best_text)
            print(f"Final captcha text after post-processing: {best_text}")
            return best_text
            
        except Exception as e:
            print(f"Error getting captcha text: {str(e)}")
            return None

    def click_login_button(self):
        """Helper method to try different ways of clicking the login button"""
        selectors = [
            "input.btn.btn-primary.float-sm-right",
            "input[type='submit'][value='Login']",
            "input[value='Login']",
            "button.btn-primary",
            "//input[@value='Login']",
            "//button[contains(text(), 'Login')]"
        ]
        
        for selector in selectors:
            try:
                print(f"Trying selector: {selector}")
                if selector.startswith("//"):
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(0.5)
                
                try:
                    self.driver.execute_script("arguments[0].click();", button)
                    print("Clicked using JavaScript")
                    return True
                except:
                    try:
                        ActionChains(self.driver).move_to_element(button).click().perform()
                        print("Clicked using ActionChains")
                        return True
                    except:
                        try:
                            button.click()
                            print("Clicked using regular click")
                            return True
                        except:
                            continue
            except Exception as e:
                print(f"Selector {selector} failed: {str(e)}")
                continue
        
        return False

    def login(self, username, password):
        """Log in to the system"""
        try:
            print("Navigating to login page...")
            self.driver.get(self.login_url)
            time.sleep(3)
            
            print(f"Filling username: {username}")
            username_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Client Code/ User Name']"))
            )
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(1)
            
            print("Filling password...")
            password_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Password']"))
            )
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)

            print("\nGetting captcha text...")
            captcha_text = self.get_captcha_text()
            if not captcha_text:
                raise Exception("Failed to get captcha text")

            print(f"Filling captcha: {captcha_text}")
            captcha_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Enter Captcha']"))
            )
            captcha_field.clear()
            time.sleep(0.5)
            captcha_field.send_keys(captcha_text)
            time.sleep(1)
            
            print("Attempting to click login button...")
            if not self.click_login_button():
                try:
                    print("Attempting to submit form directly...")
                    form = self.driver.find_element(By.CSS_SELECTOR, "form.login_form")
                    self.driver.execute_script("arguments[0].submit();", form)
                except Exception as e:
                    print(f"Form submission failed: {str(e)}")
                    try:
                        print("Attempting to submit via Enter key...")
                        captcha_field.send_keys(Keys.RETURN)
                    except:
                        raise Exception("All submission methods failed")

            print("Waiting for login response...")
            time.sleep(3)
            
            current_url = self.driver.current_url
            if "/login" not in current_url:
                print("Login successful!")
                self.is_logged_in = True
                return True
            else:
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error-message, .alert, .text-danger")
                    if error_elements:
                        print("Login failed. Error messages found:")
                        for error in error_elements:
                            error_text = error.text
                            print(f"Error: {error_text}")
                            if "session limit" in error_text.lower() or "active session" in error_text.lower():
                                print("Session limit error detected! Waiting to retry...")
                                time.sleep(10)  # Wait longer before retries for this specific error
                    else:
                        print("Login failed but no error message found")
                except:
                    print("Could not check for error messages")
                return False

        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False

    def logout(self):
        """Properly log out of the trading system"""
        try:
            print("Logging out...")
            # Navigate to logout URL if it exists
            try:
                # Try clicking logout button if available
                logout_btn = self.driver.find_element(By.CSS_SELECTOR, "a.logout, button.logout, a[href*='logout'], .user-dropdown")
                self.driver.execute_script("arguments[0].click();", logout_btn)
                time.sleep(1)
                
                # If clicking the dropdown, look for logout option
                try:
                    logout_option = self.driver.find_element(By.CSS_SELECTOR, "a[href*='logout'], .logout-option")
                    self.driver.execute_script("arguments[0].click();", logout_option)
                except:
                    pass
            except:
                # Try direct logout URL as fallback
                self.driver.get(f"{self.base_url}/logout")
            
            time.sleep(2)
            print("Logout successful")
            self.is_logged_in = False
            return True
        except Exception as e:
            print(f"Error during logout: {str(e)}")
            return False

    def login_with_retries(self, username, password):
        """Login with multiple retries"""
        attempt = 1
        while attempt <= self.max_retries:
            print(f"\n{'='*50}")
            print(f"Login attempt {attempt} of {self.max_retries}")
            print(f"{'='*50}")
            
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
                print(f"Error during login attempt {attempt}: {str(e)}")
                if attempt < self.max_retries:
                    print("Retrying...")
                    time.sleep(self.retry_delay)
                    self.driver.refresh()
            
            attempt += 1
            
        print(f"Failed to login after {self.max_retries} attempts")
        return False

    def prepare_order_form(self, action, symbol, quantity, price, trigger_price):
        """Prepare the order form with the given details but skip price entry until trigger condition is met"""
        try:
            # Store these values for later use
            self.action = action
            self.symbol = symbol
            self.quantity = quantity
            self.price = price
            self.trigger_price = trigger_price
            
            print("Navigating to order entry page...")
            self.driver.get(self.order_entry_url)
            time.sleep(3)  # Wait for page to load
            
            # Set buy/sell option based on user selection
            if action == "buy":
                print("Setting action to BUY")
                buy_element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label.xtoggler-btn-wrapper:nth-of-type(3)")))
                self.driver.execute_script("arguments[0].click();", buy_element)
            else:
                print("Setting action to SELL")
                sell_element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label.xtoggler-btn-wrapper:first-of-type")))
                self.driver.execute_script("arguments[0].click();", sell_element)
            
            # Enter stock symbol
            print(f"Entering symbol: {symbol}")
            symbol_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.order__form--name input")))
            symbol_field.clear()
            symbol_field.send_keys(symbol)
            time.sleep(1)
            
            # Enter quantity
            print(f"Entering quantity: {quantity}")
            qty_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.order__form--qty input")))
            qty_field.clear()
            qty_field.send_keys(quantity)
            time.sleep(1)
            
            # We'll skip entering price until trigger condition is met
            print(f"Price ({price}) will be entered when trigger price is reached")
            
            # Locate and cache the price field for later use
            self.price_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.order__form--price input")))
            
            # Locate submit button so we have it cached for later
            print("Locating the submit button...")
            try:
                self.submit_button = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn.btn-sm.btn-primary"))
                )
                print("Submit button found - will click when trigger condition is met")
            except Exception as e:
                print(f"Error finding submit button: {str(e)}")
                self.driver.save_screenshot("button_error.png")
                return False
                
            # Take screenshot for verification
            self.driver.save_screenshot("order_form_ready.png")
            print("Order form prepared - waiting for trigger price match before entering price and submitting")
            return True
                
        except Exception as e:
            print(f"Error during order preparation: {str(e)}")
            return False
                
    def place_order_fast(self):
        try:
            start_time = time.time()
            
            # Get the current LTP
            current_ltp = self.get_ltp_from_ui()
            if current_ltp is None:
                print("Error: Could not get current LTP")
                return False
                
            # Calculate price as LTP + 2% with 1 decimal floor
            import math
            calculated_price = current_ltp * 1.02
            calculated_price = math.floor(calculated_price * 10) / 10  # Floor to 1 decimal place
            print(f"Setting price to LTP + 2%: {current_ltp} + 2% = {calculated_price}")
            
            # Direct JavaScript value setting (faster than clear+sendKeys)
            self.driver.execute_script("""
                // Set value directly (sub-millisecond operation)
                arguments[0].value = arguments[1];
                
                // Force input event to ensure validation triggers
                var event = new Event('input', { bubbles: true });
                arguments[0].dispatchEvent(event);
            """, self.price_field, calculated_price)
            
            # Execute button click with lowest possible latency
            self.driver.execute_script("""
                // Bypass browser's click event chain for maximum speed
                var button = arguments[0];
                
                // Create and dispatch native events (faster than .click())
                ['mousedown', 'mouseup', 'click'].forEach(function(eventType) {
                    var clickEvent = new MouseEvent(eventType, {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    button.dispatchEvent(clickEvent);
                });
                
                // Immediately handle confirmation dialog if appears
                setTimeout(function() {
                    var confirmBtns = document.querySelectorAll('.confirm-button, .modal button.btn-primary');
                    if (confirmBtns.length > 0) confirmBtns[0].dispatchEvent(new MouseEvent('click'));
                }, 5); // Ultra-short timeout
            """, self.submit_button)
            
            execution_time = (time.time() - start_time) * 1000
            print(f"⚡️ Order executed in {execution_time:.2f}ms!")
            self.order_placed = True
            return True
        except Exception as e:
            print(f"Error in fast execution: {str(e)}")
            return False

    def get_ltp_from_ui(self):
        """Ultra-optimized LTP extraction using cached DOM access"""
        try:
            # Optimized JavaScript that caches DOM element between calls
            ltp_value = self.driver.execute_script("""
                // Cache DOM lookups between calls
                if (!window._cachedLtpElement) {
                    // Try direct ID access first (fastest)
                    window._cachedLtpElement = document.getElementById('ltp-value');
                    
                    // Fallback to searching labels if ID not found
                    if (!window._cachedLtpElement) {
                        var labels = document.querySelectorAll('label[class*="order__form--label"]');
                        for (var i = 0; i < labels.length; i++) {
                            if (labels[i].textContent.includes('LTP')) {
                                window._cachedLtpElement = labels[i].parentElement;
                                break;
                            }
                        }
                        
                        // Last resort - check dedicated price containers
                        if (!window._cachedLtpElement) {
                            window._cachedLtpElement = document.querySelector('.price-value, .ltp, [data-field="lastPrice"]');
                        }
                    }
                }
                
                // Fast extraction from cached element
                if (window._cachedLtpElement) {
                    var text = window._cachedLtpElement.textContent.trim();
                    var match = text.match(/LTP[^0-9]*([0-9]+\\.?[0-9]*)/);
                    return match ? parseFloat(match[1]) : parseFloat(text);
                }
                
                return null;
            """)
            return ltp_value
        except Exception as e:
            print(f"Error in optimized LTP extraction: {str(e)}")
            return None

    def start_ui_trigger_monitor(self):
        """Zero-latency price monitoring with predictive execution"""
        if self.trigger_monitor_running:
            return
            
        self.trigger_monitor_running = True
        print("⚡ ACTIVATING ZERO-LATENCY MONITORING ⚡")
        import os
        try:
            os.nice(-20)  # Maximum priority on macOS/Unix
        except:
            pass
        
        # Set process priority to high
        try:
            import psutil
            process = psutil.Process()
            process.cpu_affinity([0])
            process.nice(psutil.HIGH_PRIORITY_CLASS)
            print("✅ Process priority set to HIGH for minimal latency")
        except:
            pass  # Optional, continue if priority setting fails
        
        def monitor_thread():
            try:
                # Pre-convert to avoid type conversion during monitoring
                trigger_price_float = float(self.trigger_price)
                
                print(f"🚀 ZERO-LATENCY MONITORING ACTIVE for {self.symbol}")
                print(f"✅ Target: {self.trigger_price}")
                print(f"Price will be entered only at trigger time")
                
                start_time = time.time()
                poll_count = 0
                last_price = None
                
                while not self.order_placed:
                    # Get price with zero overhead
                    current_price = self.get_ltp_from_ui()
                    
                    if current_price is not None:
                        poll_count += 1
                        
                        # Only print when price changes to reduce CPU usage
                        if current_price != last_price:
                            print(f"[{poll_count}] Price: {current_price} | Target: {self.trigger_price}")
                            last_price = current_price
                        
                        # Check trigger condition with optimized comparison
                        if current_price >= trigger_price_float:
                            execution_time = (time.time() - start_time) * 1000
                            print(f"⚡ TRIGGER MET in {execution_time:.2f}ms! {current_price} >= {self.trigger_price}")
                            if not self.order_placed:
                                self.place_order_fast()
                            break
                    
                    # Ultra-short polling interval (0.5ms) for near-realtime monitoring
                    time.sleep(0.0005)
                    
            except Exception as e:
                print(f"Monitor error: {str(e)}")
            finally:
                self.trigger_monitor_running = False
        
        # Start dedicated monitoring thread with max priority
        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()

    async def optimized_websocket_client(self):
        """Optimized WebSocket client for minimal latency price monitoring - triggers when current price >= trigger price"""
        uri = "ws://localhost:8000/ws"
        try:
            async with websockets.connect(uri) as websocket:
                print(f"Ultra-fast price monitoring established for {self.symbol}.")
                print(f"Waiting for current price to reach or exceed trigger price: {self.trigger_price}")
                print("System ready and waiting - DO NOT close this window")
                
                # Pre-convert trigger price to float for faster comparison
                trigger_price_float = float(self.trigger_price)
                
                # For performance monitoring
                poll_count = 0
                start_time = time.time()
                
                while not self.order_placed:
                    # Receive data from the WebSocket server
                    data = await websocket.recv()
                    market_data = json.loads(data)
                    
                    poll_count += 1
                    
                    if market_data.get("type") == "data":
                        # Direct lookup for maximum speed
                        stock_data = market_data.get("data", {}).get(self.symbol)
                        
                        if stock_data:
                            current_price = stock_data.get("last_price")
                            if current_price is not None:
                                current_price_float = float(current_price)
                                
                                # Print price on EVERY check, regardless of whether it changed
                                print(f"Current price: {current_price} | Trigger price: {self.trigger_price}")
                                
                                # Check if current price is greater than or equal to trigger price
                                if current_price_float >= trigger_price_float:
                                    print(f"PRICE TRIGGER CONDITION MET! Current price: {current_price} >= Trigger: {self.trigger_price}")
                                    execution_time = time.time() - start_time
                                    print(f"Trigger condition met after {execution_time:.2f}s of monitoring")
                                    return True
                    
                    # Minimal wait - just enough to not overload CPU
                    await asyncio.sleep(0.01)
                
        except Exception as e:
            print(f"WebSocket error: {str(e)}")
            return False

    def start_optimized_trigger_monitor(self):
        """Start an optimized high-speed trigger price monitor"""
        if self.trigger_monitor_running:
            return
            
        self.trigger_monitor_running = True
        
        def monitor_thread():
            try:
                # Run the asyncio event loop in this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Start optimized WebSocket monitoring
                trigger_met = loop.run_until_complete(self.optimized_websocket_client())
                
                if trigger_met and not self.order_placed:
                    print("💥 TRIGGER PRICE REACHED! EXECUTING ORDER... 💥")
                    self.place_order_fast()
            except Exception as e:
                print(f"Error in price monitor thread: {str(e)}")
            finally:
                self.trigger_monitor_running = False
        
        # Start monitoring in a separate thread
        threading.Thread(target=monitor_thread, daemon=True).start()

    def close(self):
        try:
            if self.is_logged_in:
                self.logout()
        finally:
            self.driver.quit()


if __name__ == "__main__":
    # First ask for broker number and credentials
    print("\n==== Nepse TMS Auto-Trade System ====")
    print("\nPlease provide your broker information:")
    
    broker_number = input("Enter your broker number (e.g., 59): ").strip()
    username = input("Enter your username: ").strip()
    password = input("Enter your password: ").strip()
    
    # Initialize the scraper with the broker number
    scraper = NepseScraper(broker_number)
    
    try:
        print("\nAttempting to log in to your broker's TMS...")
        success = scraper.login_with_retries(username, password)
        
        if success:
            print("\n✅ Login successful! Maintaining session...")
            
            # Now ask for trading details
            print("\n==== Trading Details ====")
            
            action = input("Do you want to buy or sell? (buy/sell): ").strip().lower()
            while action not in ["buy", "sell"]:
                action = input("Invalid choice. Please enter 'buy' or 'sell': ").strip().lower()
            
            symbol = input("Enter stock symbol: ").strip().upper()
            quantity = input("Enter quantity: ").strip()
            # Remove price input - will be calculated at trigger time
            price = "0"  # Placeholder, will be replaced with LTP + 2%
            trigger_price = input("Enter trigger price (required for automated execution): ").strip()
            while not trigger_price:
                trigger_price = input("Trigger price is required. Please enter a valid price: ").strip()
            
            print(f"\nSetting up ultra-fast order execution:")
            print(f"Action: {action.upper()}")
            print(f"Symbol: {symbol}")
            print(f"Quantity: {quantity}")
            print(f"Order price: Will be set to LTP + 2% when triggered")
            print(f"Trigger price: {trigger_price}")
            
            # Prepare the order form
            prepared = scraper.prepare_order_form(action, symbol, quantity, price, trigger_price)
            
            if prepared:
                print("\n✅ System ready for ultra-fast execution!")
                print(f"Waiting for {symbol} price to reach {trigger_price}...")
                print("DO NOT close this window - order will execute automatically when price is reached")
                
                # Start the UI-based trigger price monitor (much faster than WebSocket)
                scraper.start_ui_trigger_monitor()
                
                try:
                    # Keep main thread alive until order is placed
                    while not scraper.order_placed:
                        time.sleep(0.1)
                    
                    print("\n🎉 Order execution complete! 🎉")
                except KeyboardInterrupt:
                    print("\nMonitoring stopped by user. Order not placed.")
            else:
                print("Failed to prepare the order form. Please try again.")
        else:
            print("Login failed. Please check your broker number, username, and password.")
    finally:
        time.sleep(3)  # Give a moment to see final messages
        scraper.close()

        #broker number 21
        #2021026996

        #59
        #2020128057
        #clear

        #SPDL
        #430 - T
        #423p