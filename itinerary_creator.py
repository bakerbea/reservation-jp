import pandas as pd
import re
from datetime import datetime, timedelta

def parse_available_slots(slot_string):
    # Handle "No Availability" case
    if slot_string == "No Availability":
        return []
    
    # Extract date, operation, and display title using regex
    slot_pattern = re.compile(r"(\d{4}-\d{2}-\d{2}) \((\w+)\): (.+)")
    slots = []
    
    # Process each slot entry
    for match in slot_pattern.finditer(slot_string):
        date, operation, display_title = match.groups()
        slots.append({
            "date": date,
            "operation": operation,
            "display_title": display_title
        })
    
    return slots

def load_reservations(filenames):
    # Load and combine data from multiple files
    dataframes = []
    for filename in filenames:
        try:
            df = pd.read_csv(filename)
            dataframes.append(df)
        except FileNotFoundError:
            print(f"File {filename} not found.")
        except pd.errors.ParserError:
            print(f"Error parsing {filename}. Ensure it's a valid CSV.")
    
    combined_df = pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()
    combined_df['Available Slots'] = combined_df['Available Slots'].apply(parse_available_slots)
    return combined_df

def filter_dates(df, start_date, end_date):
    # Convert start and end date strings to datetime objects
    start_dt = datetime.strptime(start_date, "%m/%d/%Y")
    end_dt = datetime.strptime(end_date, "%m/%d/%Y")
    
    # Filter slots within the date range
    filtered_slots = []
    for _, row in df.iterrows():
        slots = [
            slot for slot in row['Available Slots']
            if start_dt.date() <= datetime.strptime(slot['date'], "%Y-%m-%d").date() <= end_dt.date()
        ]
        if slots:
            row['Available Slots'] = slots
            filtered_slots.append(row)
    return pd.DataFrame(filtered_slots), start_dt, end_dt

def suggest_reservations_strict_no_repeat(df, allow_repeats):
    # Initialize suggestions dictionary
    suggestions = {}
    
    # Sort by rating in descending order, so higher-rated restaurants are prioritized
    df = df.sort_values(by="Tabelog Score", ascending=False, na_position='last')
    
    # Set to track used restaurants across all dates when repeats are not allowed
    used_restaurants = set()
    
    # Loop through each day in the date range and suggest lunch and dinner
    dates = sorted(set(slot['date'] for slots in df['Available Slots'] for slot in slots))
    for date in dates:
        suggestions[date] = {"lunch": None, "dinner": None}
        
        for _, row in df.iterrows():
            restaurant = row['Restaurant']
            
            # Check for repeats and skip if not allowed
            if not allow_repeats and restaurant in used_restaurants:
                continue
            
            for slot in row['Available Slots']:
                if slot['date'] == date:
                    # Assign to lunch or dinner based on operation type, if not already filled
                    if slot['operation'] == "lunch" and not suggestions[date]["lunch"]:
                        suggestions[date]["lunch"] = {
                            "restaurant": restaurant,
                            "reservation": slot['display_title']
                        }
                        used_restaurants.add(restaurant)  # Mark restaurant as used

                    elif slot['operation'] == "dinner" and not suggestions[date]["dinner"]:
                        suggestions[date]["dinner"] = {
                            "restaurant": restaurant,
                            "reservation": slot['display_title']
                        }
                        used_restaurants.add(restaurant)  # Mark restaurant as used
                        
                    # Break once both lunch and dinner slots are filled for the date
                    if suggestions[date]["lunch"] and suggestions[date]["dinner"]:
                        break
            if suggestions[date]["lunch"] and suggestions[date]["dinner"]:
                break
    return suggestions

def generate_suggestion_output(suggestions, start_dt, end_dt):
    # Generate a list of all dates in the trip range
    all_dates = [start_dt + timedelta(days=i) for i in range((end_dt - start_dt).days + 1)]
    
    output_data = {
        "Date": [],
        "Lunch": [],
        "Dinner": []
    }
    
    for date in all_dates:
        date_str = date.strftime("%Y-%m-%d")
        slots = suggestions.get(date_str, {"lunch": None, "dinner": None})
        
        output_data["Date"].append(date_str)
        output_data["Lunch"].append(
            f"{slots['lunch']['restaurant']} - {slots['lunch']['reservation']}" if slots['lunch'] else "No suggestion"
        )
        output_data["Dinner"].append(
            f"{slots['dinner']['restaurant']} - {slots['dinner']['reservation']}" if slots['dinner'] else "No suggestion"
        )
    
    output_df = pd.DataFrame(output_data)
    output_filename = "suggested_reservations.xlsx"
    output_df.to_excel(output_filename, index=False)
    print(f"Suggested reservations saved to {output_filename}")
    return output_filename

def main():
    # Prompt user for input files
    filenames = input("Enter the filenames of the output files separated by commas: ").split(",")
    filenames = [filename.strip() for filename in filenames]

    # Load combined reservations data
    df = load_reservations(filenames)
    
    # Prompt for start and end date
    start_date = input("Enter the start date of your trip (mm/dd/yyyy): ")
    end_date = input("Enter the end date of your trip (mm/dd/yyyy): ")
    
    # Prompt for allowing repeat restaurants
    allow_repeats_input = input("Allow repeated restaurants? (yes or no, default is no): ").strip().lower()
    allow_repeats = allow_repeats_input == "yes"
    
    # Filter reservations by date range
    df, start_dt, end_dt = filter_dates(df, start_date, end_date)
    
    # Generate suggestions
    suggestions = suggest_reservations_strict_no_repeat(df, allow_repeats)
    
    # Prepare output for Excel
    generate_suggestion_output(suggestions, start_dt, end_dt)

if __name__ == "__main__":
    main()
