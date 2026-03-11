import time
import os
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

class NepseScraper:
    def __init__(self):
        self.url = "https://tms59.nepsetms.com.np/login"
        self.max_retries = 5
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

    def login(self, username, password, action, symbol, quantity, price):
        try:
            print("Navigating to login page...")
            self.driver.get(self.url)
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
                print("Navigating to order entry page...")
                self.driver.get("https://tms59.nepsetms.com.np/tms/me/memberclientorderentry")
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
                
                # Enter price
                print(f"Entering price: {price}")
                price_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.order__form--price input")))
                price_field.clear()
                price_field.send_keys(price)
                time.sleep(1)
                
                return True
            else:
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error-message, .alert, .text-danger")
                    if error_elements:
                        print("Login failed. Error messages found:")
                        for error in error_elements:
                            print(f"Error: {error.text}")
                    else:
                        print("Login failed but no error message found")
                except:
                    print("Could not check for error messages")
                return False

        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False

    def check_session_expiry(self, refresh_count=1000):
        """Refresh the page multiple times and check if session expires"""
        print(f"\nStarting session expiry check with {refresh_count} refreshes...")
        
        for i in range(1, refresh_count + 1):
            try:
                print(f"Refresh attempt {i}/{refresh_count}")
                self.driver.refresh()
                time.sleep(1)  # Short delay between refreshes
                
                # Check if we're redirected to login page which indicates session expiry
                if "/login" in self.driver.current_url:
                    print(f"SESSION EXPIRED after {i} refreshes!")
                    return i
                    
                # Every 50 refreshes, print a status update
                if i % 50 == 0:
                    print(f"Completed {i} refreshes, session still active")
                    
            except Exception as e:
                print(f"Error during refresh attempt {i}: {str(e)}")
                
        print(f"Session remained active after {refresh_count} refreshes")
        return None

    def login_with_retries(self, username, password, action, symbol, quantity, price):
        """Attempt to login multiple times until successful"""
        attempt = 1
        while attempt <= self.max_retries:
            print(f"\n{'='*50}")
            print(f"Login attempt {attempt} of {self.max_retries}")
            print(f"{'='*50}")
            
            try:
                success = self.login(username, password, action, symbol, quantity, price)
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

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = NepseScraper()
    try:
        # Get user input for buy or sell
        action = input("Do you want to buy or sell? (buy/sell): ").strip().lower()
        while action not in ["buy", "sell"]:
            action = input("Invalid choice. Please enter 'buy' or 'sell': ").strip().lower()
        
        # Get stock symbol from user
        symbol = input("Enter stock symbol: ").strip().upper()
        
        # Get quantity and price
        quantity = input("Enter quantity: ").strip()
        price = input("Enter price: ").strip()
        
        print(f"Selected action: {action}")
        print(f"Selected symbol: {symbol}")
        
        username = "2020128057" 
        password = "Graymatter@123"  
        
        success = scraper.login_with_retries(username, password, action, symbol, quantity, price)
        if success:
            print("Login successful! Now checking session expiry...")
            expiry_count = scraper.check_session_expiry(1000)
            if expiry_count:
                print(f"SESSION EXPIRED after {expiry_count} refreshes")
            else:
                print("Session remained active after 1000 refreshes")
        else:
            print("Failed to complete the login process after all retries")
    finally:
        scraper.close()