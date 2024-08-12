from __future__ import print_function
import time
import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app)

def login_to_linkedin(driver, email, password):
    try:
        driver.get("https://www.linkedin.com/login")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.feed-identity-module"))
        )
        logging.info("Main feed page loaded successfully.")
    except TimeoutException:
        logging.error("Timeout reached. Unable to load the main feed page.")
    except Exception as e:
        logging.error(f"An error occurred while waiting for the main feed page: {e}")

def search_jobs(driver, job_role,location):
    try:
        driver.get("https://www.linkedin.com/jobs")
        logging.info("Navigating to LinkedIn jobs page.")
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.jobs-search-box__text-input"))
        )
        search_box.clear()
        search_box.send_keys(job_role)
        search_box.send_keys(Keys.RETURN)
        logging.info(f"Searching for jobs: {job_role}")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results"))
        )
        logging.info("Job search completed.")
    except TimeoutException as e:
        logging.error(f"Timeout during job search: {e}")
    except NoSuchElementException as e:
        logging.error(f"Element not found during job search: {e}")
    except WebDriverException as e:
        logging.error(f"WebDriver error during job search: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during job search: {e}")
        
    if location:
                apply_location_filter(driver, location)

def apply_location_filter(driver, location):
    if location:
        try:
            location_box = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.jobs-search-box__input.jobs-search-box__input--location"))
            )
            location_box.clear()
            location_box.send_keys(location)
            location_box.send_keys(Keys.RETURN)
            logging.info(f"Location filter applied: {location}")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results"))
            )
        except Exception as e:
            logging.error(f"Error applying location filter: {e}")

def apply_date_posted_filter(driver, date_posted):
    """
    Applies the 'Date Posted' filter on LinkedIn based on the selected filter option.
    
    :param driver: Selenium WebDriver instance.
    :param date_posted: The filter option selected from the HTML dropdown.
                            Possible values: 'Any time', 'Past month', 'Past week', 'Past 24 hours'.
    """
    # Open the 'Date Posted' filter dropdown
    date_filter_button = driver.find_element(By.ID, "searchFilter_timePostedRange")
    date_filter_button.click()

    # Select the appropriate filter option based on the date_posted variable
    if date_posted == "Any time":
        option = driver.find_element(By.CSS_SELECTOR, "input#timePostedRange- + label")
        option.click()

    elif date_posted == "Past month":
        option = driver.find_element(By.CSS_SELECTOR, "input#timePostedRange-r2592000 + label")
        option.click()

    elif date_posted == "Past week":
        option = driver.find_element(By.CSS_SELECTOR, "input#timePostedRange-r604800 + label")
        option.click()

    elif date_posted == "Past 24 hours":
        option = driver.find_element(By.CSS_SELECTOR, "input#timePostedRange-r86400 + label")
        option.click()

    else:
        raise ValueError("Invalid filter option selected.")

    # After selecting the filter, click the "Show results" button
    show_results_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label^='Apply current filter']"))
    )
    show_results_button.click()

    print(f"Applied '{date_posted}' filter successfully.")


def scroll_jobs_container(driver):
    try:
        # Wait for the jobs container to be present after the date posted filter is applied
        job_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results-list__pagination.scaffold-layout__list-container"))
        )
        logging.info("Found the job container. Starting to scroll.")
        
        last_height = driver.execute_script("return arguments[0].scrollHeight", job_container)
        
        while True:
            # Scroll to the bottom of the container
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", job_container)
            logging.info("Scrolled to the bottom of the jobs container.")
            time.sleep(3)  # Wait for the content to load
            
            new_height = driver.execute_script("return arguments[0].scrollHeight", job_container)
            
            # If the height hasn't changed, the scrolling is done
            if new_height == last_height:
                logging.info("Scrolling completed. No more content to load.")
                break
            
            last_height = new_height
            
    except TimeoutException:
        logging.error("Timeout while waiting for the jobs container to load.")
    except WebDriverException as e:
        logging.error(f"WebDriver error while scrolling jobs container: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while scrolling down jobs container: {e}")



