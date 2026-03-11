
        # For trigger price functionality
        self.is_logged_in = False
        self.order_placed = False
        self.trigger_monitor_running = False
        self.submit_button = None

    def setup_driver(self):
        # Use Firefox instead of Chrome
        firefox_options = Options()
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Firefox(options=firefox_options)
        self.wait = WebDriverWait(self.driver, 10)
        logging.info("Firefox WebDriver initialized")
        return
        # Firefox is used instead
        # firefox_options.binary_location = "/usr/bin/google-chrome-stable"
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--js-flags=--max_old_space_size=4096")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        logging.info("Chrome WebDriver initialized")

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
-- INSERT --                                                                                      82,1           6%