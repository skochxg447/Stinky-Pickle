import os
import urllib.request, urllib.parse, urllib.error
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import ssl
import re
import json
import pyap
import streamlit as st
import pandas as pd
import subprocess
from api_key import api_key

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def find_dealer_name(short_body_text, short_footer_text, url):
    # First try the original regex pattern
    dealer_pattern = re.compile(r"©\s?(?:\d{4}\s)?\b[\w\s]+\b(?=[^\w\s]|[\s]{2})")
    
    # Check for dealer name in bottomtext first
    for line in short_footer_text:
        dealer_matches = dealer_pattern.findall(line)
        for match in dealer_matches:
            dealer_name = re.search(r"(?<=\d{4}\s)\b[\w\s]+\b", match.strip())
            if dealer_name:
                # st.write('Dealer Name:', dealer_name.group().strip())
                return dealer_name.group().strip()
    
    # If dealer name not found in bottomtext, check in text
    for line in short_body_text:
        dealer_matches = dealer_pattern.findall(line)
        for match in dealer_matches:
            dealer_name = re.search(r"(?<=\d{4}\s)\b[\w\s]+\b", match.strip())
            if dealer_name:
                # st.write('Dealer Name:', dealer_name.group().strip())
                return dealer_name.group().strip()
    
    # If the first pattern doesn't match any text, try the second pattern
    dealer_pattern = re.compile(r"[@]\s?(?:\d{4}\s)\b[\w\s]+\b(?=[^\w\s]|[\s]{2})")
    
    # Check for dealer name in bottomtext first
    for line in short_footer_text:
        dealer_matches = dealer_pattern.findall(line)
        for match in dealer_matches:
            dealer_name = re.search(r"(?<=\d{4}\s)\b[\w\s]+\b", match.strip())
            if dealer_name:
                # st.write('Dealer Name:', dealer_name.group().strip())
                return dealer_name.group().strip()
    
    # If dealer name not found in bottomtext, check in bodytext
    for line in short_body_text:
        dealer_matches = dealer_pattern.findall(line)
        for match in dealer_matches:
            dealer_name = re.search(r"(?<=\d{4}\s)\b[\w\s]+\b", match.strip())
            if dealer_name:
                # st.write('Dealer Name:', dealer_name.group().strip())
                return dealer_name.group().strip()

    #if all methodsfailed, failsafe for dealer_name is extracting name from url
    url_pattern = re.compile(r"(?:https?://)?(?:www\.)?([\w-]+)\.[a-z]+(?:/[^\s]*)?")
    match = url_pattern.search(url)
    if match:
        url_name = match.group(1)
        # st.write('Dealer:', url_name)
    return url_name

serviceurl = 'https://maps.googleapis.com/maps/api/geocode/json?address='

def find_address(short_body_text, short_footer_text, api_key):
    # First method: pyap
    for line in short_body_text:
        addresses = pyap.parse(line, country='US')
        for address in addresses:
            # Prepare the URL for the Google Maps Geocoding API
            url = serviceurl + urllib.parse.quote(address.full_address) + '&key=' + api_key
            # Send a request to the Google Maps Geocoding API and get the response
            response = urllib.request.urlopen(url)
            data = response.read().decode('utf-8')
            # Parse the response JSON and extract the components of the address
            result = json.loads(data)
            if result['status'] == 'OK':
                components = result['results'][0]['address_components']
                street_number = ''
                route = ''
                locality = ''
                administrative_area_level_1 = ''
                postal_code = ''
                for component in components:
                    if 'street_number' in component['types']:
                        street_number = component['long_name']
                    if 'route' in component['types']:
                        route = component['long_name']
                    if 'locality' in component['types']:
                        locality = component['long_name']
                    if 'administrative_area_level_1' in component['types']:
                        administrative_area_level_1 = component['short_name']
                    if 'postal_code' in component['types']:
                        postal_code = component['long_name']
                address = (street_number + ' ' + route)
                city = locality
                state = administrative_area_level_1
                ZIP = postal_code
                # st.write('Address:', address)
                # st.write('City:', locality)
                # st.write('State:', administrative_area_level_1)
                # st.write('ZIP code:', postal_code)
                return address, city, state, ZIP # Success! Exit the function

    # First method failed, try second method: address_pattern
   # Method 2: address pattern
    address_pattern = r'\d+\s+[a-zA-Z0-9.,# ]+\s+[a-zA-Z]{2}\s+\d{5}'
    addresses = []
    # Search for the pattern in the body text
    for line in short_body_text:
        matches = re.findall(address_pattern, line)
        addresses.extend(matches)
    # Search for the pattern in the footer text
    for line in short_footer_text:
        matches = re.findall(address_pattern, line)
        addresses.extend(matches)
    # Find the shortest address and st.write it
    if addresses:
        shortest_address = min(addresses, key=len)

        # Prepare the URL for the Google Maps Geocoding API
        url = serviceurl + urllib.parse.quote(shortest_address) + '&key=' + api_key

        # Send a request to the Google Maps Geocoding API and get the response
        response = urllib.request.urlopen(url)
        data = response.read().decode('utf-8')

        # Parse the response JSON and extract the components of the address
        result = json.loads(data)
        if result['status'] == 'OK':
            components = result['results'][0]['address_components']
            street_number = ''
            route = ''
            locality = ''
            administrative_area_level_1 = ''
            postal_code = ''
            for component in components:
                if 'street_number' in component['types']:
                    street_number = component['long_name']
                if 'route' in component['types']:
                    route = component['long_name']
                if 'locality' in component['types']:
                    locality = component['long_name']
                if 'administrative_area_level_1' in component['types']:
                    administrative_area_level_1 = component['short_name']
                if 'postal_code' in component['types']:
                    postal_code = component['long_name']
            address = (street_number + ' ' + route)
            city = locality
            state = administrative_area_level_1
            ZIP = postal_code
            # st.write('Address:', address)
            # st.write('City:', locality)
            # st.write('State:', administrative_area_level_1)
            # st.write('ZIP code:', postal_code)
            return(address, city, state, ZIP) # Success! Exit the function
    else:
        # st.write('Address: Not Found')
        # st.write('City: Not Found')
        # st.write('State: Not Found')
        # st.write('ZIP code: Not Found')
        return False, False, False, False,


