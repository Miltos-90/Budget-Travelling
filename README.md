# Budget-Travelling
Cost minimisation of hotel stays &amp; airplane tickets for a multi-destination round trip.
Hotel and air-ticket fares were scraped from Trivago and Skyscanner, respectively, and choice of hotels and flights for a 2 month round-trip was formulated as an optimisation problem and solved using PuLP

# Table of Contents
* [Introduction](#intro)
* [Getting the Data](#data_gathering)
    * [Searching for hotels](#hotel_gather)
    * [Searching for flights](#flight_gather)
    * [Putting the scrapers to work](#scraper_work)
    * [Results](#scrape_res)
* [Optimisation Problem](#opt_prob)
    * [Formulation](#formulation)
    * [PuLP Programming](#pulp)
* [Solution](#solution)


# Introduction

<a id="intro"></a>

The worst part of traveling abroad for holidays is that one has to arrange means of transport and book a hotel. But what if we could automate part of the process?

Suppose we have a list of destinations (multiple ones) in mind, and a predetermined holiday period. Normally, I would go online, and try to book hotels and flights to accomodate my holiday plan, always keeping cost in mind (unfortunately there's a limit to what I can afford). But what if my PC can answer this simple question: Given a list of destinations, can you find me the flights and hotels I need to book, in order to visit a subset of the destinations, as cheap as possible?

Sounds like an optimisation problem, right?

# Getting the Data
<a id="data_gathering"></a>

First things first, we need to define our destinations. Where would we like to go? Luckily, someone has already answered this for us: [Best places to travel in Europe - 2018](https://www.europeanbestdestinations.com/european-best-destinations-2018/).

So, the best destinations are the following:
- Wroclaw,
- Bilbao,
- Colmar, 
- Hvar, 
- Riga, 
- Milan, 
- Athens, 
- Budapest, 
- Lisbon, 
- Bohinj, 
- Prague, 
- Kotor, 
- Paris, 
- Vienna, 
- Amsterdam.

Next question is, when do we want to go on vacation? Let's assume that we have a month available between July 1st, up to and including August 1st.

## Searching for hotels
<a id="hotel_gather"></a>

Obviously, to answer the question at hand, we need to know how much it costs to stay in a hotel, at any one of the cities listed above, at any time between July 1st to August 1st. We can scrape the data we need from various websites available. Here, we'll use [Trivago](https://www.trivago.com/). The search page looks like the following:
![main_hotel](img/trivago_main.png)
Clearly, there are a few steps to take:
1. Fire up a browser (obviously)
2. Check for captchas or 'enable javascript' error messages (the latter tends to happen on Tor)
3. Set our country to USA (It's goof to ensure consistency of the text that appears on the website)
4. Set the currency to EUR
5. Enter the required destination
6. Select our check-in date from the drop-down menu
7. Select our check-out date from the dropdown menu
8. Grab the best offer

Of course, we have to repeat most steps to gather all the data we need. We'll also implement some 'waiting periods' in-between these actions, as there's no reason to strain the server with our requests. Let's write our scraper using Selenium and the Tor web browser (for info on getting Selenium to work nicely with Tor, check: https://stackoverflow.com/questions/15316304/open-tor-browser-with-selenium):

### Hotel Offer Web Scraper
<a id="hotel_scraper"></a>

First of all, let's instantiate our scraper class:


```python
from tbselenium.tbdriver import TorBrowserDriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from tbselenium.utils import start_xvfb, stop_xvfb

from datetime import datetime as dt
from datetime import timedelta
from time import sleep

from multiprocessing import Pool, cpu_count, Manager

from itertools import product
from functools import partial

import pandas as pd
import numpy as np
import pulp as plp

# Imports specifically for jupyter
import jdc

# Path for TOR
DRIVER_PATH = '/tor-browser/tor-browser_en-US/'

class Hotel_Scraper(object):
    
    def __init__(self):
        
        self.url = "https://www.trivago.com/"
        self.implicit_wait = 5 # Wait in between actions
        self.wait_for_elem = 20 # Wait up to 20 seconds for an element to appear, be clickable, etc.
    
```

Right. Now we need to write our functions that perform steps 1 - 8 above. Step 1 will be performed in the end. Let's begin with steps 2 - 4:


```python
%%add_to Hotel_Scraper

    # Check whether a captcha has appeared
    def is_captcha(self):
        
        try:
            css_selector_tag = 'main.main-content > section.pos-relative.clearfix > div.centerwrapper--narrow.m-0-auto > div.gutter-box.mb-gutter-doubled.bg-white.border-radius.opacity-high.ta-center > h2.h2'
            self.browser.find_element_by_css_selector(css_selector_tag)
            return True
        except:
            # No captcha mentioned
            return False


    # Check whether a 'enable javascript' msg has appeared
    def is_js_alert(self):
        
        try:
            # Try and get the alert on the top of the page
            css_selector_tag = 'body > span > div.alert.alert--info.alert--top > p.alert__message > a'
            alert            = self.browser.find_element_by_css_selector(css_selector_tag).get_attribute("href")
            # Does it say anything about javascript?
            if 'javascript' in alert:
                return True
        except:
            # No js. alert
            return False
```

The best thing we can do, if any of the two alerts appear is to refresh the page and hope they don't appear again. There must be something more efficient we can do, I didn't find it though. Let's write a small function to refresh the page:


```python
%%add_to Hotel_Scraper

    # Refresh on bot or js alert
    def refresh(self):
        
        # Keep refreshing until there's no javascript alert or a captcha
        while self.is_captcha() or self.is_js_alert():
            
            # Close the current browser
            self.browser.close()
            
            # Fire up a new browser
            self.browser = TorBrowserDriver(DRIVER_PATH)
            self.browser.implicitly_wait(self.implicit_wait) 
            self.browser.set_window_size(1024, 768)
            self.browser.get(self.url)
    
        return
```

Perfect. Next up, we need to set the country and currency. Pretty simple:


```python
 %%add_to Hotel_Scraper
    
    # Set country to USA
    def set_country(self):
        
        # Find the dropdown menu
        xpath_tag = "//select[contains(@id, 'select-country')]"
        country_btn = Select(self.browser.find_element_by_xpath(xpath_tag))
        
        # Set it to US
        country_btn.select_by_value("us")
        
        return
        
    # Set currency to EUR
    def set_currency(self):
        
        # Find the currency selector
        currency_btn = Select(self.browser.find_element_by_css_selector("select#currency"))
                                                                   
        # Set it to EURO
        currency_btn.select_by_value("EUR")
        
        # Wait a bit
        sleep(5)
        
        return
```

Right. Now we can start filling in our details. Let's begin with our destination. We need a function to take a string (destination) as input, and a boolean indicating if this is the first time we're searching something on the current session (some additional steps are needed):


```python
%%add_to Hotel_Scraper

    def enter_destination(self, destination, first_search):
        
        # Destination input
        css_selector_tag  = "input#horus-querytext"
        destination_input = self.browser.find_element_by_css_selector(css_selector_tag)
        destination_input.send_keys(destination)
        
        # Wait until the selection pop-up becomes available
        css_selector_tag = "div.ssg-suggestion__info"
        wait             = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, css_selector_tag)))
        
        if first_search:
            # Click tab twice and hit enter (move to the next input)
            destination_input.send_keys(Keys.TAB)
            destination_input.send_keys(Keys.TAB)
            destination_input.send_keys(Keys.ENTER)
        
        return
```

Next, we need functions to enter the check-in and check-out dates. After having some brief inspection of the page's HTML code, I decided its easy to combine both functions in one, as there are only some minor differences in the names of the buttons that have to be pressed, which will be given as inputs to the function. Moreover, we need to account for the fact that, if this is our first search in the session, we need to click on a few extra things:


```python
%%add_to Hotel_Scraper

    # Enter check_in date
    def enter_date(self, check_in_date, first_search, xpath_tag):
        
        if not first_search: 
            self.browser.find_element_by_xpath(xpath_tag).click()
            wait = WebDriverWait(self.browser, self.wait_for_elem)
            wait.until(ec.visibility_of_element_located((By.XPATH, xpath_tag)))
        
        # Get the month that appeared in the dropdown menu
        css_selector_tag = 'th#cal-heading-month.cal-heading-month > span'
        menu_month       = self.browser.find_element_by_css_selector(css_selector_tag).text
        
        # Parse it
        menu_month = dt.strptime(menu_month, "%B %Y").month
        
        # Parse check in date
        check_in_date_parsed = dt.strptime(check_in_date, "%d/%m/%Y")
        
        # Get the difference in months (i.e how many times to hit the button)
        delta = check_in_date_parsed.month - menu_month
        
        # Get the next month button
        css_selector_tag  = "button.cal-btn-next"
        next_month_button = self.browser.find_element_by_css_selector(css_selector_tag)
        
        # Click it an appropriate number of times
        for _ in range(delta):
            next_month_button.click()
        
        # Grab the calendar web element again (avoid stale reference error)
        css_selector_tag = "div.df_container_calendar"
        calendar_elem    = self.browser.find_element_by_css_selector(css_selector_tag)
        
        # Click on the right button
        xpath_tag = "//time[@datetime='" + check_in_date[-4:] + '-' + check_in_date[3:5] + '-'+ check_in_date[0:2] + "']"
        wait      = WebDriverWait(self.browser, self.wait_for_elem)
        
        wait.until(ec.visibility_of_element_located((By.XPATH, xpath_tag)))
        calendar_elem.find_element_by_xpath(xpath_tag).click()
        
        return
```

Next up, we need to fill in the room info. Namely, the number of adults:


```python
%%add_to Hotel_Scraper

    def enter_room_info(self, adults):
        
        # Depending on the IP, two different dropdown menus appear
        try:
            # Get the dropdown menu
            css_selector_tag = "ul.df_container_roomtype_selector.df_dropdown"
            room_menu        = self.browser.find_element_by_css_selector(css_selector_tag)
            
        except NoSuchElementException:
            # Get the current no. of adults
            xpath_tag      = "//input[contains(@id, 'adults-input')]"
            current_adults = self.browser.find_element_by_xpath(xpath_tag)
            current_adults = int(current_adults.get_attribute("ID")[-1])
            
            # Figure out how many types to click on the plus/minus button
            delta = adults - current_adults
            
            if delta < 0:
                # Grab the minus button
                css_tag = "div.room-filters__content > button.circle-btn.circle-btn--minus"
                btn     = self.browser.find_element_by_css_selector(css_tag)
                
                # Make delta positive
                delta = abs(delta)
            elif delta > 0:
                # Grab the plus button
                css_tag = "div.room-filters__content > button.circle-btn.circle-btn--plus"
                btn     = self.browser.find_element_by_css_selector(css_selector_tag)
                
            for _ in range(delta):
                btn.click()
            
        else:
            # Click on the double room (2nd element from the list)
            css_tag = 'li.roomtype-item'
            rooms   = room_menu.find_elements_by_css_selector(css_tag)
            rooms[1].click()
        
        return
    
```

Perfect. Finally, we need to collect the best offer identified by the website. The results returned are already sorted according to their recommendations algorithm, so we just need to grab the first offer we get (I trust that their recommender is a good one :)). A typical result returned is the following:

![typical_result_hotel](img/trivago_typical_result.png)

There are a few things we need from this tab: Hotel name, no. stars, the website that offers the deal, and the total price. Let's also add check-in and check-out dates on this list so that we can make a one-line dataframe that will be later appended to the rest of the results:


```python
%%add_to Hotel_Scraper

    # Get the best offer according to website
    def get_offer(self, destination, check_in_date, check_out_date):    
        
        # Wait until the loader exits
        xpath_tag = "//span[@class='loader-text.center-x']"
        wait      = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.invisibility_of_element_located((By.XPATH, xpath_tag)))
        
        # Grab the first result (already sorted)
        xpath_tag = "//li[@class='hotel-item item-order__list-item js_co_item']"
        offer     = self.browser.find_element_by_xpath(xpath_tag)
        
        # Get hotel name
        css_selector_tag = "span.item-link.name__copytext"
        name             = offer.find_element_by_css_selector(css_selector_tag)
        name             = name.text
        
        # Get no stars
        css_selector_tag = "div.stars-wrp > span.icon-ic.star"
        stars            = len(offer.find_elements_by_css_selector(css_selector_tag))
        
        # Get deal website
        css_selector_tag = "em.item__deal-best-ota.block.fs-normal.cur-pointer--hover"
        website          = offer.find_element_by_css_selector(css_selector_tag).text
        
        # Get total price
        try:
            # One night stays
            css_selector_tag = "em.item__per-night.fs-normal > span"
            price            = offer.find_element_by_css_selector(css_selector_tag).text
            
        except:
            # More than one night stays (different element is needed)
            css_selector_tag = "strong.item__best-price.price_min"
            price            = offer.find_element_by_css_selector(css_selector_tag).text
            
        # Remove Euro sign, remove thousands separator, and convert to int
        price = int(price.replace("€","").replace(".","").replace(",",""))
        
        # concatenate results
        df = pd.DataFrame({"city" :      destination,
                           "check_in" :  check_in_date,
                           "check_out" : check_out_date,
                           "hotel" :     name,
                           "stars" :     stars,
                           "offered_by": website,
                           "price" :     price}, 
                          index = [0])
        
        return df
```

Perfect. The few small steps that remain from the list can be implemented directly on our main function. The inputs to our main function will be a dict containing a 'destinations' list, 'start_dates', 'end_dates' lists, and the number of adults for the room:


```python
%%add_to Hotel_Scraper

    # Main
    def run(self, inputs):
        
        # Fire up a browser with the main page
        self.browser = TorBrowserDriver(DRIVER_PATH)
        self.browser.set_window_size(1024, 768)
        self.browser.implicitly_wait(self.implicit_wait) 
        self.browser.get(self.url)
    
        # Refresh on js alert or bot message
        self.refresh()
        
        # Change country to USA
        self.set_country()
        
        # Set to EURO currency
        self.set_currency()
        
        # Start scraping
        first_search = True
        dfs          = []
        
        # Enter destination
        for destination in inputs["destinations"]:
            
            self.enter_destination(destination, first_search)
            
            for check_in_date, check_out_date in zip(inputs["start_dates"], inputs["end_dates"]):
                    
                    # Enter check-in date
                    xpath_tag = "//button[@data-qa='calendar-checkin']"
                    self.enter_date(check_in_date, first_search, xpath_tag)
                    
                    # Enter check-out date
                    xpath_tag = "//button[@data-qa='calendar-checkout']"
                    self.enter_date(check_out_date, first_search, xpath_tag)
                     
                    # Fill in room info on the first time only (saved afterwards)
                    if first_search:
                        self.enter_room_info(inputs["no_adults"])
                    
                    # Search
                    css_selector_tag = "button.btn.btn--primary.js-search-button.horus-btn-search"
                    self.browser.find_element_by_css_selector(css_selector_tag).click()
                    
                    # Get offer
                    dfs.append(self.get_offer(destination, check_in_date, check_out_date))
                    
                    # Set the 'first time search' flag to false, and update the previous check in date
                    first_search           = False
                    previous_check_in_date = check_in_date
                    
        # Close window
        self.browser.quit()        
                
        # Gather results
        df = pd.concat(dfs, ignore_index = True)    
        
        return df
```

## Searching for flights
<a id="flight_gather"></a>
In a similar way, we can gather the data we need for the flights between our destinations. For this, we'll use [Skyscanner](https://www.skyscanner.com). The search tab looks like this:

![main_hotel](img/skyscanner_main.png)

Once again, we need to perform the following steps:
1. Fire up a browser (obviously)
2. Check for captchas or 'enable javascript' error messages (the latter tends to happen on Tor)
3. Choose one-way flights
4. Set the currency to EUR
5. Enter the traveler info
6. Set inbound city
7. Set outbound city
8. Select flight date
9. Grab the result (if results exist)

Let's begin writing our flight scraper. Once again, we'll be using Selenium and Tor.
First of all, let's instantiate a scraper:


```python
class Flight_Scraper(object):
    
    def __init__(self):
        # Initialize
        self.url           = "https://www.skyscanner.com"
        self.implicit_wait = 10 # Wait in between actions
        self.wait_for_elem = 20 # Wait up to 20 seconds for an element to appear, be clickable, etc.
```

Let's begin implementing the steps mentioned above. First of all, a coule function to refresh the page if a captcha or a javascript error appears:


```python
%%add_to Flight_Scraper

    # Check for exception on start
    def exception_on_start(self):
        
        try:
            # Fire up the main page
            self.browser.get('https://www.skyscanner.com')
            sleep(self.wait_for_elem + 1) # Wait to see if the timeout exception will be thrown
            return False
        except TimeoutException or WebDriverException:
            return True
    
    # Refresh on timeout or webdriver exception
    def refresh(self):
        
        # Keep refreshing until there's no javascript alert or a captcha
        while self.exception_on_start():
            
            # Fire up a new browser
            self.browser = TorBrowserDriver(DRIVER_PATH)
            self.browser.implicitly_wait(self.implicit_wait) 
    
        return
```

Sometimes, an annoying login prompt appears. Let's remove it:


```python
%%add_to Flight_Scraper

    # Remove login prompt
    def supress_login_prompt(self):
        
        # Remove annoying login prompt if it exists
        try:
            xpath = "//div[contains(@class, 'LoginPrompt')]"
            self.browser.find_element_by_xpath(xpath)
        except:
            # If it doesn't exist - do nothing
            pass
        else:
            # If it exists close it
            css_selector_tag = "button.bpk-close-button-65MQ0.bpk-modal__close-button-2a-Xb"
            self.browser.find_element_by_css_selector(css_selector_tag).click()
        
        return
```

Let's set the currency to EUR:


```python
%%add_to Flight_Scraper

    # Set currency to EUR
    def set_currency(self):
        # Click on the culture info button
        self.browser.find_element_by_css_selector("li#culture-info > button").click()
        
        # Wait for the appropriate element (currency selector) to become available
        wait = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.visibility_of_element_located((By.ID, "culture-selector-currency")))
    
        # Once it does, click it
        currency_btn = Select(self.browser.find_element_by_id("culture-selector-currency"))
        currency_btn.select_by_value("EUR")
        
        # Click on save
        self.browser.find_element_by_id("culture-selector-save").click()
        
        return
```

Now, there's a bit more code required to fill in the passenger info. Namely, to select the correct number of adults:


```python
%%add_to Flight_Scraper

    # Fill in traveller info
    def enter_traveller_info(self, no_adults):
        
        # Click on the cabin, class & travellers button
        xpath_tag = "//button[contains(@id, 'CabinClassTravellersSelector')]"
        
        # wait until it is not obscured by something else
        wait = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.invisibility_of_element_located((By.CLASS_NAME, 'bpk-scrim-2oT4Y')))
        
        # once it does, click it
        self.browser.find_element_by_xpath(xpath_tag).click()
                        
        # Enter adult info
        self.enter_adult_info(no_adults)
        
        # CLick on the done button
        xpath_tag = "//footer[contains(@class, 'BpkPopover_bpk-popover__footer')]//button"
        self.browser.find_element_by_xpath(xpath_tag).click()
        
        return
    
    # Enter the required information about adults
    def enter_adult_info(self, no_adults):
        
        # Find the adults button
        xpath_tag = "//button[@aria-controls='search-controls-adults-nudger']"
        
        # Wait until it becomes available
        wait = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.visibility_of_any_elements_located((By.XPATH, xpath_tag)))
        
        increase_adults_btn = self.browser.find_elements_by_xpath(xpath_tag)[1]
        
        # CLick the button an appropriate number of times
        for _ in range(1, no_adults):
            increase_adults_btn.click()
            
        return
```

Perfect. Next up, we need two functions to enter the origin and destination airports:


```python
%%add_to Flight_Scraper

    # Enter outbound airport
    def enter_origin(self, city_from):
        
        # Wait until the search button is visible 
        wait = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.visibility_of_element_located((By.ID, "fsc-origin-search")))
        origin_input = self.browser.find_element_by_id("fsc-origin-search")
        origin_input.clear()
        origin_input = self.browser.find_element_by_id("fsc-origin-search")
        origin_input.send_keys(city_from)
            
        # Wait until autosuggest gives a matching result
        css_selector_tag = "div#react-autowhatever-fsc-origin-search"
        wait             = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, css_selector_tag)))
            
        # Hit tab once it does
        origin_input.send_keys(Keys.TAB)
        
        return
    
    
    #Enter destination airport
    def enter_destination(self, city_to):
        
        destination_input = self.browser.find_element_by_id("fsc-destination-search")
        destination_input.clear()
        destination_input = self.browser.find_element_by_id("fsc-destination-search")
        destination_input.send_keys(city_to)
            
        # Wait until autosuggest gives a matching result
        css_selector_tag = "div#react-autowhatever-fsc-destination-search"
        wait             = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, css_selector_tag)))
            
        # Hit tab once it does
        destination_input.send_keys(Keys.TAB)
        
        return
```

Nice. Next step is to enter the departure date:


```python
%%add_to Flight_Scraper

    # Enter departure date
    def enter_departure_date(self, date):
        
        # Get the date element
        self.browser.find_element_by_id("depart-fsc-datepicker-button").click()
        
        # Select the appropriate  month
        css_selector = 'select#depart-calendar__bpk_calendar_nav_select'
        month_btn    = Select(self.browser.find_element_by_css_selector(css_selector))
        month        = date[-4:] + '-' + date[3:5] # Grab year and month from the input
        month_btn.select_by_value(month) # Select it
                        
        # Select the appropriate day of the month
        # Grab the <dd> part of the day and remove any leading zeros
        day = date[:2].lstrip('0')
                        
        # Grab the table element with the dates
        date_table = self.browser.find_element_by_xpath("//table[starts-with(@class, 'BpkCalendarGrid')]//tbody")
                    
        # Iterate over all the buttons (couldn't find an appropriate xpath constructor for this)
        for btn in date_table.find_elements_by_css_selector('button'):
            
            # Select the appropriate one and click it
            if 'outside__tumet' not in btn.get_attribute('class') and btn.text == day:
                btn.click()
                break
        
        return
```

Finally, we need to collect the results that are returned. Once again, results are soted according to price and most convenient departure time, so we just need to grab the first result returned (if at all). A typical result looks like this:

![flight_result](img/skyscanner_typical_result.png)

From this, we can collect the price, operator and flight number, as well as departure and arrival times:


```python
%%add_to Flight_Scraper

    # Gather the results
    def scrape_page(self, city_from, city_to, date):
        
        # There's a chance that a flight cannot be found on that day
        
        try: # Check if there are no flights on that day
            css_selector_tag = "div.fss-fxo-legs"
            self.browser.find_element_by_css_selector(css_selector_tag)
            
            # No flight found!
            df = pd.DataFrame({"city_from" : city_from,
                               "city_to" :   city_to,
                               "date" :      date,
                               "flight" :    "None",
                               "departure" : "None",
                               "arrival":    "None",
                               "price" :     99999}, 
                              index = [0])
            
        except:
            # Grab the best offer (automatically sorted)
            xpath_tag = "//li[contains(@class, day-list-item.ItinerariesContainer)]//div//div//article"
            offer     = self.browser.find_element_by_xpath(xpath_tag)
        
            # Get the price
            xpath_tag  = "//a[contains(@class, 'CTASection__total-price')]"
            price_text = offer.find_element_by_xpath(xpath_tag).text
            
            # Get numbers delimited by word boundaries (space, period, comma), i.e. the price
            price = int(re.findall(r'\b\d+\b', price_text)[0])
            
            # Click the go-to button
            xpath_tag = "//button[@class='bpk-button CTASection__cta-button-JozPr']"
            offer.find_element_by_xpath(xpath_tag).click()
            
            # Get the summary
            css_selector = 'div.ItineraryLeg__leg-summary-container-qSDzV.clearfix'
            self.browser.find_element_by_css_selector(css_selector).click()
            
            xpath_tag = '//div[contains(@class, ItineraryLeg__leg-summary-details)]'
            summary   = self.browser.find_element_by_xpath(xpath_tag)
            
            # From the summary get the operator
            xpath_tag = "//span[contains(@class, 'ItineraryLeg__operated-by')]"
            operator  = summary.find_element_by_xpath(xpath_tag).text
            
            # From the summary get the departure, arrival times and flight duration
            xpath_tag = "//div//div[contains(@class, 'ItineraryLeg__segment-times')]"
            times     = summary.find_element_by_xpath(xpath_tag).text.split('\n')
            dep_time  = times[0] # departure time
            arr_time  = times[1] # Arrival time
            
            # concatenate results
            df = pd.DataFrame({"city_from" : city_from,
                               "city_to" :   city_to,
                               "date" :      date,
                               "flight" :    operator,
                               "departure" : dep_time,
                               "arrival":    arr_time,
                               "price" :     price}, 
                              index = [0])
        
        
        return df
```

Perfect. Now, let's put the flight scraper together:


```python
%%add_to Flight_Scraper

    # Main
    def run(self, inputs):
        
        # Fire up a new browser
        self.browser = TorBrowserDriver(DRIVER_PATH)
        self.browser.implicitly_wait(self.implicit_wait) 
        
        # Refresh on error
        self.refresh()
        
        # We want one-way flights
        self.browser.find_element_by_id("fsc-trip-type-selector-one-way").click()
            
        # We want prices in euros
        self.set_currency()
        
        # Enter traveller info
        self.enter_traveller_info(inputs["no_adults"])
        
        # empty list to hold results
        dfs = []
        
        # Iterate over all city pairs and dates
        for city_from in inputs["city_from"]:
            for city_to in inputs["city_to"]:
               
                # Outbound city
                self.enter_origin(city_from)
                    
                # Inbound city
                self.enter_destination(city_to)
                
                for date in inputs["departure_dates"]:
                    
                    # Flight date
                    self.enter_departure_date(date)
                            
                    # Search flights
                    xpath_tag = "//button[contains(@class, 'SubmitButton')]"
                    self.browser.find_element_by_xpath(xpath_tag).click()
                    
                    # Close login prompt (if it exists)
                    self.supress_login_prompt()
                    
                    # Wait for the progress bar to disappear 
                    wait = WebDriverWait(self.browser, self.wait_for_elem)
                    wait.until(ec.invisibility_of_element_located((By.XPATH, "//div[@class='day-search-progress']")))
                    
                    # Get results and put them to list
                    dfs.append(self.scrape_page(city_from, city_to, date))
                
                    # Go back to homepage
                    self.browser.get('https://www.skyscanner.com')
                    
        # Close window
        self.browser.quit()        
            
        # Gather results
        df = pd.concat(dfs, ignore_index = True)        
        
        return df
```

Once again, the inputs to the flight scraper will be a dict, containing lists with the number of adults (this one is constant), inbound and outbound cities, as well as departure dates.

## Putting the scrapers to work

<a id="scraper_work"></a>

Right, we've built our scrapers so far. Now we need to set them to work. The easiest thing to do to speed up the process of gathering the data, is to set them to run in parallel. Let's wrap them in another class, whose aim is to fire up the multiple scrapers (workers), distribute the queries among them, collect the results from each scraping session, and write them to a file. Let's begin (once again):


```python
class Scraper(object):
    
    # Initialize
    def __init__(self, filename, scrape_type, max_job, no_processes, queries_per_process = 1):
        
        self.scrape_type         = scrape_type         # Scrape hotel or flight data?
        self.max_job             = max_job             # No. of jobs that will be performed by the scraper
        self.no_processes        = no_processes        # No. of processes to start
        self.queries_per_process = queries_per_process # No. of queries per process
        self.filename            = filename            # Filename to write outputs
        
        # Input check
        if self.scrape_type not in ['hotel', 'flight']:
            raise ValueError('Invalid scraper type')
            
        # Date format for the flight and hotel scrapers
        self.date_format = "%d/%m/%Y"

```

Let's write the main part of the program first, and then start making the functions:


```python
%%add_to Scraper

    # Main
    def run(self, destinations, start_date, end_date, no_adults):
    
        # Generate inputs for each process
        scraper_inputs = self.generate_inputs(destinations, start_date, end_date, no_adults)
        
        # Manager to manage the queue and make it accessible to the different workers
        m = Manager()
        
        # Make the queue
        q = m.Queue()
        
        # Make the pool
        p = Pool(self.no_processes)
    
        # Fire up the workers
        processes_running = p.starmap_async(partial(self.worker, queue = q), scraper_inputs) 
        
        # Fire up the listener
        self.listener(self.filename, q, processes_running)
        
        # Exiting: kill the pool
        p.close()
        p.join()
        
        return
```

This should be farly easy to understand. The generate_inputs() function will generate a list of inputs for each worker, which will be distributed on the worker() function (i.e. the scraper) by the starmap_async() function, and the listener() process will be responsible of collecting the data when one of the workers exits, and write them to a CSV file. 

Let's write the generate_inputs() function. This will take a dictionary containing a list of destinations, one start and one end date, and the number of adults. It will return a list of dicts of equal length, each dict containing the inputs for each worker:


```python
%%add_to Scraper

    # Generate a list of dicts for the flight and hotel scraper    
    def generate_inputs(self, destinations, start_date, end_date, no_adults):
        
        # Scraping hotels
        if self.scrape_type == 'hotel':
            scraper_inputs = self.hotel_scraper_input_list(destinations, 
                                                           start_date, 
                                                           end_date,
                                                           no_adults,
                                                           self.date_format)
        # Scraping flights
        else:
            scraper_inputs = self.flight_scraper_input_list(destinations, 
                                                            start_date, 
                                                            end_date, 
                                                            no_adults,
                                                            self.date_format)
        
        print('Total number of jobs: ', len(scraper_inputs))
        
        # Get the appropriate inputs
        remaining_jobs = self.get_remaining_jobs()
        scraper_inputs = [(idx, inputs) for (idx, inputs) in scraper_inputs if idx in remaining_jobs]
        
        return scraper_inputs
    
    
    # Return a list of equal query-sized inputs for the flight scraper processes
    @staticmethod
    def flight_scraper_input_list(destinations, start_date, end_date, no_adults, date_format):
        
        # Parse starting and ending dates for the trip
        tStart = dt.strptime(start_date, date_format) 
        tEnd   = dt.strptime(end_date, date_format)
        
        # Derive a day range to loop from for the start date
        delta = tEnd - tStart
    
        # Get all the dates between start date and end date
        dates = [tStart + timedelta(i) for i in range(delta.days + 1)]
        
        # Parse them to the appropriate format
        dates = [dt.strftime(elem, date_format) for elem in dates]
        
        # Generate an iterator with all inputs for the flight scraper
        city_input_pairs = product(destinations, destinations)
        
        # De-duplicate (city of arrival == city of departure)
        city_pairs = [[city_from, city_to] for (city_from, city_to) in city_input_pairs if city_from != city_to]
        
        # Generate list of dicts containing the inputs for each process
        flight_scraper_inputs = []
        
        for idx, elem in enumerate(product(city_pairs, dates)):
            
            city_from       = elem[0][0]
            city_to         = elem[0][1]
            departure_dates = list(elem[1])
            
            inputs = {"no_adults" :      no_adults,
                      "city_from" :      [city_from],
                      "city_to" :        [city_to],
                      "departure_dates" : departure_dates,
                      "id" :              idx}
            
            flight_scraper_inputs.append(inputs)
            
        return flight_scraper_inputs
        
    
    # Return a list of inputs for the hotel scraper processes
    @staticmethod
    def hotel_scraper_input_list(destinations, start_date, end_date, no_adults, date_format):
        
        # Parse starting and ending dates for the trip
        tStart = dt.strptime(start_date, date_format) 
        tEnd   = dt.strptime(end_date, date_format)
        
        date_pairs = [] # Empty list to hold the results
        
        # Derive a day range to loop from for the start date
        tRange_outer = range(0, (tEnd - tStart).days + 1)
            
        # Loop through all the date pairs, and append them to the list
        for tStart_outer in (tStart + timedelta(n) for n in tRange_outer):
                
            # Derive a day range to loop from for the end date
            tRange_inner = range(1, (tEnd - tStart_outer).days + 1)
                
            for date in (tStart_outer + timedelta(n) for n in tRange_inner):
                tCursor_end   = dt.strftime(date, date_format)
                tCursor_start = dt.strftime(tStart_outer, date_format)
                date_pairs.append((tCursor_start, tCursor_end))
        
        
        # Iterate over each destination and each date-pair to create a dataframe
        inputs = [] # Empty list to hold the results
        
        for idx, (destination, date_pair) in enumerate(product(destinations, date_pairs)):
            
            # Generate a dictionary with the destination included, and a unique set of start dates
            temp                 = date_pair.to_dict('list')
            temp["no_adults"]    = no_adults
            temp['destinations'] = [destination]
            temp["id"]           = idx
            
            # Append to list
            inputs.append(temp)
        
        return inputs
    
    
    # Generate a list of remaining jobIDs to run
    def get_remaining_jobs(self):
        
        # Get all the keys from the file
        with pd.HDFStore(self.filename) as hdf:
            keys = hdf.keys()
        
        # Get the job id from each key
        finished_jobs =[elem.replace('/', '') for elem in keys]
        
        # Construct job id for all the jobs we want to perform
        all_jobs = ['job_' + str(elem) for elem in range(self.max_job + 1)]
        
        # Get the job IDs that need to be performed
        remaining_jobs = list(set(all_jobs) - set(finished_jobs))
        
        return remaining_jobs
```

Perfect. Next up, let's write our worker process. This will start a virtual display, fire up the appropriate scraper (for flights or hotels), scrape the data we want, put them to queue for the listener to collect it, and close the browser and the virtual display:


```python
%%add_to Scraper

    # Worker to scrape data
    def worker(self, job_id, args, queue): 
        
        # Start virtual display
        xvfb_display = start_xvfb()
        
        # Start up the appropriate scraper instance
        if self.scrape_type == 'hotel':
            scraper = Hotel_Scraper()
            
        elif self.scrape_type == 'flight':
            scraper = Flight_Scraper()
            
        # Put it to work
        df = scraper.run(args)
        
        # Put the result to the queue
        queue.put((job_id, df))
        
        # Close the virtual display
        stop_xvfb(xvfb_display)
    
        return
```

Finally, we need the listener() process. This will monitor the queue containing results from the workers, and as soon as any results have been inserted to the queue, it will write them to a CSV file:


```python
%%add_to Scraper

    # Listen for messages on the queue (q) and writes to file
    @staticmethod
    def listener(filename, queue, processes_running):
        
        # While the processes are still running or the queue is not empty:
        while (not processes_running.ready()) or (not queue.empty()):
    
            # Grab an item from the queue
            df = queue.get(block = True)
            
            if not df.empty:
                
                with open(filename, 'a') as f:
                    df.to_csv(f, header = False)
            
            # Wait a bit
            sleep(2)
        
        return
```

Perfect. Now we just need to put the scrapers to work:


```python
    # ----------------------- Scrape Hotels --------------------------------
    scraper = Scraper(filename     = 'hotels.csv',
                      scrape_type  = 'hotel',
                      max_job      = 4959,
                      no_processes =  cpu_count() - 1) # cpu_count() - 1
    
    
    scraper.run(destinations = ['Wroclaw', 'Bilbao', 'Colmar', 'Hvar', 'Riga', 'Milan', 'Athens', 'Budapest', 'Lisbon', 'Bohinj'], # https://www.europeanbestdestinations.com/european-best-destinations-2018/ 
                start_date = "01/07/2019", 
                end_date = "01/08/2019", 
                no_adults = 2)
    
    
    # ----------------------- Scrape Flights --------------------------------
    scraper = Scraper(filename     = 'flights.csv',
                      scrape_type  = 'flight',
                      max_job      = 2879,
                      no_processes = cpu_count() - 1)
        
        
    scraper.run(destinations = ['Wroclaw', 'Bilbao', 'Colmar', 'Hvar', 'Riga', 'Milan', 'Athens', 'Budapest', 'Lisbon', 'Bohinj', 'Amsterdam'],
                start_date   = "01/07/2019", 
                end_date     = "01/08/2019", 
                no_adults    = 2)
```

## Results

<a id="scrape_res"></a>

This took some time.. Now, we have two files, containing all the data we want:


```python
hotels = pd.read_excel('./data/hotels.xlsx')
hotels.head(5)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>city</th>
      <th>check_in</th>
      <th>check_out</th>
      <th>hotel</th>
      <th>stars</th>
      <th>offered_by</th>
      <th>price</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Athens</td>
      <td>07/01/2019</td>
      <td>08/01/2019</td>
      <td>Hotel Niki</td>
      <td>3</td>
      <td>Hotel Website</td>
      <td>4081</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Athens</td>
      <td>07/01/2019</td>
      <td>07/02/2019</td>
      <td>Hotel Divani Palace Acropolis</td>
      <td>5</td>
      <td>Booking.com</td>
      <td>125</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Athens</td>
      <td>07/01/2019</td>
      <td>07/03/2019</td>
      <td>Royal Olympic Hotel</td>
      <td>5</td>
      <td>Expedia</td>
      <td>279</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Athens</td>
      <td>07/01/2019</td>
      <td>07/04/2019</td>
      <td>Acropolis View Hotel</td>
      <td>3</td>
      <td>Hotels.com</td>
      <td>314</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Athens</td>
      <td>07/01/2019</td>
      <td>07/05/2019</td>
      <td>Royal Olympic Hotel</td>
      <td>5</td>
      <td>Expedia</td>
      <td>564</td>
    </tr>
  </tbody>
</table>
</div>



Perfect. So, in this dataframe we have the best (according to Trivago) hotel, for staying in every one of our destinations, for all combinations of check-in and check-out dates.  Let's see what's in the flights file:


```python
flights = pd.read_excel('./data/flights.xlsx')
flights.head(5)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>city_from</th>
      <th>city_to</th>
      <th>date</th>
      <th>flight</th>
      <th>departure</th>
      <th>arrival</th>
      <th>price</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Amsterdam</td>
      <td>Wroclaw</td>
      <td>07/01/2019</td>
      <td>KLM KL1271</td>
      <td>11:50</td>
      <td>13:35</td>
      <td>292</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Amsterdam</td>
      <td>Bilbao</td>
      <td>07/01/2019</td>
      <td>KLM KL1685</td>
      <td>09:15</td>
      <td>11:20</td>
      <td>384</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Amsterdam</td>
      <td>Colmar</td>
      <td>07/01/2019</td>
      <td>EasyJet EZY1045</td>
      <td>19:00</td>
      <td>20:20</td>
      <td>234</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Amsterdam</td>
      <td>Hvar</td>
      <td>07/01/2019</td>
      <td>EasyJet EZY7997</td>
      <td>12:50</td>
      <td>15:00</td>
      <td>500</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Amsterdam</td>
      <td>Riga</td>
      <td>07/01/2019</td>
      <td>Air Baltic BT618</td>
      <td>10:20</td>
      <td>13:35</td>
      <td>234</td>
    </tr>
  </tbody>
</table>
</div>



Here, we have flights from every city in our list (including the home node: Amsterdam), towards every other city in our list, for every date between July 1st to August 1st. From here on we can focus on solving the question at hand, as we have all the data we need. 

# Optimisation Problem
<a id="opt_prob"></a>

The problem we are trying to solve can be formulated as a binary integer linear programming (BILP) problem. This type of problems can be solved efficiently by a variety of algorithms, from which we can choose and write our own, but there's already a python library we can utilize, called [PuLP](https://coin-or.github.io/pulp/). In the following, we'll (a) formulate the optimisation the problem, and (b) solve it using PuLP instead of implementing our own algorithm from scratch.

## Formulation

<a id="formulation"></a>

In the following, we'll introduce our decision variables, the objective function to be minimised, along with the necessary constraints. We'll also introduce the necessary notation as we go along:

### Decision Variables
First of all, we need to introduce some notation, along with our decision variables:
* $x_{f}^{o,d,t} \in Z_2^{p(p-1)q}$ are binary decision variables, one for each flight in the dataset, having a value of 1 if a flight is active (i.e. to be taken), or 0 if it is not active. $o$ refers to the outbound city (origin), $d$ refers to the inbound city (destination), and $t$ is the day of travel. The total number of variables is $q$ (number of days in the dataset), times $p(p-1)$, as the same city cannot be an origin and a destination at the same time.
* $x_{h}^{o,t_b,t_e} \in Z_2^{pq(q+1)/2}$ are, again, binary decision variables, one for each hotel, denoted by subscipt $o$ and duration of stay $(t_b, t_e)$, with $t_b$ being the day we'll start occupying a room in the hotel, and $t_e$, the day we'll depart from it. Note that, the number of elements is $p$ (one hotel for each city) times $q(q+1)/2$, which is the number of all possible stay durations (equal to the number of elements in the upper triangle of a square matrix). If, for example, we check-in on the 13th of July, we can only checkout on the days that follow (on the 14th, 15th etc), not the preceding ones (12th, 11th, etc).

where: 
* $C$ refers to the set of cities that will be visited, $p$ is the total number of cities, and $c = 0$ is the home node, from which we have to start and finish our trip.
* $T$ refers to the set of days between July 1st ($t_0$) to August 1st, with $q$ being the total number of days between our one month time span.

### Objective function

The objective function is the total cost of our holidays, i.e. cost of every hotel and every flight we take:

$$min_{\bar{x}_f, \bar{x}_h} = \sum_{i = 1}^{p} \sum_{j = 1, j \neq i}^{p} \sum_{k = 1}^{q} c_{f}^{i,j,k} x_{f}^{i,j,k} + \sum_{i = 1}^{p} \sum_{j = 1}^{q} \sum_{k = j + 1}^{q} c_{h}^{i, j, k} x_{h}^{i, j, k}$$

with:

* $c_{f}^{o,d,t} \in R^{p(p-1)q}$ are the costs of flying from city $o$ (origin) to city $d$ (destination) at time $t$
* $c_{h}^{o,t_b,t_e} \in R^{pq(q+1)/2}$ are the costs of staying at city $o$, from day $t_b$ to day $t_e$.

### Constraints

While the objective function is easy to deduct, the constraints require a bit more work:

First of all, we need to make sure that we start our holidays from the home node, and we also arrive back to the home node at the end of the holiday period. This means that there must be exactly one flight from the home node $c = 0$ (Amsterdam) at time $t = 0$, and exactly one flight towards the home node at the end $t = t_q$. All flights with a different outbound city in the dataset are not allowed:

$$ \begin{align}
\sum_{j = 1}^{p} x_f^{c_0, j, t_0} &= 1 \\ 
 \sum_{j = 1}^{p} x_f^{j, c_0, t_q} &= 1 \\
 \sum_{j = 1, j \neq c}^{p} x_f^{c, j, t_0} &= 0,~ \forall c \in C \\
 \sum_{j = 1, j \neq c}^{p} x_f^{j, c, t_q} &= 0,~ \forall c \in C
 \end{align}$$

Moreover, we have to make sure that each city is visited at most once (apart from the home node). This also means that there is at most one flight towards every destination, and one flight from every origin:

$$ \begin{align}
\sum_{i = 0}^{q} \sum_{j = 1 + 1}^{q} x_h^{c, i, j} &\leq 1,~\forall \{c \in C~|~c \neq 0 \} \\
\sum_{i = 0}^{p} \sum_{j = 0}^{q} x_f^{i,c,j} &\leq 1,~\forall c \in C \\
\sum_{i = 0}^{p} \sum_{j = 0}^{q} x_f^{c,i,j} &\leq 1,~\forall c \in C
\end{align} $$

Each hotel stay must be accompanied by the corresponding inbound and outbound flight (there's no way to get to a city without taking a flight towards it, and you can't get out with another flight):

$$
x_f^{i,c,t_b} = x_h^{c,t_b,t_e} = x_f^{c, i, t_e},~\forall t_b \in T, ~ \forall t_e > t_b\in T, ~\forall c \in C
$$

At least $N$ cities will be visited. For cost minimisation (if the problem is formulated properly), this essentially means that exactly $N$ cities will be visited. Furthermore, at least $N + 1$ flights will be taken (+ 1 to return to the home node at the end):

$$
\begin{align}
\sum_{i = 1}^{p} \sum_{j = 0}^{q} \sum_{k = j + 1}^{q} x_h^{i,j,k} &\leq N \\
\sum_{i = 1}^{p} \sum_{j = 0, j \neq i}^{p} \sum_{k = 1}^{q} x_f^{i,j,k} &\leq N + 1
\end{align}
$$

Finally, we need to implement a minimum stay duration of $K$ days at each city , apart from the home node. This means that, if a city is visited on a certain date, we need to restrict all outgoing flights for the next $K$ days. The equality constraints introduced above will then ensure that any other hotel stays for the next $K$ days will be zeroed out. This can be implemented with the following set of big-M constraints:

$$
\sum_{i = 1}^{p} \sum_{j = J}^{q} x_{f}^{c,i,j} \leq M \left(1 - \sum_{i = 1}^{p} \sum_{j=J}^{J+K} x_{f}^{i,c,k}\right),~\forall\{c \in C~|~c \neq 0 \},~\forall \{J \in T ~| ~J \leq q - K\}
$$

The above works for all intermediate nodes. We need to set the following constraints to- and from- the home node:

$$
\begin{align}
\sum_{i = 0}^{p} \sum_{j = 0}^{p} \sum_{k = 1}^{K} x_f{i,j,k} &= 0 \\
\sum_{i = 1}^{p} \sum_{j = 1}^{K} \sum_{k = j + 1}^{K+ 1} x_h^{i,j,k} &= 0
\end{align}
$$

And that's about it. Next, code it all:

## PuLP programming

<a id="pulp"></a>

PuLP has a fairly intuitive way of formulating the problem. In the following, we'll instantiate the problem, add one by one the constraints followed by the objective function, and then get the solution to the problem.

First of all let's generate the necessary constants, and instantiate the problem:


```python
    # Necessary constants
    t0 = "07/01/2019"
    tq = "08/01/2019"
    c0 = "Amsterdam"
    K  = 4
    N  = 6 + 1 # Plus one for the home node
    M  = 1e9
    C  = flights['city_from'].unique()
    T  = flights['date'].unique()
    cf = flights.set_index(['city_from', 'city_to', 'date'])
    ch = hotels.set_index(['city', 'check_in', 'check_out'])
    C.sort()
    T.sort()
    
    # Instantiate problem
    model = plp.LpProblem("Traveling Costs", plp.LpMinimize)
```

Next, let's generate our decision variables:


```python
    # Generate decision variables
    xf = plp.LpVariable.dicts("xf", ((from_city, to_city, at_date) \
                                     for from_city, to_city, at_date in cf.index),
                              cat = 'Binary')
    
    xh = plp.LpVariable.dicts("xh", ((city, check_in, check_out) \
                                     for city, check_in, check_out in ch.index),
                              cat = 'Binary' )
```

Right. Now we'll start adding up our constraints in the same order as they appeared earlier. First of all, we'll code the constraints that ensure we'll start and finish our holidays at the home node:


```python
    # Starting flight only from AMS at 07/01/2019
    cf_from_c0_at_t0 = [xf[c0, to_city, t0] for to_city in C if to_city != c0]
    
    model += plp.lpSum(cf_from_c0_at_t0) == 1, "Starting flight only from AMS at 07/01/2019 constraint 1/2" 
    
    cf_not_from_c0_at_t0 = [xf[from_city, to_city, t0] \
                            for from_city, to_city in product(C, C) \
                            if from_city != to_city and from_city != c0 and to_city != c0]
    
    model += plp.lpSum(cf_not_from_c0_at_t0) == 0, "Starting flight only from AMS at 07/01/2019 constraint 2/2" 
    
    # Returning flight only to AMS at 08/01/2019
    cf_towards_c0_on_tq = [xf[from_city, c0, tq] for from_city in C if from_city != c0]
    
    model += plp.lpSum(cf_towards_c0_on_tq) == 1, "Returning flight only to AMS at 08/01/2019 - constraint 1/2" 

    cf_not_towards_c0_on_tq = [xf[from_city, to_city, tq] \
                               for from_city, to_city, at_date in cf.index \
                               if to_city != c0 and at_date == tq]
    
    model += plp.lpSum(cf_not_towards_c0_on_tq) == 0, "Returning flight only to AMS at 08/01/2019 - constraint 2/2"
```

Next, the constraints indicating that each city must be visited at most once:


```python
     # At most one visit (check in / check out pair) per city
    for city_name in C:
        if city_name != c0:
            
            possible_checkins_at_city = [xh[city, check_in, check_out]
                                         for city, check_in, check_out in ch.index if city == city_name]
            
            model += plp.lpSum(possible_checkins_at_city) <= 1, "At most one visit at {}".format(city_name)
    
    # At most one flight connecting any two cities
    for city_1, city_2 in product(C, C):
        
        if city_1 != city_2 and city_1 != c0 and city_2 != c0: # (c0 is the only city with two flights. One at the beginning and one at the end of the holidays)
            
            cf_from_city1_to_city2 = [xf[city_1, city_2, at_date] for at_date in T]
            cf_from_city2_to_city1 = [xf[city_2, city_1, at_date] for at_date in T]
            
            model += plp.lpSum(cf_from_city1_to_city2) + plp.lpSum(cf_from_city2_to_city1) <= 1, \
            "Travel between {} and {} at most once".format(city_1, city_2)
    
```

Very good. Next, we need to manage our connections between cities. That requires a bit more code:


```python
    # Manage connections: Flight at_date must match check_in at_date for inbound city and check_out at_date for the outbound city
    for from_city, to_city, flight_date in cf.index:
        
        # Is it the first flight we'll take as we start out?
        initial_flight = from_city == c0 and flight_date == t0
        
        # Is it the final flight we'll take (going c0)?
        final_flight = to_city == c0 and flight_date == tq
        
        # Is it a flight from leaving from c0, or returning to c0?
        intermediate_flight = not(initial_flight) and not(final_flight)
        
       
        if intermediate_flight:
            current_flight = xf[from_city, to_city, flight_date]
            
            prior_possible_checkouts_if_on_current_flight = [xh[from_city, from_date, flight_date] \
                                                             for from_date in remaining_T(T, flight_date, 'pre') \
                                                             if from_date != flight_date]
            
            post_possible_checkins_if_on_current_flight = [xh[to_city, flight_date, at_date] \
                                                            for at_date in remaining_T(T, flight_date, 'post') \
                                                            if at_date != flight_date]
            
            # Check out at_date <check-out> for city <city from> matching flight <city from> at at_date <check-out>
            model += current_flight <= plp.lpSum(prior_possible_checkouts_if_on_current_flight), \
            'Check out: traveling from {} to {} at {}'.format(from_city, to_city, flight_date)
        
            # Check in at_date <check-in> for city <city to> matching flight <city to> at at_date <check-in>
            model += current_flight <= plp.lpSum(post_possible_checkins_if_on_current_flight), \
            'Check_in: traveling from {} to {} at {}'.format(from_city, to_city, flight_date)

        elif initial_flight:
            # Check in at hotel of first city
            current_flight = xf[from_city, to_city, flight_date]
            
            post_possible_checkins_if_on_current_flight = [xh[to_city, flight_date, from_date] \
                                                           for from_date in remaining_T(T, flight_date, 'post') \
                                                           if from_date != flight_date]
            
            model += current_flight == plp.lpSum(post_possible_checkins_if_on_current_flight), \
            'Check_in: traveling from {} to {} at {}'.format(from_city, to_city, flight_date)
        
        elif final_flight: 
            
            current_flight = xf[from_city, to_city, flight_date]
            
            prior_possible_checkouts_if_on_current_flight = [xh[from_city, from_date, flight_date] \
                                                             for from_date in remaining_T(T, flight_date, 'pre') \
                                                             if from_date != flight_date]
            
            # Check out of hotel of last city 
            model += current_flight == plp.lpSum(prior_possible_checkouts_if_on_current_flight), \
            'Check_out: traveling from {} to {} at {}'.format(from_city, to_city, flight_date)
    
```

Right, next we need to incorporate the minimum stay duration constraints:


```python
    # Minimum stay at each city = No flights allowed before and after N days
    for cur_city, cur_date in product(C, T):
        if cur_city != c0 and cur_date != tq:
            
            cf_from_current_city_at_current_date = [xf[from_city, to_city, at_date] \
                                                    for from_city, to_city, at_date in cf.index \
                                                    if to_city == cur_city and at_date == cur_date]
            
            no_flight_dates = remaining_T(T, cur_date, 'post')[0 : K - 1] 
            
            forbidden_cf_from_current_city_at_current_date = [xf[from_city, to_city, at_date] \
                                                              for from_city, to_city, at_date in cf.index \
                                                              if from_city == cur_city and at_date in no_flight_dates]
        
            x = plp.lpSum(cf_from_current_city_at_current_date)
            y = plp.lpSum(forbidden_cf_from_current_city_at_current_date)
        
            # If x == 1: y == 0 else if x == 0: y >= 0 -> y <= M(1-x)
            model += y <= M * (1 - x), 'Minimum stay at {} if visited on {}'.format(cur_city, cur_date)
            
    
    # No flights or checkins allowed after the start date for at least N days
    forbidden_flight_dates = remaining_T(T, t0, 'post')[0 : K - 1]
    
    forbidden_cf = [xf[from_city, to_city, at_date] \
                    for from_city, to_city, at_date in cf.index if at_date in forbidden_flight_dates]
    
    model += plp.lpSum(forbidden_cf) == 0, 'Minimum stay on first node - cf'
    
    # No checkins allowed after the start date for at least N days    
    for cur_city in C:
        if cur_city != c0:
            
            forbidden_checkins = [xh[cur_city, check_in, check_out] \
                                  for cur_city, check_in, check_out in ch.index \
                               if check_in == cur_date and check_out in forbidden_flight_dates]
            
            model += plp.lpSum(forbidden_checkins) == 0, "Minimum stay on first node - ch at {}".format(cur_city)
```

Finally, we have to make sure that at least (or exactly) N cities will be visited:


```python
# At least N cities must be visited: at least N check ins + at least (N + 1) flights
    total_checkins = [xh[city, from_date, to_date] for city, from_date, to_date in ch.index if city != c0]
    
    model += plp.lpSum(total_checkins) >= N, "No cities to visit"
    
    total_cf = [xf[from_city, to_city, at_date] for from_city, to_city, at_date in cf.index]
        
    model += plp.lpSum(total_cf) >= N + 1, 'No flights to take'
```

Perfect. That was the final constraint. Let's generate our objective function:


```python
    # Generate objective function
    total_flight_costs = [xf[from_city, to_city, at_date] * cf.loc[(from_city, to_city, at_date), "price"] \
                          for from_city, to_city, at_date in cf.index]
    
    total_hotel_costs = [xh[city, check_in, check_out] * ch.loc[(city, check_in, check_out), "price"] \
                         for city, check_in, check_out in ch.index]
    
    model += plp.lpSum(total_flight_costs + total_hotel_costs), "Total cost minimization"
```

That's it. Let's solve the problem (just a one-liner), and collect the results in new dataframes:


```python
    model.solve() # Solve the model    
    
    # Grab results
    sol_cf = [cf.loc[from_city, to_city, at_date] \
              for from_city, to_city, at_date in cf.index if xf[from_city, to_city, at_date].varValue == 1]
    sol_cf = pd.concat(sol_cf, axis = 1).T
    
    sol_cf.index = sol_cf.index.set_names(['city_from', 'city_to', 'date'])
    sol_cf.reset_index(inplace = True)
    
    sol_ch = [ch.loc[city, check_in, check_out] \
              for city, check_in, check_out in ch.index if xh[city, check_in, check_out].varValue == 1]
    sol_ch = pd.concat(sol_ch, axis = 1).T
    
    sol_ch.index = sol_ch.index.set_names(['city_from', 'city_to', 'date'])
    sol_ch.reset_index(inplace = True)
```

# Solution

<a id="solution"></a>
Let's have a look:


```python
    pd.set_option('expand_frame_repr', False)
    
    print("-----------------------------------Flight Schedule-----------------------------------")
    print(sol_cf, '\n\n')
    print("-----------------------------------Hotel Schedule-----------------------------------")
    print(sol_ch)
    
```

    -----------------------------------Flight Schedule-----------------------------------
       city_from    city_to        date                 flight departure  arrival  price
    0  Amsterdam    Wroclaw  07/01/2019             KLM KL1271     11:50    13:35    292
    1    Wroclaw       Hvar  07/04/2019         Ryanair FR4108     12:30    13:45    250
    2       Hvar   Budapest  07/10/2019     Laudamotion OE5592   8:05 AM  9:40 AM    112
    3   Budapest     Colmar  07/14/2019        Wizz Air W62269     13:10    14:55     85
    4     Colmar      Milan  07/25/2019             KLM KL1990     18:25    19:55    212
    5      Milan     Athens  07/25/2019  Aegean Airlines A3665     17:45    21:10    189
    6     Athens  Amsterdam  08/01/2019             KLM KL1576     17:20    19:55    278 
    
    
    -----------------------------------Hotel Schedule-----------------------------------
           city    check_in   check_out                                 hotel  stars   offered_by  price
    0   Wroclaw  07/01/2019  07/04/2019                AC by Marriott Wroclaw      4    AC Hotels    324
    1      Hvar  07/04/2019  07/10/2019  Hotel Amfora Hvar Grand Beach Resort      4      Expedia    440
    2  Budapest  07/10/2019  07/14/2019         Hotel Mercure Budapest Korona      4  ebookers.ch    351
    3    Colmar  07/14/2019  07/18/2019                  James Boutique Hôtel      4   Hotels.com    508
    4     Milan  07/18/2019  07/25/2019                      Room Mate Giulia      5      Expedia    840
    5    Athens  07/25/2019  08/01/2019              Hotel Grand Hyatt Athens      5  Booking.com    734


Beautiful. We could also implement additional constraints, like no. stars on each hotel, or flight arrival times etc. (I don't like the flight from Milan to Athens, arriving at 9 pm), but it should be fairly easy to implement those...
