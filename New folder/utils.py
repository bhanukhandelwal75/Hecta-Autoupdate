import googlemaps
import random
import pandas as pd
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import requests
import math
from collections import defaultdict
import re

#AIzaSyB2H5MYCIr0_UscY6QOvpWqlVWHxuDP5bo Nabeel bhai GEMINI KEY Cost include
#AIzaSyDwjfsJ58iNBgql__r0bBPe51CNZKbB_l0 #vijay key

genai.configure(api_key="AIzaSyB2H5MYCIr0_UscY6QOvpWqlVWHxuDP5bo")  # Gemini Flash API key
model = genai.GenerativeModel("gemini-1.5-flash")

gmaps = googlemaps.Client(key='AIzaSyDIRQDHrB5vKPXvhoZDAHLfzLyYdKmAeI4')

def clean_address(address):
    """
    Function to clean and structure the given address using AI intelligence.
    """
    super_clean_address="" 
    property_type_ind=None

    prompt = (
        f"Your task is to clean and structure the following address into a single-line format for easy identification and navigation.\n"
        f"---\n"
        f"### **Rules for Cleaning:**\n"
        f"- **DO NOT** add extra words like 'Formatted Address:' or 'Clean Address:' in the response.\n"
        f"- **DO NOT** include PIN codes, state names, administrative divisions like tehsil, district, taluka, village, or borrower's name.\n"
        f"- **KEEP ONLY ESSENTIAL IDENTIFIERS** needed to locate the property. Ensure no important details are removed.\n"
        f"- Please Before finalizing, verify that intermediate locations like sub-cities or talukas are not removed.\n"
        f"- If a House No. is present in the address (e.g., House No.125, Municipal House No.10, etc.), then DO NOT include Survey No., Plot No., Khasra No., or similar land identifiers in the final cleaned address. If Municipial House No.' is explicitly mentioned, then remove 'Survey No.' completely from the final address.Do not include Survey No. if 'House No.' is present.\n"
        f"- If 'Gala No.', 'Shop No.', or any commercial unit identifier is present in the address, it must be retained in the final cleaned address.\n."
        f"- The address must include identifiers like Plot No, Survey No, SF, Gat No, etc., if present.\n"
        f"\n"
        f"### **Rules for Different Property Types:**\n"
        f"- **FLATS / APARTMENTS** → Include: **Flat No, Floor, Block No.(If given), Phase(If given), Building Name, Sub-localities name(if given), Locality, City** in the final cleaned address. Remove: **Survey No, Khasra No, Plot No.**\n"
        f"- **PLOTS / HOUSES / ROW HOUSES** → Include: **Plot No, Block No, House No, Locality, City**. Keep identifiers like 'Plot No' and 'Block No' if given.\n"
        f"- For agricultural land and plot there is khasra and khatoni no ,use your intelligence whether to keep it or not.\n"
        f"- Dont miss anything which led to confusion.\n"
        f"- **COMMERCIAL PROPERTIES** → Include: **Shop No, Floor, Building Name, Market Name, Locality, City**.\n"
        f"- **VACANT LAND** → Include: **Plot No, Block No, Locality, City**. Remove extra legal terms but **keep location-relevant identifiers.**\n"
        f"\n"
        f"### **Additional Extraction:**\n"
        f"- Extract the **Area** of the property (e.g., square feet or square meters or square Yards or Acres), and store it as a variable. If it is carpet area, mark it as **CA**, if built-up area, mark it as **BUA**.\n"
        f"- Identify the **MicroMarket** (if given) and extract it separately.\n"
        f"- If the **Building Name or Society Name** is mentioned (for Flats, Apartments, or Villas), it must be included naturally in the cleaned address.\n"
        f"- Additionally, create a new variable called **Super Clean Address**, which only includes: Building Name (if given), Society Name (if given), Area Name(s), Locality, City, State. Use your intellegence to give these details in that order right.This will be used for geolocation purposes. Make sure not to miss Building name if given.\n"
        f"- Use AI to determine and classify the **Property Type** as one of the following:\n"
        f"  - Residential Flat\n"
        f"  - Residential House/Building\n"
        f"  - Residential Plot\n"
        f"  - Vacant Land\n"
        f"  - Commercial Shop/Retail Space\n"
        f"\n"
        f"---\n"
        f"**Address to Clean:** {address}\n"
        f"Provide ONLY the cleaned address in a structured format without unnecessary symbols or formatting."

    )

    while True:
        
        try:
            
            response = model.generate_content(prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH, 
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH
                })
            response_text = response.text.strip()
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)

    
    Area,MicroMarket,buildingname = "","",""
    
    
    cleaned_lines = []
    lines = response_text.strip().split("\n")
    for line in lines:
        if "Area:" in line:
            Area = line.split(":", 1)[-1].strip().strip('*').strip()
        elif "MicroMarket:" in line:
            MicroMarket = line.split(":", 1)[-1].strip()
        elif "Building Name:" in line:
            buildingname = line.split(":", 1)[-1].strip()
        elif "Super Clean Address:" in line:
            super_clean_address = line.split(":", 1)[-1].strip()
        elif "Property Type:" in line:
            property_type_ind = line.split(":", 1)[-1].strip()
        else:
            cleaned_lines.append(line)
    
    cleaned_address = " ".join(cleaned_lines)

    if not super_clean_address:
        address_parts = cleaned_address.split(",")
        if len(address_parts) >= 2:
            super_clean_address = f"{address_parts[-2].strip()}, {address_parts[-1].strip()}"
        else:
            super_clean_address = cleaned_address.strip()
    if not property_type_ind:
        address_lower = cleaned_address.lower()
        if 'f no' in address_lower or 'f.no' in address_lower or 'flat' in address_lower:
            property_type_ind = "Residential Flat"
        elif ('row house' in address_lower or 'house' in address_lower or 'house no' in address_lower or 'door' in address_lower) and \
             ('plot no' in address_lower or 'Sy No' in address_lower or 'survey no' in address_lower or 'Sy' in address_lower):
            property_type_ind = "Residential House/Building"
        elif any(keyword in address_lower for keyword in ['house', 'door', 'row house', 'house no', 'door no']):
            property_type_ind = "Residential House/Building"
        elif any(keyword in address_lower for keyword in ['plot', 'sy no', 'survey no', 'katha no', 'khasra']):
            property_type_ind = "Residential Plot"
        elif any(keyword in address_lower for keyword in ['door', 'asset no', 'house', 'row house']):
            property_type_ind = "Residential House/Building"
        elif 'bungalow' in address_lower:
            property_type_ind = "Residential Bungalow"
        elif 'farm' in address_lower:
            property_type_ind = "Residential Farm House"
        elif 'villa' in address_lower:
            property_type_ind = "Villa"
        elif 'office' in address_lower:
            property_type_ind = "Commercial Office Space"
        elif 'shop' in address_lower:
            property_type_ind = "Commercial Shop/Retail Space"
        elif 'warehouse' in address_lower:
            property_type_ind = "Warehouse"
        elif 'showroom' in address_lower:
            property_type_ind = "Commercial Showroom"
        elif 'land' in address_lower or 'vacant land' in address_lower:
            property_type_ind = "Land and Building"
        else:
            property_type_ind = "Residential Plot"  # Default fallback
        
        

        
    
    return cleaned_address, Area, MicroMarket, buildingname, super_clean_address, property_type_ind 
    
    return cleaned_address, Area, MicroMarket, buildingname, super_clean_address, property_type_ind    
        
        
    
    # Reconstruct the cleaned address without Area, MicroMarket, and Building Name
    cleaned_address = " ".join(cleaned_lines)
    if buildingname and "Building Name" in cleaned_address:
        
    
        pattern = rf"Building Name:?\s*{re.escape(buildingname)}"
    
    # Remove the "Building Name" and its value from the cleaned_address
        cleaned_address = re.sub(pattern, "", cleaned_address).strip()
    
    
        cleaned_address = re.sub(r"\s{2,}", " ", cleaned_address).strip(", ").strip()
    
    
    
    return cleaned_address, Area, MicroMarket, buildingname, super_clean_address, property_type_ind



    
    
            
            
            
        
            
            
             
        