# finding owner started, but no longer needed
# def find_owner(short_body_text, short_footer_text):
#     owner_pattern = re.compile(r'^.*?\bowner\b.*?$', re.IGNORECASE )
#     for line in short_body_text:
#         owner_match = owner_pattern.search(line)
#         if owner_match:
#             owner_words = owner_match.group().split()
#             # st.write(' '.join(owner_words))
#             return True

#     for line in short_footer_text:
#         owner_match = owner_pattern.search(line)
#         if owner_match:
#             owner_words = owner_match.group().split()
#             # st.write(' '.join(owner_words))
#             return True
#     else:
#         # st.write('Owner: Not Found')
#         return False


def find_phone_number(short_body_text):
    # Regular expression pattern to match phone numbers with optional extensions
    phone_pattern = re.compile(r'\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})(?:\s*(?:ext|x)\s*(\d+))?')
    # Look for phone numbers in the short body text
    for line in short_body_text:
        # Find all matches of the phone pattern in the line
        phone_matches = phone_pattern.findall(line)
        # Loop over each match
        for match in phone_matches:
            # Format the phone number with hyphens and an extension if present
            phone_number = '-'.join(match[:3])
            if match[3]:
                phone_number += f' ext. {match[3]}'
            # Return the formatted phone number if a match is found
            return phone_number
        # If no matches are found in the line, continue to the next line
        if not phone_matches:
            continue
        # Return False if no phone numbers are found in the short body text
        return False
    # If all lines have been searched and no matches found, return False
    else:
        # st.write('Phone Number: Not Found')
        return False

def find_website(url):
    # Return the URL passed as an argument
    # st.write('Website:', url)
    return url


def find_email(short_body_text):
    # Regular expression pattern to match email addresses
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    # Look for email addresses in the short body text
    for line in short_body_text:
        # Find all matches of the email pattern in the line
        email_matches = email_pattern.findall(line)
        # If at least one match is found, return the first match
        if email_matches:
            # st.write('Email:', email_matches[0], '\n')
            return email_matches[0]
    # If no matches are found, return False
    # st.write('Email: Not Found', '\n')
    return False

def pull_and_parse(local_url):
    site_content = urllib.request.urlopen(local_url, context=ctx).read()
    bsoup = BeautifulSoup(site_content, 'html.parser')

    short_body_text = []
    short_footer_text = []
    for body in bsoup.find_all('body'):
        body_text = body.get_text(separator=' ').strip()
        body_text = re.sub('\n+', ' ', body_text)
        body_text = re.sub('\t+', ' \t ', body_text)
        body_text = body_text.replace('\xa0', ' \xa0 ')
        short_body_text.append(body_text)

    for footer in bsoup.find_all('footer'):
        footer_text = footer.get_text(separator=' ').strip()
        footer_text = re.sub('\n+', ' ', footer_text)
        footer_text = re.sub('\t+', ' \t ', footer_text)
        footer_text = footer_text.replace('\xa0', ' \xa0 ')
        short_footer_text.append(footer_text)

    return short_body_text, short_footer_text, bsoup


def scraping_action(short_body_text, short_footer_text, url):

    dealer_name = find_dealer_name(short_body_text, short_footer_text, url)
    address, city, state, ZIP = find_address(short_body_text, short_footer_text, api_key)
    phone_number = find_phone_number(short_body_text)
    website = find_website(url)
    email = find_email(short_body_text)
    return dealer_name, address, city, state, ZIP, phone_number, website, email

