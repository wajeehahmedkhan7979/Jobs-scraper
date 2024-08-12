LinkedIn Job Scraper
Overview
The LinkedIn Job Scraper is a web application that allows users to scrape job postings from LinkedIn based on specified criteria. It uses Selenium for web scraping and Flask for the web interface. Users can specify job roles, locations, and date ranges to filter job postings and download the results as an Excel file.

Features
Login to LinkedIn: Authenticates users to access LinkedIn's job search functionality.
Search Jobs: Searches for jobs based on user-provided job roles and locations.
Apply Filters: Allows users to filter job postings by date (e.g., past month, past week, past 24 hours).
Download Results: Saves the scraped job data to an Excel file, which can be downloaded by the user.
Custom File Path: Users can specify the file path where the Excel file will be saved.
Installation
Prerequisites
Python 3.7 or higher
pip (Python package installer)
Clone the Repository
bash
Copy code
git clone https://github.com/yourusername/linkedin-job-scraper.git
cd linkedin-job-scraper
Install Dependencies
Create a virtual environment and install the required packages:

bash
Copy code
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
Additional Setup
ChromeDriver: The project uses ChromeDriver, which should be installed automatically via webdriver_manager.
Usage
Running the Application
Start the Flask application by running:

bash
Copy code
python app.py
The application will be available at http://127.0.0.1:5000.

Making Requests
Open the provided HTML form in a web browser.
Fill in the required fields: email, password, job role, and file path.
Optionally provide location and date posted filters.
Submit the form to scrape job data.
Endpoints
POST /scrape: Accepts JSON data with the following fields:
email: LinkedIn email address
password: LinkedIn password
job_role: Role to search for
location: (Optional) Location to filter by
date_posted: (Optional) Date range for job postings
file_path: Path to save the Excel file
Example Request
json
Copy code
{
  "email": "user@example.com",
  "password": "yourpassword",
  "job_role": "Software Engineer",
  "location": "San Francisco",
  "date_posted": "Past month",
  "file_path": "downloads/software_engineer.xlsx"
}
Notes
Ensure that you handle your LinkedIn credentials securely and avoid exposing them in public repositories.
Be aware of LinkedIn's scraping policies and terms of service.
Contributing
Feel free to contribute to this project by submitting issues or pull requests. Please follow the guidelines for contributing.

License
This project is licensed under the MIT License - see the LICENSE file for details.

Contact
For questions or further information, you can reach me at [wajeehahmed7@gmail.com].