def determine_property_type(cleaned_address):
    """
    Function to determine the property type based on the cleaned address.
    """
    
    address_lower = cleaned_address.lower()

    if 'f no' in address_lower or 'f.no' in address_lower or 'flat' in address_lower:
        return "Residential Flat"
    if ('row house' in address_lower or 'house' in address_lower or 'house no' in address_lower or 'door' in address_lower) and ('plot no' in address_lower or 'Sy No' in address_lower or 'survey no' in address_lower or 'Sy' in address_lower):
        return "Residential House/Building"       
    if any(keyword in address_lower for keyword in ['house', 'door', 'row house', 'house no', 'door no']):
        return "Residential House/Building"
    elif 'plot' in address_lower or 'sy no' in address_lower or 'survey no' in address_lower or 'katha no' in address_lower or 'khasra' in address_lower:
        return "Residential Plot"
    elif 'Door' in address_lower or 'asset no' in address_lower or 'house' in address_lower or 'row house' in address_lower:
        return "Residential House/Building"
    elif 'Bungalow' in address_lower:
        return "Residential Bungalow"
    elif 'farm' in address_lower:
        return "Residential Farm House"
    elif 'villa' in address_lower:
        return "Villa"
    elif 'office' in address_lower:
        return "Commercial Office Space"
    elif 'shop' in address_lower or 'Shop' in address_lower:
        return "Commercial Shop/Retail Space"
    elif 'warehouse' in address_lower:
        return "Warehouse"
    elif 'showroom' in address_lower:
        return "Commercial Showroom"
    elif 'land' in address_lower or 'vacant land' in address_lower:
        return "Land and Building" 
    
    
     
    return "Residential Plot"