def find_links(bsoup, url):
    links_found = bsoup('a')
    links_processed = set()
    about_contact_links = set()

    for tag in links_found:
        link = tag.get('href', None)
        if link and link.startswith('http') and link not in links_processed:
            links_processed.add(link)
            if 'contact' in link.lower() or 'about' in link.lower():
                about_contact_links.add(link)
        if link and link not in links_processed:
            if '/contact' in link.lower() or '/about' in link.lower():
                full_link = urljoin(url, link)  # normalize the URL
                about_contact_links.add(full_link)
            elif link.startswith("/pages/"):
                full_link = urljoin(url, link[1:])
                about_contact_links.add(full_link)

    return about_contact_links


    if not about_contact_links:
        # st.write('No about or contact us page found')
        ...
    else:
        # st.write(about_contact_links)
        return about_contact_links




def main():
    # prompt for a website from the user, and take off any trailing '/
    url = st.text_input('Input website: ').strip("/")
    # if the user clicks the button or hits enter, run the program
    if st.button("Extract Website") or url:

        st.write('Retrieving:', url, '\n')
        found_all_info_first_time = False
        # a nice loading circle
        with st.spinner(text="In progress..."):
            try: 
                short_body_text, short_footer_text, bsoup = pull_and_parse(url)
                dealer_name, address, city, state, ZIP, phone_number, website, email = scraping_action(short_body_text, short_footer_text, url)
                # out_table = scraping_action(short_body_text, short_footer_text, url)
                if all((dealer_name, address, city, state, ZIP, phone_number, website, email,)):
                    found_all_info_first_time = True
            except:
                st.write("Invalid URL. Please try again.")
                if st.button('Open CSV File'):
                    subprocess.call(('open', 'out_df.csv'))
                return

        # st.write(dealer_name, address, phone_number, website, email)
        found_all_info = False

        # if all info not found on first page, try finding about and/or contact links on that page 
        if not found_all_info_first_time:
            about_contact_links = find_links(bsoup, url)

            # for every contact or about page found, look for more information on that page
            for link in about_contact_links:

                # if we flag was changed to true exit loop
                if found_all_info:
                    break
                short_body_text, short_footer_text, bsoup = pull_and_parse(link)

                # check the if the dealer name is falsey, if it is - try to find it
                if not dealer_name:
                    dealer_name = find_dealer_name(short_body_text, short_footer_text, link)

                # check the if any of the address areas are falsey, if they are - try to find them all again
                if not (address and city and state and ZIP):
                    address, city, state, ZIP = find_address(short_body_text, short_footer_text, api_key)

                # check the if the phone_number is falsey, if it is - try to find it
                if not phone_number:
                    phone_number = find_phone_number(short_body_text)

                # check the if the email is falsey, if it is - try to find it
                if not email:
                    email = find_email(short_body_text)
                # if all variables were found turn flag to true
                if dealer_name and address and phone_number and website and email:
                    found_all_info = True

        #setting owner name to empty string (to add another column to csv)
        owner_name = ''
        if found_all_info or found_all_info_first_time:
            st.write(f'all info found for {url}')
            # st.write('Dealer:', dealer_name)
            # st.write('Address:', address)
            # st.write('City:', city)
            # st.write('State:', state)
            # st.write('ZIP code:', ZIP)
            # st.write('Email:', email)
        else:
            st.write(f'not all info found for {url}')
            # st.write('Dealer:', dealer_name)
            # st.write('Address:', address)
            # st.write('City:', city)
            # st.write('State:', state)
            # st.write('ZIP code:', ZIP)
            # st.write('Email:', email)

        out_row = [dealer_name or '', address or '', city or '', state or '', ZIP or '', owner_name or '', phone_number or '', website or '', email or '']
        columns = ["Dealer Name", "Address", "City", "State", "ZIP", "Owner", "Phone Number", "Website", "Email"]
        out_table = pd.DataFrame(
                        [out_row],
                        columns=columns,
                    )
        if "saved_table" in st.session_state:
            out_table = pd.concat([st.session_state["saved_table"], out_table], ignore_index=True).drop_duplicates()
        st.session_state["saved_table"] = out_table
        st.dataframe(out_table)
        out_path = "out_df.csv"
        if not os.path.exists(out_path):
            out_table.to_csv(out_path, index=False)  # exclude index column from the saved file
        else:
            in_df = pd.read_csv(out_path)
            out_df = pd.concat([in_df, out_table], ignore_index=True)
            out_df = out_df.drop_duplicates(subset="Website")
            out_df.to_csv(out_path, index=False)  # exclude index column from the saved file
    if st.button('Open CSV File'):
        subprocess.call(('open', 'out_df.csv'))
main()



