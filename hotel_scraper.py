DRIVER_PATH = '/home/miltos/Downloads/tor-browser-linux64-8.0.8_en-US/tor-browser_en-US/'
#DRIVER_PATH = '/home/miltos/Downloads/chromedriver_linux64/chromedriver'

from tbselenium.tbdriver import TorBrowserDriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

from datetime import datetime as dt
import pandas as pd
from time import sleep


class Hotel_Scraper(object):
    
    def __init__(self):
        
        self.url = "https://www.trivago.com/"
        self.implicit_wait = 5 # Wait in between actions
        self.wait_for_elem = 20 # Wait up to 20 seconds for an element to appear, be clickable, etc.
    

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
            alert = self.browser.find_element_by_css_selector(css_selector_tag).get_attribute("href")
            # Does it say anything about javascript?
            if 'javascript' in alert:
                return True
        except:
            # No js. alert
            return False
        
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
    
    
    def enter_destination(self, destination, first_search):
        
        # Destination input
        css_selector_tag = "input#horus-querytext"
        destination_input = self.browser.find_element_by_css_selector(css_selector_tag)
        destination_input.send_keys(destination)
        
        # Wait until the selection pop-up becomes available
        css_selector_tag = "div.ssg-suggestion__info"
        wait = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, css_selector_tag)))
        
        if first_search:
            # Click tab twice and hit enter (move to the next input)
            destination_input.send_keys(Keys.TAB)
            destination_input.send_keys(Keys.TAB)
            destination_input.send_keys(Keys.ENTER)
        
        return
    
    
    def enter_room_info(self, adults):
        
        # Depending on the IP, two different dropdown menus appear
        try:
            # Get the dropdown menu
            css_selector_tag = "ul.df_container_roomtype_selector.df_dropdown"
            room_menu = self.browser.find_element_by_css_selector(css_selector_tag)
            
        except NoSuchElementException:
            # Get the current no. of adults
            xpath_tag = "//input[contains(@id, 'adults-input')]"
            current_adults = self.browser.find_element_by_xpath(xpath_tag)
            current_adults = int(current_adults.get_attribute("ID")[-1])
            
            # Figure out how many types to click on the plus/minus button
            delta = adults - current_adults
            
            if delta < 0:
                # Grab the minus button
                css_selector_tag = "div.room-filters__content > button.circle-btn.circle-btn--minus"
                btn = self.browser.find_element_by_css_selector(css_selector_tag)
                
                # Make delta positive
                delta = abs(delta)
            elif delta > 0:
                # Grab the plus button
                css_selector_tag = "div.room-filters__content > button.circle-btn.circle-btn--plus"
                btn = self.browser.find_element_by_css_selector(css_selector_tag)
                
            for _ in range(delta):
                btn.click()
            
        else:
            # Click on the double room (2nd element from the list)
            css_selector_tag = 'li.roomtype-item'
            rooms = room_menu.find_elements_by_css_selector(css_selector_tag)
            rooms[1].click()
        
        return
    
    
    # Enter check_in date
    def enter_date(self, check_in_date, first_search, xpath_tag):
        
        if not first_search: 
            self.browser.find_element_by_xpath(xpath_tag).click()
            wait = WebDriverWait(self.browser, self.wait_for_elem)
            wait.until(ec.visibility_of_element_located((By.XPATH, xpath_tag)))
        
        # Get the month that appeared in the dropdown menu
        css_selector_tag = 'th#cal-heading-month.cal-heading-month > span'
        menu_month = self.browser.find_element_by_css_selector(css_selector_tag).text
        
        # Parse it
        menu_month = dt.strptime(menu_month, "%B %Y").month
        
        # Parse check in date
        check_in_date_parsed = dt.strptime(check_in_date, "%d/%m/%Y")
        
        # Get the difference in months (i.e how many times to hit the button)
        delta = check_in_date_parsed.month - menu_month
        
        # Get the next month button
        css_selector_tag = "button.cal-btn-next"
        next_month_button = self.browser.find_element_by_css_selector(css_selector_tag)
        
        # Click it an appropriate number of times
        for _ in range(delta):
            next_month_button.click()
        
        # Grab the calendar web element again (avoid stale reference error)
        css_selector_tag = "div.df_container_calendar"
        calendar_elem = self.browser.find_element_by_css_selector(css_selector_tag)
        
        # Click on the right button
        xpath_tag = "//time[@datetime='" + check_in_date[-4:] + '-' + check_in_date[3:5] + '-'+ check_in_date[0:2] + "']"
        wait = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.visibility_of_element_located((By.XPATH, xpath_tag)))
        calendar_elem.find_element_by_xpath(xpath_tag).click()
        
        return
    
# NOT NECESSARY ANYMORE!!! :)
    # Enter check-out date
