import subprocess
import random
import time
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

def fetch_page(url):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    try:
        result = subprocess.run(
            ["wget", "--quiet", "--output-document=-", "--user-agent", user_agent, url],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while fetching {url}: {e}")
        return None

def get_max_pages(base_url):
    html_content = fetch_page(base_url)
    if not html_content:
        return 1
    
    soup = BeautifulSoup(html_content, 'html.parser')
    nav_element = soup.select_one("nav[data-test-id='cms-navigation']")
    if nav_element:
        page_links = nav_element.select("a.css-1lsqgb5")
        if page_links:
            last_page_element = page_links[-1]  # Select the last pagination link
            return int(last_page_element.text)
    return 1

def extract_course_info(article):
    # Extract title
    title = article.find('h2', class_='css-1k3iole').text.strip()
    
    # Extract description
    description = article.find('p', class_='css-17ftio6').text.strip()
    
    # Extract length
    length_span = article.select_one('span.css-10eknbb')
    length = 'N/A'
    if length_span:
    # Get all text content after the svg element
        length = ''.join(length_span.find('svg').next_siblings).strip()

    category_spans = article.select('span.css-10eknbb')
    
    # Extract category
    category = 'N/A'
    if len(category_spans) > 1:
        category = category_spans[1].text.strip()
        category = category[3:] if category.startswith('Tag') else category
    
    # Extract technology
    technology_div = article.find('div', class_='css-r4pjff')
    technology = technology_div['data-testid'] if technology_div else 'N/A'
    
    # Extract teacher
    teacher_span = article.find_all('span', class_='css-10eknbb')[-1]

    teacher = 'N/A'
    if len(teacher_span) > 1:
        teacher = teacher_span.text.strip() if teacher_span else 'N/A'
        teacher = teacher[4:] if teacher.startswith('User') else teacher
    
    return {
        'Title': title,
        'Description': description,
        'Length': length,
        'Category': category,
        'Technology': technology,
        'Teacher': teacher
    }

def scrape_and_process_datacamp(base_url):
    max_pages = get_max_pages(base_url)
    print(f"Discovered {max_pages} pages to scrape.")
    all_courses = []

    for page in tqdm(range(1, max_pages + 1), desc="Scraping Progress", unit="page"):
        url = base_url if page == 1 else f"{base_url}/page/{page}"
        html_content = fetch_page(url)
        
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            articles = soup.select('article.css-pg8v6f')
            for article in articles:
                course_info = extract_course_info(article)
                all_courses.append(course_info)
        
        time.sleep(random.uniform(1, 3))  # Add a random delay between requests

    return pd.DataFrame(all_courses)

if __name__ == "__main__":
    base_url = "https://www.datacamp.com/courses-all"
    df = scrape_and_process_datacamp(base_url)
    output_file = "datacamp_courses.csv"
    df.to_csv(output_file, index=False)
    print(f"Data has been extracted and saved to {output_file}")