def scrape_job_data(job):
    try:
        job_title = job.find_element(By.CSS_SELECTOR, "a.job-card-list__title").text
        company_name = job.find_element(By.CSS_SELECTOR, "div.artdeco-entity-lockup__subtitle span.job-card-container__primary-description").text
        Job_link = job.find_element(By.CSS_SELECTOR, "a.job-card-list__title").get_attribute("href")
        job_location = job.find_element(By.CSS_SELECTOR, "div.artdeco-entity-lockup__caption li.job-card-container__metadata-item").text
        
        job_data = {
            "job_title": job_title,
            "company_name": company_name,
            "Job_link": Job_link,
            "job_location": job_location
        }
        logging.info(f"Scraped job data: {job_data}")
        return job_data
    except NoSuchElementException as e:
        logging.warning(f"Error scraping job data: {e}")
        return None

def scrape_all_pages(driver):
    jobs = []
    wait = WebDriverWait(driver, 5)
    
    while True:
        try:
            # Wait for the job elements to be present and scrape them
            job_elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".scaffold-layout__list-container li"))
            )
            
            for job in job_elements:
                job_data = scrape_job_data(job)
                if job_data:
                    jobs.append(job_data)
                else:
                    logging.info("No job data returned for an element.")
            
            # Find the active page button
            active_page = driver.find_element(By.CSS_SELECTOR, ".artdeco-pagination__indicator--number.active")
            
            # Try to find the next page button by looking for the next sibling element of the active page
            try:
                next_page_button = active_page.find_element(By.XPATH, 'following-sibling::li/button')
            except NoSuchElementException:
                # If no next sibling exists, check if there's a "..." button
                ellipsis_button = driver.find_element(By.XPATH, "//li[contains(@class, 'artdeco-pagination__indicator') and contains(., '…')]/button")
                if ellipsis_button:
                    next_page_button = ellipsis_button
                else:
                    logging.info("No more pages left to scrape.")
                    break

            if next_page_button:
                next_page_button.click()
                logging.info("Clicked on next page button.")
                time.sleep(3)  # Small delay to ensure the next page loads
            else:
                logging.info("No more pages left to scrape.")
                break
        
        except NoSuchElementException:
            logging.error("No job elements found on the page.")
            break
        except TimeoutException as e:
            logging.error(f"Timeout exception during pagination: {e}")
            break
        except WebDriverException as e:
            logging.error(f"WebDriver error during pagination: {e}")
            break
    
    logging.info(f"Total jobs scraped: {len(jobs)}")
    return jobs


def perform_scraping(email, password, job_role, location, date_posted, file_path):
    options = Options()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        login_to_linkedin(driver, email, password)
        search_jobs(driver, job_role, location)

        if date_posted:
            apply_date_posted_filter(driver, date_posted)
        
        scroll_jobs_container(driver)

        job_data = scrape_all_pages(driver)
        
        if job_data:
            df = pd.DataFrame(job_data)
            df.to_excel(file_path, index=False)
            logging.info(f"Jobs data saved to {file_path}")
        else:
            logging.warning("No job data to save.")
            file_path = None

    finally:
        driver.quit()

    return file_path

@app.route('/scrape', methods=['POST'])
def scrape_jobs():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    job_role = data.get('job_role')
    location = data.get('location', None)
    date_posted = data.get('date_posted', None)
    file_path = data.get('file_path')

    if not email or not password or not job_role or not file_path:
        return jsonify({"error": "Missing required fields."}), 400

    # Ensure the directory exists
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = perform_scraping(email, password, job_role, location, date_posted, file_path)

    if file_path:
        return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path), as_attachment=True)
    else:
        return jsonify({"error": "No job data scraped."}), 500

if __name__ == '__main__':
    app.run(debug=True)