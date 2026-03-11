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

class NepseScraper:
    def __init__(self):
        self.url = "https://tms21.nepsetms.com.np/login"
        self.setup_driver()
        # Create directories for saving images
        os.makedirs("captchas/original", exist_ok=True)
        os.makedirs("captchas/processed", exist_ok=True)
        # Initialize EasyOCR
        print("Initializing EasyOCR (this might take a few seconds)...")
        self.reader = easyocr.Reader(['en'])

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
            
            # Increase image size (upscale)
            height, width = gray.shape
            upscaled = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(upscaled, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(binary)
            
            # Ensure black text on white background
            if np.mean(denoised) < 127:
                denoised = cv2.bitwise_not(denoised)
            
            return denoised
            
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
            
            # Try OCR on both original and processed images
            results_original = self.reader.readtext(original_image_path, allowlist='abcdefghijklmnopqrstuvwxyz0123456789')
            results_processed = self.reader.readtext(processed_path, allowlist='abcdefghijklmnopqrstuvwxyz0123456789')
            
            # Get text from results
            text_original = ''.join([result[1].lower() for result in results_original])
            text_processed = ''.join([result[1].lower() for result in results_processed])
            
            print(f"OCR Results - Original: {text_original}, Processed: {text_processed}")
            
            # Use the result that looks more like a valid captcha
            captcha_text = text_original if len(text_original) >= len(text_processed) else text_processed
            
            if not captcha_text:
                raise Exception("No text detected in captcha")
            
            print(f"Selected captcha text: {captcha_text}")
            return captcha_text
            
        except Exception as e:
            print(f"Error getting captcha text: {str(e)}")
            return None

    def click_login_button(self):
        """Helper method to try different ways of clicking the login button"""
        selectors = [
            "input.btn.btn-primary.float-sm-right",  # Exact class from HTML
            "input[type='submit'][value='Login']",    # Input submit button
            "input[value='Login']",                   # Any input with Login value
            "button.btn-primary",                     # Generic primary button
            "//input[@value='Login']",                # XPath for login input
            "//button[contains(text(), 'Login')]"     # XPath for login button
        ]
        
        for selector in selectors:
            try:
                print(f"Trying selector: {selector}")
                if selector.startswith("//"):
                    # XPath selector
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    # CSS selector
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(0.5)
                
                # Try multiple click methods
                try:
                    # Method 1: JavaScript click
                    self.driver.execute_script("arguments[0].click();", button)
                    print("Clicked using JavaScript")
                    return True
                except:
                    try:
                        # Method 2: ActionChains click
                        ActionChains(self.driver).move_to_element(button).click().perform()
                        print("Clicked using ActionChains")
                        return True
                    except:
                        try:
                            # Method 3: Regular click
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
        try:
            print("Navigating to login page...")
            self.driver.get(self.url)
            time.sleep(3)  # Wait for page load
            
            # Fill username and password first
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

            # Now handle captcha
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
            time.sleep(1)  # Wait after filling captcha
            
            # Try to click the login button
            print("Attempting to click login button...")
            if not self.click_login_button():
                # If clicking failed, try submitting the form
                try:
                    print("Attempting to submit form directly...")
                    form = self.driver.find_element(By.CSS_SELECTOR, "form.login_form")
                    self.driver.execute_script("arguments[0].submit();", form)
                except Exception as e:
                    print(f"Form submission failed: {str(e)}")
                    # Try pressing Enter in the captcha field
                    try:
                        print("Attempting to submit via Enter key...")
                        captcha_field.send_keys(Keys.RETURN)
                    except:
                        raise Exception("All submission methods failed")

            # Wait for URL change or error message
            print("Waiting for login response...")
            time.sleep(3)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "/login" not in current_url:
                print("Login successful!")
                return True
            else:
                # Check for error messages
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

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = NepseScraper()
    try:

        username = "2021026996" 
        password = "alphaGamma1#"  
        
        success = scraper.login(username, password)
        if success:
            print("Successfully logged in!")
            time.sleep(5)
    finally:
        scraper.close()




