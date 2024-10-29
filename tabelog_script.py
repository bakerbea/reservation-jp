import requests
from bs4 import BeautifulSoup
import csv
import time

# Base URL for Tabelog's Tokyo restaurant listing page, sorted by rating
base_url = 'https://tabelog.com/en/tokyo/rstLst/'

# Define the minimum rating threshold
min_rating = 3.5  # Adjust this as needed

# Number of pages to scrape (adjust based on how many pages you want to go through)
num_pages = 5

# Headers to mimic a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# List to store restaurant data
restaurants = []

# Loop over the specified number of pages
for page in range(1, num_pages + 1):
    # Construct the URL for each page
    url = f"{base_url}{page}/?SrtT=rt"
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all restaurant containers
        restaurant_list = soup.find_all('div', class_='list-rst__rst-name-wrap')

        for restaurant in restaurant_list:
            # Extract the restaurant name
            name_tag = restaurant.find('a', class_='list-rst__rst-name-target')
            if name_tag:
                name = name_tag.get_text(strip=True)

                # Extract the rating
                rating_tag = restaurant.find_next('span', class_='c-rating__val')
                if rating_tag:
                    try:
                        rating = float(rating_tag.get_text(strip=True))
                        # Filter by the minimum rating
                        if rating >= min_rating:
                            restaurants.append({'Name': name, 'Rating': rating})
                    except ValueError:
                        # Handle cases where rating is missing or not a number
                        pass

        # Wait between requests to mimic human browsing and avoid IP blocking
        time.sleep(2)
    else:
        print(f"Failed to retrieve data for page {page}. Status code: {response.status_code}")

# Print and save the result set
print("Scraped Restaurants with Rating >= ", min_rating)
for restaurant in restaurants:
    print(restaurant)

# Save results to CSV
with open('test2.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['Name', 'Rating'])
    writer.writeheader()
    for restaurant in restaurants:
        writer.writerow(restaurant)

print(f"Scraping complete! {len(restaurants)} restaurants found with a rating of {min_rating} or higher.")
