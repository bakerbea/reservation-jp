from pycookiecheat import chrome_cookies

def get_omakase_cookies():
    try:
        # Use the identified profile's Cookies file
        cookies = chrome_cookies('https://omakase.in', cookie_file='/Users/beasiy/Library/Application Support/Google/Chrome/Profile 1/Cookies')
        print("Successfully retrieved cookies:")
        for name, value in cookies.items():
            print(f"{name}: {value}")
        return cookies
    except Exception as e:
        print(f"Error retrieving cookies: {e}")
        return None

# Test the cookie retrieval
cookies = get_omakase_cookies()