#    def enter_check_out_date(self, check_out_date, first_search):
#        
#        # Enter checkout date
#        if not first_search:
#            xpath_tag = "//button[@data-qa='calendar-checkout']"
#            self.browser.find_element_by_xpath(xpath_tag).click()
#            wait = WebDriverWait(self.browser, self.wait_for_elem)
#            wait.until(ec.visibility_of_element_located((By.XPATH, xpath_tag)))
#            
#        # Get the month that appeared in the dropdown menu
#        css_selector_tag = 'th#cal-heading-month.cal-heading-month > span'
#        menu_month = self.browser.find_element_by_css_selector(css_selector_tag).text
#        
#        # Parse it
#        menu_month = dt.strptime(menu_month, "%B %Y").month
#        
#        # Parse check_out date
#        check_out_date_parsed = dt.strptime(check_out_date, "%d/%m/%Y")
#        
#        # Get the difference in months (i.e how many times to hit the button)
#        delta = check_out_date_parsed.month - menu_month
#        
#        # Get the next month button (avoid stale reference error)
#        css_selector_tag = "button.cal-btn-next"
#        next_month_button = self.browser.find_element_by_css_selector(css_selector_tag)
#        
#        # CLick the button an appropriate number of times
#        for _ in range(delta):
#            next_month_button.click()
#            
#        # Grab the calendar web element again (avoid stale reference error)
#        css_selector_tag = "div.df_container_calendar"
#        calendar_elem = self.browser.find_element_by_css_selector(css_selector_tag)
#        
#        # Click on the right button
#        xpath_tag = "//time[@datetime='" + check_out_date[-4:] + '-' + check_out_date[3:5] + '-'+ check_out_date[0:2] + "']"
#        calendar_elem.find_element_by_xpath(xpath_tag).click()
#        
#        return
    
    
    # Get the best offer according to website
    def get_offer(self, destination, check_in_date, check_out_date):    
        
        # Wait until the loader exits
        xpath_tag = "//span[@class='loader-text.center-x']"
        wait = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.invisibility_of_element_located((By.XPATH, xpath_tag)))
        
        # Grab the first result (already sorted)
        xpath_tag = "//li[@class='hotel-item item-order__list-item js_co_item']"
        offer = self.browser.find_element_by_xpath(xpath_tag)
        
        # Get hotel name
        css_selector_tag = "span.item-link.name__copytext"
        name = offer.find_element_by_css_selector(css_selector_tag)
        name = name.text
        
        # Get no stars
        css_selector_tag = "div.stars-wrp > span.icon-ic.star"
        stars = len(offer.find_elements_by_css_selector(css_selector_tag))
        
        # Get deal website
        css_selector_tag = "em.item__deal-best-ota.block.fs-normal.cur-pointer--hover"
        website = offer.find_element_by_css_selector(css_selector_tag).text
        
        # Get total price
        try:
            # One night stays
            css_selector_tag = "em.item__per-night.fs-normal > span"
            price = offer.find_element_by_css_selector(css_selector_tag).text
            
        except:
            # More than one night stays (different element is needed)
            css_selector_tag = "strong.item__best-price.price_min"
            price = offer.find_element_by_css_selector(css_selector_tag).text
            
        # Remove Euro sign, remove thousands separator, and convert to int
        price = int(price.replace("€","").replace(".","").replace(",",""))
        
        # concatenate results
        df = pd.DataFrame({"city" : destination,
                           "check_in" : check_in_date,
                           "check_out" : check_out_date,
                           "hotel" : name,
                           "stars" : stars,
                           "offered_by": website,
                           "price" : price}, index = [0])
        
        return df
    

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
        # previous_check_in_date = dt.strftime(dt.now(), "%d/%m/%Y")
        dfs = []
        
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
                    #if first_search:
                    #    self.enter_room_info(inputs["no_adults"])
                    
                    # Search
                    css_selector_tag = "button.btn.btn--primary.js-search-button.horus-btn-search"
                    self.browser.find_element_by_css_selector(css_selector_tag).click()
                    
                    # Get offer
                    dfs.append(self.get_offer(destination, check_in_date, check_out_date))
                    
                    # Set the 'first time search' flag to false, and update the previous check in date
                    first_search = False
                    # previous_check_in_date = check_in_date
                    
        # Close window
        self.browser.quit()        
                
        # Gather results
        df = pd.concat(dfs, ignore_index = True)    
        
        return df
        
    
if __name__ == "__main__": 
   
    # Test a random city at a random date
    inputs = {
            "destinations" : ['Wroclaw'],
            "start_dates" : ["01/07/2019"],
            "end_dates" : ["01/08/2019"],
            "no_adults" : 2, # No adults in each room
            }
    
    scraper = Hotel_Scraper()
    
    res = scraper.run(inputs)