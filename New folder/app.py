import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import requests
import os
import pandas as pd
import re
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill
from  db import create_connection
from hectalogging import log
import urllib.parse





def split_and_join(address):
    words = re.findall(r'\w+', address)  # Only extract word-like tokens
    return ' '.join(words)
    


def cleanse_borrower_name(name):
        titles = ['Mr', 'Ms', 'Mrs', 'Shri', 'Shrimati', 'M/s', 'M/S',
                  'Messers', 'Dr', 'Prof','Smt', 'M/s.',
                  "M'S.", "M's", "m's","Mis.","0","1","2","3","4","5","6","7","8","9","Property","property","(",")","no.","No."," No:2)"]
        for title in titles:
            name = name.replace(title + '.', '').replace(title + ' ', '')
        name = re.sub(r'\b[0-9]+\b', '', name)
        name = re.sub(r'\(?\s*Property\s*No\s*[:\-]?\s*\d+\)?', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\(?\s*No\s*[:\-]?\s*\d+\)?', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\bNo[:\-\s]*\)?', '', name, flags=re.IGNORECASE)
        name = re.sub(r"[^\w\s]", "", name)
    
        return name.strip()

    

def normalize_address(raw_address):
    """
    Normalizes an address:
    - Cleans spacing and punctuation.
    - Capitalizes major words, lowers minor words like 'of', 'and', etc.
    """
    # Remove punctuation
    address = re.sub(r'[^\w\s]', '', raw_address)
    # Replace multiple spaces with a single space
    address = re.sub(r'\s+', ' ', address)

    return address

def separate_words_and_numbers(text):
    return re.sub(r'(?<=\D)(?=\d)|(?<=\d)(?=\D)', ' ', text)



def get_existing_addresses(borrower_name, address, bank):
    """
    Function to get the existing addresses from the database
    """
    address = separate_words_and_numbers(address)
    encoded_address = urllib.parse.quote_plus(f"address:*{normalize_address(address)}*")
    borrower_filter = f"borrower:{cleanse_borrower_name(borrower_name)}"
    borrower_filter=borrower_filter.lower()
    fuzzy_borrower_name = " ".join([word + "~" for word in borrower_filter.split() if len(word)>2])

    bank_filter = f'bank:{bank}'   
    
    try:
        solr_url = (
            f"http://172.31.41.173:8983/solr/hectacore_latest/select"
            f"?indent=true"
            f"&q={encoded_address}"
            f"&fq={urllib.parse.quote_plus(fuzzy_borrower_name)}"
            f"&fq={urllib.parse.quote_plus(bank_filter)}"
            f"&fq=type:Prop"
            f"&defType=edismax"
            f"&qf=address"
            f"&rows=150"
            f"&fl=*,score"
        )    
        
        response = requests.get(solr_url)
        response.raise_for_status()
        # print("📦Solr Response for Addrerss:")
        # print(json.dumps(response.json(), indent=4))
        
        return response.json()

    except requests.RequestException as e:
        print(f"Error making API request: {e}")
        return None





def get_existing_borrowers(borrower_name, address, bank):
    """
    Function to get the existing borrowers from Solr and print the response.
    """
    
    if borrower_name is None or borrower_name.strip() == "":
        # print("Borrower name is empty")
        return None

    borrower_name = cleanse_borrower_name(borrower_name)
    fuzzy_borrower_name = " ".join([word + "~" for word in borrower_name.split() if len(word)>2])
    bank_filter = f'bank:{bank}'
    


    try:
        base_url = 'http://172.31.41.173:8983/solr/hectacore_latest/select'
        words_count = 2
        query = (
            f"{base_url}?indent=true"
            f"&q={requests.utils.quote(fuzzy_borrower_name)}"
            f"&defType=edismax"
            f"&mm={words_count}"
            f"&qf=borrower"
            f"&fq=type:Prop"
            f"&fq={requests.utils.quote(bank_filter)}"
            f"&rows=150"
            f"&wt=json"
            f"&fl=*,score"
        )
        

        
        response = requests.get(query)
        response.raise_for_status()
        
        
        # print("📦Solr Response for Borrower:")
        # print(json.dumps(response.json(), indent=4))
        
        return response.json()

    except requests.RequestException as e:
        print(f"❗Error making Solr request: {e}")
        return None


def borrower_clean_and_split(text):
    # Convert text to lowercase
    text = text.lower()
    
    # Split using regex: split on any non-word character (anything except a-z, A-Z, 0-9, _)
    words = re.split(r'[^\w]+', text)
    
    # Remove any empty strings from the list
    cleaned_words = set(filter(None, words))
    
    return cleaned_words

def clean_and_split(text):
    words = re.split(r'[^\w]+', text.lower())
    return set(filter(None, words))



def borrower_match_words(short_text, long_text):
    short_words = borrower_clean_and_split(short_text)
    long_words = borrower_clean_and_split(long_text)
    if not short_words:
        return 0.0
    matched = short_words.intersection(long_words)
    matched_ratio_ = len(matched) / len(short_words)
    return matched_ratio_


def match_words(short_text, long_text):
    short_words = clean_and_split(short_text.replace('Bangalore', 'Bengaluru').replace('bangalore', 'bengaluru').replace('BENGALURU', 'bengaluru'))
    long_words = clean_and_split(long_text.replace('Bangalore', 'Bengaluru').replace('bangalore', 'bengaluru').replace('BENGALURU', 'bengaluru'))
    if not short_words:
        return "0%"
    matched = short_words.intersection(long_words)
    matched_ratio = len(matched) / len(short_words)
    matched_ratio = f"{matched_ratio * 100:.2f}%"
    return matched_ratio

