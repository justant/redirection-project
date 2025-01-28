import os
import signal
import psutil
import time
import schedule
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from TW import TW
from openai_trans import analyze_and_translate_tweet
from output_handler import handle_new_tweets

# 크롬 프로필 설정 (세션 유지)
CHROME_PROFILE_PATH = "C:\\Users\\Justant\\AppData\\Local\\Google\\Chrome\\User Data"
PROFILE_DIRECTORY = "Default"
CHROME_DRIVER_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chromedriver.exe"

# 기존 Chrome 및 Chromedriver 프로세스 종료
def kill_chrome_processes():
    chrome_processes = ["chrome.exe", "chromedriver.exe"]
    for process in psutil.process_iter(['name']):
        try:
            if process.info['name'] in chrome_processes:
                os.kill(process.pid, signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

# Selenium 드라이버 초기화
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    chrome_options.add_argument(f"--profile-directory={PROFILE_DIRECTORY}")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver

# 트윗 스크래핑 및 TW 객체 생성
def fetch_tweets_as_objects(driver, username, tweet_count=5):
    """
    Fetch the latest tweets of a user and create TW objects.
    Handles quoted tweets and ensures proper data scraping.

    :param driver: Selenium WebDriver
    :param username: Twitter username
    :param tweet_count: Number of tweets to fetch
    :return: List of TW objects
    """
    url = f"https://twitter.com/{username}"
    driver.get(url)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(3)

    tweets = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while len(tweets) < tweet_count:
        tweet_elements = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')

        for tweet in tweet_elements:
            if len(tweets) >= tweet_count:
                break

            try:
                # 디버깅: 현재 트윗의 HTML 구조 출력 (최초 1개만 출력)
                if len(tweets) == 0:  # 첫 번째 트윗만 출력
                    print("\n===== DEBUGGING TWEET HTML STRUCTURE =====")
                    print(tweet.get_attribute('innerHTML'))
                    print("===========================================\n")

                # Basic tweet information
                user_name = username
                user_id = tweet.find_element(By.XPATH, './/div[@dir="ltr"]/span').text
                date = tweet.find_element(By.XPATH, './/time').get_attribute("datetime")
                text = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text

                # Photos and videos
                photos = [img.get_attribute("src") for img in tweet.find_elements(By.XPATH, './/img[contains(@src, "media")]')]
                videos = [video.get_attribute("src") for video in tweet.find_elements(By.XPATH, './/video')]

                # Check for quoted tweets
                is_quote = False
                quoted_tweet = None

                try:
                    # 디버깅: quote-tweet이 존재하는지 확인
                    quote_container = tweet.find_element(By.XPATH, './/div[@data-testid="quote-tweet"]')
                    print("[DEBUG] Found quote-tweet container")

                    # 디버깅: 링크 요소 확인
                    quote_link = quote_container.find_element(By.XPATH, './/a[@role="link"]')
                    print(f"[DEBUG] Quote link href: {quote_link.get_attribute('href')}")

                    quoted_tweet_link = quote_link.get_attribute("href")
                    # ... [기존 코드 유지] ...

                except Exception as e:
                    print(f"[DEBUG] Quote detection failed: {str(e)}")
                    # 디버깅: 실패 시 트윗 구조 추가 출력
                    print("\n===== FAILED TWEET STRUCTURE =====")
                    print(tweet.get_attribute('innerHTML'))
                    print("==================================\n")

                try:
                    quote_link = tweet.find_element(By.XPATH, './/div[@data-testid="tweet"]//div[@data-testid="quote-tweet"]//a[@role="link"]')
                    print(f"Quote link found: {quote_link.get_attribute('href')}")
                except Exception as e:
                    print(f"Quote link not found: {e}")

                    if quote_link:
                        quoted_tweet = fetch_original_tweet(driver, quote_link)
                        is_quote = True
                except Exception as e:
                    print(f"Not a quoted tweet or error finding quote link: {e}")
                    pass  # Not a quoted tweet

                # Create a TW object
                tw = TW(
                    user_name=user_name,
                    user_id=user_id,
                    date=date,
                    text=text,
                    photos=photos,
                    videos=videos,
                    is_quote=is_quote,
                    quoted_tweet=quoted_tweet
                )

                if tw not in tweets:  # Avoid duplicates
                    tweets.append(tw)

            except Exception as e:
                print(f"Error fetching tweet data: {e}")
                continue

        # Scroll down to load more tweets
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return tweets


# 원본 트윗 스크래핑
def fetch_original_tweet(driver, original_tweet_link):
    """
    Fetches the details of the quoted tweet from the provided link.

    :param driver: Selenium WebDriver
    :param original_tweet_link: URL of the quoted tweet
    :return: A TW object containing the quoted tweet data
    """
    try:
        driver.get(original_tweet_link)

        # Wait for the tweet to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//article[@data-testid="tweet"]'))
        )
        time.sleep(2)

        # Locate the tweet element
        tweet_element = driver.find_element(By.XPATH, '//article[@data-testid="tweet"]')

        # Extract tweet data
        user_name = tweet_element.find_element(By.XPATH, './/div[@data-testid="User-Names"]//span[1]').text
        user_id = tweet_element.find_element(By.XPATH, './/div[@data-testid="User-Names"]//span[contains(text(), "@")]').text
        date = tweet_element.find_element(By.XPATH, './/time').get_attribute("datetime")
        text = tweet_element.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text

        # Photos and videos
        photos = [img.get_attribute("src") for img in tweet_element.find_elements(By.XPATH, './/img[contains(@src, "media")]')]
        videos = [video.get_attribute("src") for video in tweet_element.find_elements(By.XPATH, './/video')]

        return TW(
            user_name=user_name,
            user_id=user_id,
            date=date,
            text=text,
            photos=photos,
            videos=videos
        )

    except Exception as e:
        print(f"Error fetching quoted tweet: {e}")
        return None


def check_new_tweets():
    username = "tele_filming"
    driver = init_driver()

    if not hasattr(check_new_tweets, "last_tweets"):
        check_new_tweets.last_tweets = set()  # 이전 트윗을 저장할 Set

    current_tweets = fetch_tweets_as_objects(driver, username, tweet_count=5)
    new_tweets = [tweet for tweet in current_tweets if (tweet.text, tweet.date) not in check_new_tweets.last_tweets]

    if new_tweets:
        print("새로운 트윗이 감지되었습니다!")
        handle_new_tweets(new_tweets)

    # 이전 트윗 상태 업데이트
    check_new_tweets.last_tweets.update((tweet.text, tweet.date) for tweet in current_tweets)

    driver.quit()

# 스케줄러 설정
def start_scheduler():
    check_new_tweets()
    schedule.every(1).minutes.do(check_new_tweets)
    while True:
        schedule.run_pending()
        time.sleep(1)

# 메인 실행
if __name__ == "__main__":
    kill_chrome_processes()
    start_scheduler()