def seo_tags(cleaned_address):
    
    prompt_template = (
                    f"Generate effective SEO tags (SEO Keyword, SEO Title, and SEO Description) for the given property address. "
                    f"The property is for sale and located in a residential area. Ensure the tags are structured well for marketing purposes.\n\n"
                    f"### Key Instructions:\n"
                    f"- Focus on property-specific details (type, location, features).\n"
                    f"- Avoid generic or promotional phrases (e.g., 'Explore the possibilities').\n"
                    f"- Aviod saying Insert key features like number of bedrooms/bathrooms, size, amenities, etc. here, e.g.,\n"
                    f"- Keep the output professional, concise, and attractive for potential buyers.\n\n"
                    f"- Avoid generic or promotional phrases (e.g., 'Explore the possibilities' or 'Contact us').\n"
                    f"### Additional Guidelines:\n"
                    f"-SEO Title:\n"
                    f"- Optimal Length: 50-60 characters.\n"
                    f"- Titles longer than 60 characters may get truncated in search results.\n\n"
                    f"-SEO Description:\n"
                    f"- Optimal Length: 150-160 characters.\n"
                    f"- Descriptions longer than 160 characters may get cut off in search results.\n"
                    f"-Avoid Prime location, close to [mention nearby landmarks or conveniences].  Contact us today!\n\n"
                    f"-When you display the seo tags , dont use ** this sign before seo keyword, seo title , seo description.\n"
                    f"-Key Considerations:\n"
                    f"- Relevance: Ensure the title and description are relevant to the property address.\n"
                    f"- Keyword: Naturally include important keywords related to the property.\n"
                    f"- Compelling Copy: Write engaging and click-worthy descriptions.\n\n"
                    f"### Address:\n"
                    f"{cleaned_address}\n\n")
    
    while True:
        try:
            response = model.generate_content(prompt_template,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH, 
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH
                })
              # Debugging the output
            
            #print(response.text)
            # Initialize variables
            seo_keyword, seo_title, seo_description = "", "", ""
            
            
            lines = response.text.strip().split("\n")
            for line in lines:
                if "SEO Keyword:" in line:
                    seo_keyword = line.split(":",1)[-1].strip()
                elif "SEO Title:" in line:
                    seo_title = line.split(":",1)[-1].strip()
                elif "SEO Description:" in line:
                    seo_description = line.split(":",1)[-1].strip()
            
            
            
            return seo_keyword, seo_title, seo_description
        
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)





def generate_property_title(property_type_ind, cleaned_address,super_clean_address):
    """
    Function to generate the property title with proper area structure.
    """
    
    locality = "Unknown Area"
    city = "Unknown City"
    buildingname = "Unknown Area"
    area_1 = "Unknown Area 1"
    area_2 = "Unknown Area 2"
    

    parts = cleaned_address.split(',')

    if len(parts) >= 3:
        area_1 = parts[-3].strip()
        area_2 = parts[-2].strip()
        city = parts[-1].strip()

        
        if property_type_ind == "Residential Flat" and len(parts) > 2:
            buildingname = parts[2].strip()

    
    if city.lower() == "delhi":
        city = "New Delhi"
        
    for part in parts:
        part = part.strip()
        if any(keyword in part.lower() for keyword in ["apartment", "complex", "residency"]):
            buildingname = part
            break
            
    if buildingname == area_1:
        buildingname = ""
        
    # Construct property title
    if property_type_ind == "Residential Flat":
        title_parts = [buildingname, area_1, area_2, city]
        title_parts = [part for part in title_parts if part] 
        return f"{property_type_ind} in {super_clean_address}"
    
    if property_type_ind == "Residential House/Building":
         return f"Independent House in {super_clean_address}"

    
    return f"{property_type_ind} in {super_clean_address}"



