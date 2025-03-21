from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from pandas import Timestamp  # Add this import
from utils import (
    clean_address, seo_tags, get_location_details, determine_property_type,
    generate_property_title, determine_location_type, find_main_amenities,
    find_famous_amenities, determine_primary_photo, get_sublocality,
    get_street_view_link, append_to_excel, gmaps
)

GOOGLE_MAPS_API_KEY = "AIzaSyDIRQDHrB5vKPXvhoZDAHLfzLyYdKmAeI4"

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file_path = request.form['file_path']

        try:
            # Read the Excel file
            df = pd.read_excel(file_path)

            # Validate required columns
            required_columns = ['address', 'Reserve Price', 'Auction Date', 'borrower', 'bank', 'possession_status']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Input file is missing one or more required columns: {required_columns}")

            results = []

            # Process each row in the DataFrame
            for _, row in df.iterrows():
                address = row['address']
                print(address)
                reserve_price = row['Reserve Price']
                auction_date = row['Auction Date']
                borrower = row['borrower']
                bank = row['bank']
                possession_status = row['possession_status']

                # Call utility functions to process the data
                cleaned_address, Area, MicroMarket, buildingname, super_clean_address, property_type_ind     = clean_address(address)
                seo_keyword, seo_title, seo_description = seo_tags(cleaned_address)
                details = get_location_details(super_clean_address)
                city, state, postal_code, latitude, longitude = details[1:6]
                property_type = determine_property_type(cleaned_address)
                property_title = generate_property_title(property_type, cleaned_address,super_clean_address)
                location_type = determine_location_type(property_type)
                main_amenities = find_main_amenities(latitude, longitude, GOOGLE_MAPS_API_KEY, property_type)
                famous_amenities = find_famous_amenities(latitude, longitude, GOOGLE_MAPS_API_KEY)
                primary_photo = determine_primary_photo(property_type, cleaned_address)
                locality = get_sublocality(gmaps, latitude, longitude)
                street_view = get_street_view_link(property_type, latitude, longitude)

                # Compile data for the row
                data = [
                    cleaned_address, property_type, property_title, city, state, postal_code,
                    latitude, longitude, location_type, street_view, main_amenities,
                    primary_photo, locality, seo_keyword, seo_title, seo_description,
                    Area, reserve_price, auction_date, borrower, bank, possession_status,address
                ]

                # Ensure data length matches expected number of columns
                if len(data) != 23:  # Update 22 to match the actual number of fields
                    raise ValueError(f"Data length mismatch: expected 23 fields, got {len(data)}")
             
                results.append(data)
            print(results)
            return render_template('index.html', data=results, success=True)

        except Exception as e:
            return render_template('index.html', error=f"Error: {str(e)}")

    return render_template('index.html')

@app.route('/append', methods=['POST'])
def append():
    try:
        # Get the form data and process it
        data = request.form.get('data')
        print("Updated Data :" +data)
        # Ensure data is not empty
        if not data:
            raise ValueError("No data provided for appending.")

        # Convert the data to a listsss
        data_list = eval(data)

        # Convert the data to a DataFrame
        df = pd.DataFrame([data_list], columns=[
            'Address', 'Property Type', 'Property Title', 'City', 'State', 'Pincode',
            'Latitude', 'Longitude', 'Location Type', 'Street View', 'Amenities',
            'Primary Photo', 'Locality', 'SEO Keyword', 'SEO Title', 'SEO Description',
            'Total Area', 'Reserve Price', 'Auction Date', 'Borrower', 'Bank', 'Possession Status'
        ])

        # Load the existing Excel file
        output_file_path = "F:/Hecta/Bulkoriginalazhar.xlsx"
        existing_df = pd.read_excel(output_file_path)

        # Append the new data to the existing DataFrame
        updated_df = pd.concat([existing_df, df], ignore_index=True)

        # Save the updated DataFrame back to the Excel file
        updated_df.to_excel(output_file_path, index=False)

        return render_template('index.html', success=True)
    except Exception as e:
        return render_template('index.html', error=f"Error: {str(e)}")

@app.route('/update', methods=['POST'])
def update():
    try:
        updated_data = request.form.to_dict()

        # Placeholder for updating logic
        # Example: Save updated_data to database or file
        print("Updated Data:", updated_data)

        return redirect(url_for('index'))
    except Exception as e:
        return render_template('index.html', error=f"Error: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
