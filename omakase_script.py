import requests
import pandas as pd
from bs4 import BeautifulSoup

# Read cookie string from a file
with open("cookie.txt", "r") as file:
    cookie_string = file.read().strip()

# Parse the cookie string into a dictionary
def parse_cookie_string(cookie_string):
    cookies = {}
    for item in cookie_string.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value
    return cookies

# Convert the cookie string to a dictionary
COOKIE_PAYLOAD = parse_cookie_string(cookie_string)

# Function to load restaurant names from a CSV file
def load_restaurants(filename):
    df = pd.read_csv(filename)
    restaurants = df[['Name', 'Rating']].to_dict(orient='records')
    return restaurants

# Function to call the API and get available dates for a specific month
def get_available_dates(restaurant_slug, year_month, reservation_token, cookies):
    available_dates = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }

    api_url = f"https://omakase.in/users/api/availability_dates?restaurant_slug={restaurant_slug}&year_month={year_month}&reservation_calendar_token={reservation_token}"
    response = requests.get(api_url, headers=headers, cookies=cookies)

    if response.status_code == 200 and response.content:
        try:
            data = response.json()
            if data.get("status") == 200 and data["data"].get("has_availability"):
                available_dates = data["data"]["available_dates"]
        except requests.exceptions.JSONDecodeError:
            print(f"Failed to parse JSON for {restaurant_slug}. Response text: {response.text}")
    else:
        print(f"Failed to retrieve availability for {restaurant_slug} in {year_month}. Status code: {response.status_code}")
        print(f"Response content: {response.text}")
    
    return available_dates

# Function to check detailed availability for a specific date and restaurant_slug
def check_detailed_availability(restaurant_slug, date, reservation_token, cookies, guests_count=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }
    api_url = f"https://omakase.in/users/api/availability_dates/{restaurant_slug}?date={date}&reservation_calendar_token={reservation_token}"
    response = requests.get(api_url, headers=headers, cookies=cookies)

    if response.status_code == 200 and response.content:
        try:
            data = response.json()
            available_slots = []

            # Filter based on guests_count if provided
            for operation, slots in data["data"]["grouped_online_stock_groups"].items():
                for slot in slots:
                    if not guests_count or guests_count in slot["guests_count_option_values"]:
                        available_slots.append({
                            "date": date,
                            "operation": operation,
                            "display_title": slot["display_title"],
                            "start_time": slot["time_options"][0]["start_time"] if slot["time_options"] else "N/A",
                            "end_time": slot["time_options"][0]["end_time"] if slot["time_options"] else "N/A",
                            "courses": [course["title"] for course in slot["courses"]],
                            "price": [course["price"] for course in slot["courses"]]
                        })
            return available_slots
        except requests.exceptions.JSONDecodeError:
            print(f"Failed to parse JSON for {restaurant_slug} on {date}. Response text: {response.text}")
    else:
        print(f"Failed to retrieve detailed availability for {restaurant_slug} on {date}. Status code: {response.status_code}")
        print(f"Response content: {response.text}")

    return []

# Function to search for a restaurant and get its detail page and availability
def check_availability(restaurant_name, year_month, reservation_token, cookies, guests_count):
    search_url = f"https://omakase.in/en/r?area=&cuisine=&search_keywords={restaurant_name}&commit=Search"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }

    session = requests.Session()
    session.headers.update(headers)
    response = session.get(search_url, cookies=cookies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        restaurant_items = soup.find_all('div', class_='c-restaurant_item')
        for item in restaurant_items:
            header_tag = item.find('h3', class_='ui header')
            if header_tag and header_tag.get_text(strip=True).lower() == restaurant_name.lower():
                detail_link_tag = item.find('a', href=True)
                if detail_link_tag:
                    detail_link = "https://omakase.in" + detail_link_tag['href']
                    restaurant_slug = detail_link.split('/')[-1]
                    print(f"Found detail page for {restaurant_name}: {detail_link}")
                    
                    # Get available dates for the restaurant
                    available_dates = get_available_dates(restaurant_slug, year_month, reservation_token, cookies)
                    detailed_availability = []
                    for date in available_dates:
                        detailed_availability.extend(check_detailed_availability(restaurant_slug, date, reservation_token, cookies, guests_count))

                    return detail_link, detailed_availability
        
        print(f"No matching restaurant found for {restaurant_name}")
        return None, []
    else:
        print(f"Failed to retrieve search results for {restaurant_name}. Status code: {response.status_code}")
        return None, []

# Main script
def main():
    cookies = COOKIE_PAYLOAD

    year = input("Enter the year to check for availability (e.g., 2024): ")
    month = input("Enter the month to check for availability (e.g., 11 for November): ")
    reservation_token = input("Enter the reservation calendar token: ")
    guest_count = input("Enter the number of guests (leave blank if any number is fine): ")
    guests_count = int(guest_count) if guest_count else None
    year_month = f"{year}-{month.zfill(2)}"

    input_filename = 'test.csv'
    restaurants = load_restaurants(input_filename)

    output_data = {
        'Restaurant': [],
        'Tabelog Score': [],
        'Detail Page URL': [],
        'Available Slots': []
    }

    for restaurant in restaurants:
        restaurant_name = restaurant['Name']
        print(f"Checking availability for {restaurant_name} in {year_month}...")
        detail_url, available_slots = check_availability(restaurant_name, year_month, reservation_token, cookies, guests_count)
        output_data['Restaurant'].append(restaurant_name)
        tabelog_score = restaurant.get('Rating', 'N/A')
        output_data['Tabelog Score'].append(tabelog_score)
        output_data['Detail Page URL'].append(detail_url if detail_url else "N/A")
        
        formatted_slots = [f"{slot['date']} ({slot['operation']}): {slot['display_title']}" for slot in available_slots]
        # Format each available slot with new lines for better readability
        formatted_slots = "\n".join([f"{slot['date']} ({slot['operation']}): {slot['display_title']}" for slot in available_slots])
        output_data['Available Slots'].append(formatted_slots if formatted_slots else "No Availability")


    output_filename = 'restaurant_availability.csv'
    output_df = pd.DataFrame(output_data)
    output_df.to_csv(output_filename, index=False)
    print(f"Availability data saved to {output_filename}")

if __name__ == "__main__":
    main()