def get_location_details(super_clean_address):
    """
    Function to get geolocation details using the Google Maps API.
    """
    geocode_result = gmaps.geocode(super_clean_address)
    
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        address_components = geocode_result[0]['address_components']
        
        latitude = location['lat']
        longitude = location['lng']
        
        postal_code = city = state = None

        
        
        
        for component in address_components:
            if 'postal_code' in component['types']:
                postal_code = component['long_name']
            if 'locality' in component['types']:
                city = component['long_name']
            if 'administrative_area_level_1' in component['types']:
                state = component['long_name']
                
        if city == "Delhi":
            city = "New Delhi"
            state = "Delhi"
            
        
        
        if not postal_code:
            reverse_geocode_result = gmaps.reverse_geocode((latitude, longitude))
            if reverse_geocode_result:
                for component in reverse_geocode_result[0]['address_components']:
                    if 'postal_code' in component['types']:
                        postal_code = component['long_name']
                    if 'locality' in component['types']:
                        city = component['long_name']
                    if 'administrative_area_level_1' in component['types']:
                        state = component['long_name']
        
        
        return (super_clean_address, city, state, postal_code, latitude, longitude)
    else:
        print("Exact address not found. Providing approximate coordinates.")
        return (super_clean_address, None, None, None, 0.0, 0.0)




def get_street_view_link(property_type,latitude, longitude):
    """
    Function to generate a Google Street View iframe using latitude and longitude.
    """
    
    
    
    
    base_url = "https://www.google.com/maps/embed/v1/streetview" 
    
    
    api_key = "AIzaSyDIRQDHrB5vKPXvhoZDAHLfzLyYdKmAeI4"

    
    iframe_url = f"{base_url}?key={api_key}&location={latitude},{longitude}&heading=0&pitch=0&fov=90"

    #If you want to give street view to all , then remove condition , and property tupe argument in function and when we pass  , remvome it from display data ,function     
    # Return the iframe code
    if property_type == "Residential Flat":
        iframe_code = (
        f'<iframe src="{iframe_url}" width="400" height="300" style="border:0;" '
        f'allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>'
        )
        return iframe_code
    else:
        return None



