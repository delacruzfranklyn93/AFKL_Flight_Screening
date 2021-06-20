from bs4 import BeautifulSoup as bs
import requests
import pymongo
from webdriver_manager.chrome import ChromeDriverManager
from splinter import Browser
import pandas as pd
import json
import html5lib
import time
import glob


# setup splinter
executable_path = {'executable_path': ChromeDriverManager().install()}
browser = Browser('chrome', **executable_path, headless=False)


# Setup the URL to visit
url = 'https://aflsbkg.airfrance.fr/'

# Visit the URL
browser.visit(url)


# Store origin and Destination for Airfrance and KLM
AF_flight = ["ORD", "CDG"]
KL_flight = ["ORD", "AMS"]

# Store the date Variable (day, month, year)
day = list(map(int, input("What day(s) do you wish to screen ").split(",")))
month = input("Input the month in 3 word format (Ex = Apr) ").title()
year = "2021"


# navigate to the correct webpage for CSV download
browser.links.find_by_partial_text('Booking').click()
browser.links.find_by_partial_text('Search').click()

time.sleep(2.00)

# define functions being used.
def af_flights():
    # fill the flight number and date input field
    browser.fill("segment.segOrigin", f"{AF_flight[0]}")
    browser.fill("segment.segDestination", f"{AF_flight[1]}")
    browser.fill("bookingSearch.legDepartureDate", f"{day[0]}/{month}/{year}")

    # filter the search for the flight needed
    browser.links.find_by_partial_text('Filter').click()

    time.sleep(3.00)

    # Visit inital page and scrape the first page data
    html = browser.html
    soup = bs(html, 'html.parser')
    table = soup.find_all('table', class_='listTable')
    df = pd.read_html(str(table))[0]

    # set a number variable to specify to splinter which page it should click and visit
    num = 2

    # Create a for loop to visit the other pages of data and concat with original df
    for y in range(10):
        try:
            browser.click_link_by_partial_href(
                f'newbookListPagingProcess.do?page={num}')
            html1 = browser.html
            soup1 = bs(html1, 'html.parser')
            table1 = soup1.find_all('table', class_='listTable')
            df2 = pd.read_html(str(table1))[0]
            df = pd.concat([df, df2], ignore_index=True)
            num += 1
        except:
            break

    # drop the unamed column
    AF = df[(df.Prefix == '006') | (df.Prefix == '057')].drop(
        ['Unnamed: 0'], axis=1)
    return(AF)


def kl_flights():

    browser.links.find_by_partial_text('Booking').click()
    browser.links.find_by_partial_text('Search').click()

    time.sleep(3.00)

    # fill the flight number and date input field
    browser.fill("segment.segOrigin", f"{KL_flight[0]}")
    browser.fill("segment.segDestination", f"{KL_flight[1]}")
    browser.fill("bookingSearch.legDepartureDate", f"{day[0]}/{month}/{year}")

    # filter the search for the flight needed
    browser.links.find_by_partial_text('Filter').click()

    time.sleep(3.00)

    # Visit inital page and scrape the first page data
    html = browser.html
    soup = bs(html, 'html.parser')
    table = soup.find_all('table', class_='listTable')
    df = pd.read_html(str(table))[0]

    # set a number variable to specify to splinter which page it should click and visit
    num = 2

    # Create a for loop to visit the other pages of data and concat with original df
    for y in range(10):
        try:
            browser.click_link_by_partial_href(
                f'newbookListPagingProcess.do?page={num}')
            html1 = browser.html
            soup1 = bs(html1, 'html.parser')
            table1 = soup1.find_all('table', class_='listTable')
            df2 = pd.read_html(str(table1))[0]
            df = pd.concat([df, df2], ignore_index=True)
            num += 1
        except:
            break

    # drop the unamed column and return the KL dataframe
    KL = df[(df.Prefix == '057') | (df.Prefix == '074')].drop(
        ['Unnamed: 0'], axis=1)
    return KL


# call functions go get the individual flight dataframes.
AF = af_flights()
KL = kl_flights()

# concat the 2 flight dataframes into the final one for filtering
df_final = pd.concat([AF, KL], ignore_index=True)


# Filter the Dataframe

# Select the columns you want to display and store in a list
columns = ["Prefix", "AWB Number", "Origin", "Destination", "Commodity",
           "Product", "Pieces", "Weight", "Volume", "Issuer", "Flight Info"]

# Filter the AWB's by  weight and volume
df_final = df_final[(df_final.Weight.astype('float') > 1000) & (
    df_final.Volume.astype("float") > 10.00)][columns]

# Filter the AWB's by product
df_final = df_final[~df_final.Product.str.contains(
    "S50|S51|S52|S53")].sort_values('Flight Info').reset_index(drop=True)


# create a new dataframe to append the data from df_final and add spaces and format
df_test = pd.DataFrame(columns=columns)

# append an empty row for csv formating.
df_test = df_test.append(pd.Series(name=" ")).fillna("")

# append the first flight that it shows
df_test = df_test.append(pd.Series(name=df_final["Flight Info"][0])).fillna("")

# define the past flight
past_flight = df_final["Flight Info"][0]

# iterate through df_final and append the table data
for index, row in df_final.iterrows():

    # if the flight has changed append a row with just the new flight to easily distinguish where a new flight starts
    if past_flight != row["Flight Info"]:
        df_test = df_test.append(pd.Series(name=" ")).fillna("")
        df_test = df_test.append(pd.Series(name=row["Flight Info"])).fillna("")
        df_test = df_test.append(row)

    # continue to append the data for that particular flight if its the same flight
    else:
        df_test = df_test.append(row)

    # change past flight variable to check if its the start of a new flight
    past_flight = row["Flight Info"]

print(df_test)

# save the dataframe to a CSV file for download.
df_test.to_csv("test.csv")
