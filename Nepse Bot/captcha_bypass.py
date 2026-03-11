import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import cv2
import numpy as np
import pytesseract
from PIL import Image
import io
from base64 import b64decode

class NepseScraper:
    def __init__(self):
        self.url = "https://tms21.nepsetms.com.np/login"
        self.setup_driver()

    def setup_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment to run in headless mode
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=chrome_options)

    def preprocess_captcha_image(self, image):
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to preprocess the image
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Apply dilation to connect text components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
        processed = cv2.dilate(thresh, kernel, iterations=1)
        
        # Apply median blur to remove noise
        processed = cv2.medianBlur(processed, 3)
        
        return processed

    def get_captcha_text(self):
        # Find and get the captcha image
        captcha_element = self.driver.find_element(By.CSS_SELECTOR, "img[alt='captcha']")
        
        # Get the base64 image data
        img_base64 = captcha_element.get_attribute("src").split(",")[1]
        img_data = b64decode(img_base64)
        
        # Convert to numpy array
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Preprocess the image
        processed_img = self.preprocess_captcha_image(img)
        
        # Extract text from the processed image
        captcha_text = pytesseract.image_to_string(processed_img, config='--psm 7 -c tessedit_char_whitelist=0123456789')
        
        # Clean the extracted text
        captcha_text = ''.join(filter(str.isdigit, captcha_text))
        
        return captcha_text

    def login(self, username, password):
        try:
            self.driver.get(self.url)
            time.sleep(2)  # Wait for page to load completely

            # Find and fill username
            username_field = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Client Code/ User Name']")
            username_field.send_keys(username)

            # Find and fill password
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Password']")
            password_field.send_keys(password)

            # Handle captcha
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # Get and solve captcha
                    captcha_text = self.get_captcha_text()
                    print(f"Detected Captcha: {captcha_text}")

                    # Enter captcha
                    captcha_field = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Enter Captcha']")
                    captcha_field.clear()
                    captcha_field.send_keys(captcha_text)

                    # Click login button
                    login_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
                    login_button.click()

                    # Wait to see if login was successful
                    time.sleep(2)
                    
                    # Check if we're still on the login page
                    if "/login" not in self.driver.current_url:
                        print("Login successful!")
                        return True
                    
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_attempts - 1:
                        # Refresh the page for a new captcha
                        self.driver.refresh()
                        time.sleep(2)
                    continue

            print("Failed to login after maximum attempts")
            return False

        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    # Set your Tesseract path if it's not in PATH
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows example
    
    scraper = NepseScraper()
    try:
        username = "YOUR_USERNAME"  # Replace with actual username
        password = "YOUR_PASSWORD"  # Replace with actual password
        
        success = scraper.login(username, password)
        if success:
            print("Successfully logged in!")
            # Add your scraping logic here
            time.sleep(5)  # Wait to see the result
    finally:
        scraper.close()