def haversine(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points on the Earth's surface."""
    R = 6371  # Radius of the Earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def find_main_amenities(lat, lon, api_key, property_type):
    """
    Find main amenities: CBSE schools, hospitals, malls, D-Mart.
    Adjust output format based on property type.
    """
    amenities = []
    formatted_amenities = []
    
    
    response = requests.get(f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=5000&keyword=cbse+school&key={api_key}")
    results = response.json().get('results', [])
    if results:
        place = results[0]
        distance = haversine(lat, lon, place['geometry']['location']['lat'], place['geometry']['location']['lng'])
        amenities.append((distance, place['name'], "CBSE School"))

    
    response = requests.get(f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=5000&type=hospital&key={api_key}")
    results = response.json().get('results', [])
    if results:
        place = results[0]
        distance = haversine(lat, lon, place['geometry']['location']['lat'], place['geometry']['location']['lng'])
        amenities.append((distance, place['name'], "Hospital"))

    
    response = requests.get(f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=5000&type=shopping_mall&key={api_key}")
    results = response.json().get('results', [])
    if results:
        place = results[0]
        distance = haversine(lat, lon, place['geometry']['location']['lat'], place['geometry']['location']['lng'])
        amenities.append((distance, place['name'], "Mall"))

    # D-Mart Stores/mart
    response = requests.get(f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=5000&keyword=D-Mart&key={api_key}")
    results = response.json().get('results', [])
    if results:
        place = results[0]
        distance = haversine(lat, lon, place['geometry']['location']['lat'], place['geometry']['location']['lng'])
        amenities.append((distance, place['name'], "D-Mart"))

    
    amenities.sort(key=lambda x: x[0])

    # Format amenities based on property type
    if property_type == "Residential Flat":
        
        formatted_amenities = [f"{round(amenity[0], 1)} km to {amenity[1]} ({amenity[2]})" for amenity in amenities]
    else:
        
        generic_phrases = ["Close to", "Near by"]
        for i, amenity in enumerate(amenities[:4]):  
            phrase = generic_phrases[i % len(generic_phrases)]  
            formatted_amenities.append(f"{phrase} {amenity[1]} ({amenity[2]})")

    return " | ".join(formatted_amenities)


def append_to_excel(data, filename="F:/Hecta/Bulkoriginalazhar.xlsx"):
    """
    Function to append data to an Excel file.
    """
    try:
        existing_data = pd.read_excel(filename, engine='openpyxl')
    except FileNotFoundError:
        existing_data = pd.DataFrame(columns=['Address', 'Property Type', 'Property Title', 'City', 'State', 'Pincode', 'Latitude', 'Longitude', 'Location Type', 'Street View', 'Amenities','Primary Photo','Locality','SEO Keyword','SEO Title','SEO Description','area','super_clean_address','property_type_ind','reserve_price','auction_date','borrower','Bank','possession_status'])
    new_data = pd.DataFrame(data, columns=['Address', 'Property Type', 'Property Title', 'City', 'State', 'Pincode', 'Latitude', 'Longitude', 'Location Type', 'Street View', 'Amenities','Primary Photo','Locality','SEO Keyword','SEO Title','SEO Description','area','super_clean_address','property_type_ind','reserve_price','auction_date','borrower','Bank','possession_status'])
    
    updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    updated_data.to_excel(filename, index=False, engine='openpyxl')


def find_famous_amenities(lat, lon, api_key):
    """Find famous amenities: metro stations, railway stations, bus stands, colleges, hotels, restaurants, IT parks, and other places."""
    famous_amenities = defaultdict(list)
    types = [
        ("subway_station", "Metro Station"),  
        ("train_station", "Railway Station"), 
        ("bus_station", "Bus Stand"),         
        ("university", "College"),            
        ("hotel", "Hotel"),                   
        ("restaurant", "Restaurant"),         
        ("park", "IT/Knowledge Park"),        
        ("stadium", "Other Points of Interest"), 
        ("point_of_interest", "Other Points of Interest")  
    ]
    
    # Search for each type within a 7 km radius
    for place_type, display_name in types:
        response = requests.get(f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=7000&type={place_type}&key={api_key}")
        results = response.json().get('results', [])
        
        for place in results:
            # Calculate distance of the place from the user's coordinates
            distance = haversine(lat, lon, place['geometry']['location']['lat'], place['geometry']['location']['lng'])
            
            # Only include places that are within 7 km
            if distance <= 7:
                famous_amenities[display_name].append((distance, place['name'], place_type))

    
    for category in famous_amenities:
        famous_amenities[category].sort(key=lambda x: x[0])

    return famous_amenities

def display_table(data):

    if isinstance(data[0], list):
        hecta_data = [item for sublist in data for item in sublist]#i use list comprenshion 
    else:
        hecta_data = data

    latest_record = hecta_data[-1]
    """
    Function to display the result in a tabular format.
    """
    df = pd.DataFrame([latest_record], columns=['Address', 'Property Type', 'Property Title', 'City', 'State', 'Pincode', 'Latitude', 'Longitude', 'Location Type', 'Street View', 'Amenities','Primary Photo','Locality','SEO Keyword','SEO Title','SEO Description','area','super_clean_address','property_type_ind','reserve_price','auction_date','borrower','Bank','possession_status'])
    for index, row in df.iterrows():
        print(f"\nRecord {index + 1}:")
        print(f"  Address        : {row['Address']}")
        print(f"  Property Type  : {row['property_type_ind']}")
        print(f"  Property Title : {row['Property Title']}")
        print(f"  City           : {row['City']}")
        print(f"  State          : {row['State']}")
        print(f"  Pincode        : {row['Pincode']}")
        print(f"  Latitude       : {row['Latitude']}")
        print(f"  Longitude      : {row['Longitude']}")
        print(f"  Location Type  : {row['Location Type']}")
        print(f"  Street View    : {row['Street View']}")
        print(f"  Amenities      : {row['Amenities']}")
        print(f"  Primary Photo  : {row['Primary Photo']}")
        print(f"  Locality       : {row['Locality']}")
        print(f"  SEO Keyword    : {row['SEO Keyword']}")
        print(f"  SEO Title      : {row['SEO Title']}")
        print(f"  SEO Description: {row['SEO Description']}")
        print(f"  Area           : {row['area']}")
        print(f"  reserve_price  : {row['reserve_price']}")
        print(f"  auction_date   : {row['auction_date']}")
        print(f"  borrower       : {row['borrower']}")
        print(f"  Bank           :  {row['Bank']}")
        print(f"  possession_status :{row['possession_status']}")

        
        
        

def determine_location_type(property_type):
    """
    Function to determine the location type based on the property type.
    """
    # Fix: Residential Flat should always have location type as 'Exact'
    if property_type == "Residential Flat":
        return "Exact"
    elif property_type == "Residential Plot" or property_type == "Residential House/Building":
        return "Approx"
    else:
        return "Approx"

def determine_primary_photo(property_type, cleaned_address):
    """
    Function to determine the primary photo URL based on property type and cleaned address.
    """
    if property_type == "Residential Plot":
        return "https://hecta-website.s3.ap-south-1.amazonaws.com/2024/11/media/1731674068_975fb743e5dd31cd.jpg"
    elif property_type == "Residential House/Building" or "row house" in cleaned_address.lower():
        return "https://hecta-website.s3.ap-south-1.amazonaws.com/2024/11/media/1731734069_8b0b8742bf274c7f.jpg"
    elif property_type == "Land and Building":
        return "https://hecta-website.s3.ap-south-1.amazonaws.com/2024/11/media/1731741519_9dc0a56cc67c56ec.jpg"
    elif property_type == "Residential Builder Floor": 
        return "https://hecta-website.s3.ap-south-1.amazonaws.com/2024/12/media/1735536562_b6c993d1c1a18a8b.jpg"
    elif property_type == "Commercial Shop/Retail Space":
        return "https://hecta-website.s3.ap-south-1.amazonaws.com/2025/01/media/1736247989_3e36aed48fc77a4d.jpg"
    else:
        return None  
#FOR FLAT --- https://hecta-website.s3.ap-south-1.amazonaws.com/2025/01/media/1736853056_436b7aba32cebd62.jpg


#For localityI
import googlemaps
def initialize_gmaps(api_key="AIzaSyB2H5MYCIr0_UscY6QOvpWqlVWHxuDP5bo"):
    return googlemaps.Client(key=api_key)

# Function to check sub-locality using Reverse Geocoding
def get_sublocality(gmaps, latitude, longitude):
    reverse_geocode_result = gmaps.reverse_geocode((latitude, longitude))
    for result in reverse_geocode_result:
        for component in result['address_components']:
            if 'sublocality' in component['types']:
                return component['long_name']
    return None  # If no sub-locality found

# Function to search for nearby places (school, hospital, railway station)
def search_nearby_places(gmaps,latitude, longitude,radius=7000):
    places = {
        "school": [],
        "hospital": [],
        "railway_station": []
    }

    # Search for schools
    school_results = gmaps.places_nearby((latitude, longitude), radius=radius, type="school")
    if school_results.get('results'):
        places["school"] = school_results['results']

    # Search for hospitals
    hospital_results = gmaps.places_nearby((latitude, longitude), radius=radius, type="hospital")
    if hospital_results.get('results'):
        places["hospital"] = hospital_results['results']

    # Search for railway stations
    railway_results = gmaps.places_nearby((latitude, longitude), radius=radius, type="train_station")
    if railway_results.get('results'):
        places["railway_station"] = railway_results['results']
    
    #return places

# Function to get the area name based on the place's location
def get_area_name(gmaps, latitude, longitude):
    geocode_result = gmaps.reverse_geocode((latitude, longitude))
    for result in geocode_result:
        for component in result['address_components']:
            if 'locality' in component['types']:
                return component['long_name']
    return "Area Not Found"

# Main function to process the coordinates
def process_coordinates(gmaps, latitude, longitude):
    # Check for sub-locality
    locality = get_sublocality(gmaps, latitude, longitude)

    if locality:
        return locality

    # If no sub-locality found, search for nearby places
    nearby_places = search_nearby_places(gmaps, latitude, longitude)

    # If no schools, hospitals, or railway stations found, return a fallback area name
    if not any(nearby_places.values()):
        area_name = get_area_name(gmaps, latitude, longitude)
        locality=area_name
        return locality
    
    # Prioritize and return the first available point of interest
    for category in ["school", "hospital", "railway_station"]:
        if nearby_places[category]:
            first_place = nearby_places[category][0]
            area_name = get_area_name(gmaps, first_place['geometry']['location']['lat'], first_place['geometry']['location']['lng'])
            locality=area_name
            return locality

# Main execution to take input from the user and process the location
    gmaps = initialize_gmaps()
    # Take latitude and longitude as input from the use
    result = process_coordinates(gmaps, latitude, longitude)
    











def main():
    api_key = "AIzaSyDIRQDHrB5vKPXvhoZDAHLfzLyYdKmAeI4"    # Input Excel file details
    excel_path = input("Enter the full path to the Excel file: ").strip()
    
    
    
    try:
        df1 = pd.read_excel(excel_path)
    except FileNotFoundError:
        print(f"Error: File not found at {excel_path}. Please check the path and try again.")
        return

    
    required_columns = ['address', 'Reserve Price', 'Auction Date','borrower','bank', 'possession_status']
    if not all(col in df1.columns for col in required_columns):
        print("Error: The Excel file must contain the following columns: Address, Reserve Price, Auction Date.")
        return
    
    results = []  
    
    
    for _, row in df1.iterrows():
        try:
            address = row['address']
            reserve_price = row['Reserve Price']
            auction_date = row['Auction Date']
            borrower = row['borrower']
            Bank=row['bank']
            possession_status=row['possession_status']
            
            
    
   
            
        
        # Step 1: Clean the address
            cleaned_address, Area, MicroMarket, buildingname, super_clean_address, property_type_ind = clean_address(address)
            print(address)
            print()
            print(super_clean_address)
            seo_keyword, seo_title, seo_description  = seo_tags(cleaned_address)

        
        # Step 2: Get location details (city, state, pincode, latitude, longitude)
            details = get_location_details(super_clean_address)
            city = details[1]
            state = details[2]
            postal_code = details[3]
            latitude = details[4]
            longitude = details[5]
        
        # Step 3: Determine property type and title
            property_type = determine_property_type(cleaned_address)
            property_title = generate_property_title(property_type_ind, cleaned_address, super_clean_address)

        # Determine location type based on property type
            location_type = determine_location_type(property_type)

        # Step 4: Get main amenities
            main_amenities = find_main_amenities(latitude, longitude, api_key,property_type)
        #amenities_list = [f"{distance:.1f} km to {name} ({amenity_type})" for distance, name, amenity_type in main_amenities]

        #step4: 
        #street_view_cleaned_address = extract_clean_address(cleaned_address)
        
        # Step 5: Get famous amenities (within 7 km)
            famous_amenities = find_famous_amenities(latitude, longitude, api_key)

        # Step 5: Determine primary photo based on property type and cleaned address
            primary_photo = determine_primary_photo(property_type, cleaned_address)

        #STep 8: Locality
            locality = get_sublocality(gmaps, latitude, longitude)
        
        # Step 6: Prepare the data to display
            data = [[cleaned_address, property_type, property_title, city, state, postal_code, latitude, longitude, location_type , get_street_view_link(property_type,latitude, longitude),main_amenities , primary_photo , locality , seo_keyword , seo_title , seo_description, Area, super_clean_address,property_type_ind, reserve_price, auction_date,borrower,Bank,possession_status]]
            results.append(data)

        except Exception as e:
            print(f"Error processing row with Address '{address}': {e}")
            continue
        
        
        display_table(results)
        
    
        
        # Step 7: Ask for confirmation to append to Excel
        confirm = input("\nDo you want to append this data to the Excel file? (yes/no): ").strip().lower()
        if confirm == 'yes':
            append_to_excel(data)
            print("\nData has been appended to Bulkoriginalazhar.xlsx")
        else:
            print("\nData was not appended.")
        
        continue_input = input("\nDo you want to process another address? (yes/no): ").strip().lower()
        if continue_input != 'yes':
            break
    
    print("\nWelcome to Hecta Cataloging Automation. Have a good day!")

if __name__ == "__main__":
    main()

    #Code run successfully get it . hecta pipleline  used api gemini and geocode F:\Hecta\InputFileCatalouged.xlsx