def is_property_match(doc_address, address):

    matched_ratio = match_words(doc_address, address)
    ratio_float = float(matched_ratio.strip('%'))
    # print(ratio_float)

    unit_keywords = ['shop', 'flat', 'office', 'unit','gala']
    

    def extract_unit_number(text, unit_type):
        text = text.lower()
        pattern = fr'{unit_type}\s*(?:no\.?|number)?\s*(\d+)'
        match = re.search(pattern, text)
        return match.group(1) if match else None

    # Apply unit number boost if applicable
    for unit in unit_keywords:
        raw_unit = extract_unit_number(address, unit)
        doc_unit = extract_unit_number(doc_address, unit)

        if raw_unit and doc_unit and raw_unit == doc_unit and ratio_float >= 75:
            ratio_float = ratio_float + 15
            break

    # Recalculate match ratio string and match flag after boost
    matched_ratio = f"{ratio_float:.2f}%"

    return matched_ratio 


def check_duplicate_db(property_json):
    connection=create_connection()
    cursor = connection.cursor()
    # Prepare the SQL query
    sql_query = "SELECT id, borrower_name,address FROM properties WHERE status=0 and stage in (1,3,4) and created_at >  NOW()  - INTERVAL 30 DAY"
    # Execute the query
    cursor.execute(sql_query)
    # Fetch all the results
    results = cursor.fetchall()

    id=None
    db_borrower_l=None
    db_address_l=None
    for row in results:
      db_id, db_borrower, db_address = row
      # Compare with the input property_json 
      borrower_score=0.0
      address_score="0%"
      try:
         
     
        if ( db_borrower is not None and property_json['borrower_name'] is not None):
            borrower_score = borrower_match_words(property_json['borrower_name'], db_borrower)
        else :
            borrower_score = 0.0

        if ( db_address is not None and property_json['property_description'] is not None):
            address_score = is_property_match(db_address, property_json['property_description'])
            address_score_float = float(address_score.strip('%'))
        else:
            address_score = "0%"
            address_score_float = float(address_score.strip('%'))
       
        if borrower_score > 0.6 and address_score_float / 100 > 0.6:
            id=db_id
            db_borrower_l=db_borrower
            db_address_l=db_address
      except Exception as e:
          log("ERROR","Error in checking duplicate properties in DB: " + str(e))
          log("ERROR" , db_borrower)
          log("ERROR", db_address)                
    
    cursor.close()        
    connection.close()

    return id, db_borrower_l, db_address_l

def check_duplicate(property_json):
    borrower_name = property_json['borrower_name']
    borrower_name = borrower_name.strip()
    address = property_json['property_description']
    log("INFO", f"Checking for duplicate borrowers and addresses. Borrower name: {borrower_name} Bank: {property_json['bank']} Address: {address}")
    address = split_and_join(address.lower())
    bank = property_json['bank']
    bank = bank.strip()

    existing_borrowers = get_existing_borrowers(borrower_name, address, bank)
    existing_addresses = get_existing_addresses(borrower_name, address, bank)

    if existing_addresses is not None and "response" in existing_addresses:
      max_score = existing_addresses["response"].get("maxScore", "")
    else:
        max_score = ""    
     
    max_score_borrower = existing_borrowers["response"].get("maxScore", "")

    borrower_docs = existing_borrowers['response'].get('docs', [])
    if existing_addresses and 'response' in existing_addresses:
       address_docs = existing_addresses['response'].get('docs', [])
    else:
        address_docs = []  # safe default: empty list

    borrower_map = {(doc.get('id'), doc.get('type')): doc for doc in borrower_docs}
    address_map = {(doc.get('id'), doc.get('type')): doc for doc in address_docs}

    common_keys = set(borrower_map.keys()) & set(address_map.keys())

    matched_candidates = [borrower_map[key] for key in common_keys]

    best_doc = None
    best_ratio = 0
    

    for doc in matched_candidates:
        ratio = is_property_match(doc['address'], address)
        if float(ratio.strip('%')) > best_ratio:
            best_ratio = float(ratio.strip('%'))
            best_doc = doc

    if best_doc:
        best_doc["max_score"] = max_score
        best_doc["max_score_borrower"] = max_score_borrower
        if best_ratio>=65:
            log("INFO","Duplicate property found in Solr index: "+str(best_doc["prop_id"]))
            best_doc['best_ratio'] = best_ratio/100
            best_doc['action'] = "update"
            status = "Matched"
            return best_doc
            
        else:
            log("INFO","Duplicate property found in Solr index but score is low: "+str(best_doc["prop_id"]))
            best_doc['best_ratio'] = best_ratio/100
            best_doc['action'] = "review"
            status = "Matched"
            return best_doc
        
    prop_id, db_borrower, db_address=check_duplicate_db(property_json)
    if (prop_id is not None):
        log("INFO","Duplicate property found in Drafts in DB: "+str(prop_id))
        property_json['action']="skip"
        property_json['prop_id']=prop_id
        property_json['draft_borrower']=db_borrower
        property_json['draft_address']=db_address
        return property_json
    
    log("INFO","NO Duplicate property found . Hence creating a new property")
    return None


