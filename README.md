# LinkedIn Automation Bot

This script automates the process of connecting with users who reacted to a specific LinkedIn post. It uses Selenium to control a Chrome browser, scrape profiles, and send personalized connection requests or messages.

## Prerequisites

- Python 3.7+
- Google Chrome installed
- A LinkedIn account

## Installation

1.  Clone this repository or download the files.
2.  Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Open `linkedin_bot.py` and update the following variables at the top of the file:

-   `LINKEDIN_EMAIL`: Your LinkedIn email address (or set `LINKEDIN_EMAIL` env var).
-   `LINKEDIN_PASSWORD`: Your LinkedIn password (or set `LINKEDIN_PASSWORD` env var).
-   `TARGET_POST_URL`: The full URL of the LinkedIn post you want to process.
-   `CONNECTION_MESSAGE_TEMPLATE`: The message to send to new connections. `{name}` is replaced by the user's first name.

**Safety Settings:**
-   `MIN_DELAY` / `MAX_DELAY`: Time in seconds to wait between actions.
-   `DRY_RUN`: Set to `True` to test the script without actually sending requests.

## Usage

Run the script from the terminal:

```bash
python linkedin_bot.py
```

The script will:
1.  Launch Chrome.
2.  Log in to LinkedIn.
3.  Navigate to the target post.
4.  Open the reactions list.
5.  Iterate through profiles, sending connection requests or messages based on their status.
6.  Log all actions to `engagement_log.csv`.

## Safety & Disclaimer

**WARNING:** Automated interaction with LinkedIn violates their Terms of Service and can lead to account restriction or banning.

-   Use this script at your own risk.
-   Do not run it aggressively (keep delays high).
-   Monitor your account for any warnings.
# linkdin-auto-scraper-post-reaction
