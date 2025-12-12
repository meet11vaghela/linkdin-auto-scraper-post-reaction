import os
import time
import random
import logging
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# --- Configuration ---
# Replace these with your actual credentials or use environment variables
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "vagh1747@gmail.com")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "Meet5234")
TARGET_POST_URL = "https://www.linkedin.com/feed/update/urn:li:activity:7404367839295496193/" # Replace with actual post URL

# Connection Message Template
# {name} will be replaced by the user's first name
CONNECTION_MESSAGE_TEMPLATE = """Hi this is test message,

I saw you reacted to my recent post about [Topic]. I'd love to connect and hear your thoughts on it!

Best,
Md PL"""

# Delays (in seconds)
MIN_DELAY = 5
MAX_DELAY = 30

# Logging
LOG_FILE = "engagement_log.csv"

# Safety
DRY_RUN = False # Set to True to simulate actions without actually connecting/messaging

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInBot:
    def __init__(self):
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 20)
        self.engagement_data = []

    def _setup_driver(self):
        options = Options()
        # options.add_argument("--headless") # Uncomment for headless mode
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222")
        
        # Random User Agent (Simple implementation, can be enhanced)
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")

        try:
            # Try to use Chromium driver since we saw /snap/bin/chromium in logs
            service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        except Exception:
            # Fallback to default Google Chrome
            service = Service(ChromeDriverManager().install())
            
        return webdriver.Chrome(service=service, options=options)

    def random_delay(self, min_seconds=MIN_DELAY, max_seconds=MAX_DELAY):
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

    def login(self):
        logger.info("Navigating to LinkedIn login page...")
        self.driver.get("https://www.linkedin.com/login")
        self.random_delay(2, 5)

        try:
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            password_field = self.driver.find_element(By.ID, "password")

            username_field.send_keys(LINKEDIN_EMAIL)
            self.random_delay(1, 3)
            password_field.send_keys(LINKEDIN_PASSWORD)
            self.random_delay(1, 3)
            
            password_field.send_keys(Keys.RETURN)
            
            # Check for successful login (e.g., search bar presence)
            self.wait.until(EC.presence_of_element_located((By.ID, "global-nav-search")))
            logger.info("Login successful.")
            self.random_delay()
        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.driver.quit()
            exit(1)

    def navigate_to_post(self, url):
        logger.info(f"Navigating to post: {url}")
        self.driver.get(url)
        self.random_delay()

    def get_reactions(self):
        logger.info("Opening reactions modal...")
        try:
            # Try multiple selectors for the reaction button
            # LinkedIn DOM is dynamic, so we try a few common patterns
            selectors = [
                (By.CLASS_NAME, "social-details-social-counts__reactions-count"),
                (By.XPATH, "//button[contains(@class, 'social-details-social-counts__count-value')]"),
                (By.XPATH, "//button[contains(@aria-label, 'reaction')]"),
                (By.XPATH, "//span[contains(@class, 'social-details-social-counts__reactions-count')]/ancestor::button"),
                (By.XPATH, "//ul[contains(@class, 'social-details-social-counts')]//button")
            ]
            
            reaction_element = None
            for by, value in selectors:
                try:
                    # Use a shorter wait for each individual selector to avoid long total wait
                    short_wait = WebDriverWait(self.driver, 5)
                    reaction_element = short_wait.until(EC.element_to_be_clickable((by, value)))
                    logger.info(f"Found reaction button using: {value}")
                    break
                except:
                    continue
            
            if not reaction_element:
                # If all fail, try one last generic wait or raise error
                raise Exception("Could not find reaction button with any known selector")

            reaction_element.click()
            self.random_delay(3, 6)

            # Wait for modal
            modal = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "artdeco-modal__content")))
            
            # Scroll to load more (simplified loop)
            # In a real scenario, you'd scroll until no new elements load or a limit is reached
            for _ in range(3): # Scroll a few times for demo
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal)
                self.random_delay(2, 4)

            # Extract profiles
            # Look for list items in the modal
            profile_items = modal.find_elements(By.XPATH, ".//li[contains(@class, 'artdeco-list__item')]")
            
            profiles = []
            for item in profile_items:
                try:
                    # Try multiple selectors for the name
                    name_selectors = [
                        (By.XPATH, ".//span[contains(@class, 'artdeco-entity-lockup__title')]//span[@aria-hidden='true']"),
                        (By.XPATH, ".//div[contains(@class, 'artdeco-entity-lockup__title')]//span[@aria-hidden='true']"),
                        (By.XPATH, ".//a[contains(@class, 'artdeco-entity-lockup__title')]"),
                        (By.XPATH, ".//div[contains(@class, 'artdeco-entity-lockup__content')]//div[1]")
                    ]
                    
                    name = "Unknown"
                    for by, value in name_selectors:
                        try:
                            name_element = item.find_element(by, value)
                            text = name_element.text.strip()
                            if text:
                                name = text
                                break
                        except:
                            continue
                    
                    if name == "Unknown":
                        logger.warning("Could not extract name for a profile item")
                        continue

                    # Connection status/button
                    # Button text could be "Connect", "Message", "Follow", "Pending"
                    button = None
                    button_text = "Unknown"
                    
                    button_selectors = [
                        (By.XPATH, ".//button[contains(@class, 'artdeco-button--2')]"),
                        (By.XPATH, ".//button[contains(@class, 'artdeco-button')]"),
                        (By.TAG_NAME, "button"),
                        (By.XPATH, ".//div[contains(@class, 'artdeco-entity-lockup__action')]//button")
                    ]
                    
                    for by, value in button_selectors:
                        try:
                            btns = item.find_elements(by, value)
                            for btn in btns:
                                txt = btn.text.strip()
                                # We are looking for specific action buttons, not just any button (like 'dismiss')
                                if txt in ["Connect", "Message", "Follow", "Pending", "Withdraw"]:
                                    button = btn
                                    button_text = txt
                                    break
                            if button:
                                break
                        except:
                            continue
                    
                    # Fallback: look for span with text if button text is hidden or complex
                    if not button:
                         try:
                            for text in ["Connect", "Message", "Follow"]:
                                try:
                                    # Look for a button containing this text
                                    btn = item.find_element(By.XPATH, f".//button[.//span[contains(text(), '{text}')]]")
                                    button = btn
                                    button_text = text
                                    break
                                except:
                                    pass
                         except:
                            pass

                    # Profile URL
                    try:
                        link_elem = item.find_element(By.XPATH, ".//a[contains(@class, 'artdeco-entity-lockup__title')]")
                        profile_url = link_elem.get_attribute("href")
                    except:
                        profile_url = "N/A"

                    profiles.append({
                        "name": name,
                        "button_text": button_text,
                        "element": item, # Store element to interact with it
                        "button_element": button,
                        "url": profile_url
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse a profile item: {e}")

            logger.info(f"Found {len(profiles)} profiles.")
            return profiles

        except Exception as e:
            logger.error(f"Error getting reactions: {e}")
            self.driver.save_screenshot("error_reactions.png")
            logger.info("Saved screenshot to error_reactions.png")
            return []

    def process_profiles(self, profiles):
        for profile in profiles:
            name = profile['name']
            action_button = profile['button_text']
            
            logger.info(f"Processing {name} - Status: {action_button}")
            
            if "Connect" in action_button:
                self.send_connection_request(profile)
            elif "Message" in action_button:
                self.send_message(profile)
            else:
                logger.info(f"Skipping {name} (Status: {action_button})")
                self.log_action(name, "Skipped", f"Status: {action_button}")

            # Random delay between profiles
            self.random_delay()

    def send_connection_request(self, profile):
        if DRY_RUN:
            logger.info(f"[DRY RUN] Would connect with {profile['name']}")
            self.log_action(profile['name'], "Connect (Dry Run)", "Would send request")
            return

        try:
            profile['button_element'].click()
            self.random_delay(2, 4)
            
            # "Add a note" modal
            add_note_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Add a note']")))
            add_note_button.click()
            self.random_delay(1, 3)
            
            # Type message
            message_box = self.wait.until(EC.presence_of_element_located((By.ID, "custom-message")))
            first_name = profile['name'].split()[0]
            message = CONNECTION_MESSAGE_TEMPLATE.format(name=first_name)
            message_box.send_keys(message)
            self.random_delay(2, 5)
            
            # Send
            send_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Send now']")
            send_button.click()
            
            logger.info(f"Connection request sent to {profile['name']}")
            self.log_action(profile['name'], "Connect", "Request sent")
            
        except Exception as e:
            logger.error(f"Failed to connect with {profile['name']}: {e}")
            self.log_action(profile['name'], "Error", str(e))
            # Close modal if stuck
            try:
                self.driver.find_element(By.CLASS_NAME, "artdeco-modal__dismiss").click()
            except:
                pass

    def send_message(self, profile):
        # Sending messages to existing connections from the reaction list can be tricky 
        # because clicking "Message" usually opens a chat window at the bottom.
        if DRY_RUN:
            logger.info(f"[DRY RUN] Would message {profile['name']}")
            self.log_action(profile['name'], "Message (Dry Run)", "Would send message")
            return

        try:
            profile['button_element'].click()
            self.random_delay(2, 4)
            
            # Wait for chat window
            # This part is highly dynamic and depends on whether a chat is already open, etc.
            # For safety/simplicity in this v1, we might just log that we clicked it.
            # Implementing full chat interaction requires robust selector handling for the active chat window.
            
            active_chat_input = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'msg-form__contenteditable')]")))
            
            first_name = profile['name'].split()[0]
            message = f"Hi {first_name}, thanks for reacting to my post!" # Simplified for existing connections
            
            active_chat_input.send_keys(message)
            self.random_delay(1, 3)
            
            # Send (usually Enter or clicking send button)
            # active_chat_input.send_keys(Keys.RETURN) # Be careful with auto-sending
            
            # For safety, let's NOT auto-send messages to existing connections in this version 
            # to avoid spamming close contacts accidentally. We'll just type it.
            logger.info(f"Drafted message to {profile['name']}")
            self.log_action(profile['name'], "Message Drafted", "Message typed but not sent (safety)")
            
            # Close chat window to clean up
            try:
                close_chat = self.driver.find_element(By.XPATH, "//button[contains(@class, 'msg-overlay-bubble-header__control--close')]")
                close_chat.click()
            except:
                pass

        except Exception as e:
            logger.error(f"Failed to message {profile['name']}: {e}")
            self.log_action(profile['name'], "Error", str(e))

    def log_action(self, name, action, details):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "Timestamp": timestamp,
            "Name": name,
            "Action": action,
            "Details": details
        }
        self.engagement_data.append(record)
        
        # Append to CSV immediately
        df = pd.DataFrame([record])
        if not os.path.isfile(LOG_FILE):
            df.to_csv(LOG_FILE, index=False)
        else:
            df.to_csv(LOG_FILE, mode='a', header=False, index=False)

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    bot = LinkedInBot()
    try:
        bot.login()
        bot.navigate_to_post(TARGET_POST_URL)
        profiles = bot.get_reactions()
        bot.process_profiles(profiles)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        bot.close()
