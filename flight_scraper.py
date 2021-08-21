DRIVER_PATH = '/home/miltos/Downloads/tor-browser-linux64-8.0.8_en-US/tor-browser_en-US/'
#DRIVER_PATH = '/home/miltos/Desktop/chromedriver'

from tbselenium.tbdriver import TorBrowserDriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
import re
import pandas as pd
from time import sleep


class Flight_Scraper(object):
    
    def __init__(self):
        # Initialize
        self.url = "https://www.skyscanner.com"
        self.implicit_wait = 10 # Wait in between actions
        self.wait_for_elem = 20 # Wait up to 20 seconds for an element to appear, be clickable, etc.
        
        # Instructions on how to install here:
        # https://stackoverflow.com/questions/15316304/open-tor-browser-with-selenium
        # Install tor with sudo-apt get. See link
        # Geckodriver by doing the following:
        #visit https://github.com/mozilla/geckodriver/releases
        #download the latest version of "geckodriver-vX.XX.X-linux64.tar.gz"
        #unarchive the tarball (tar -xvzf geckodriver-vX.XX.X-linux64.tar.gz)
        #give executable permissions to geckodriver (chmod +x geckodriver)
        #move the geckodriver binary to /usr/local/bin or any location on your system PATH


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
        wait = WebDriverWait(self.browser, self.wait_for_elem)
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
        wait = WebDriverWait(self.browser, self.wait_for_elem)
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, css_selector_tag)))
            
        # Hit tab once it does
        destination_input.send_keys(Keys.TAB)
        
        return
    
    
    # Enter departure date
    def enter_departure_date(self, date):
        
        # Get the date element
        self.browser.find_element_by_id("depart-fsc-datepicker-button").click()
        
        # Select the appropriate  month
        css_selector = 'select#depart-calendar__bpk_calendar_nav_select'
        month_btn = Select(self.browser.find_element_by_css_selector(css_selector))
        month = date[-4:] + '-' + date[3:5] # Grab year and month from the input
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
    
    # Gather the results
    def scrape_page(self, city_from, city_to, date):
        
        # There's a chance that a flight cannot be found on that day
        
        try: # Check if there are no flights on that day
            css_selector_tag = "div.fss-fxo-legs"
            self.browser.find_element_by_css_selector(css_selector_tag)
            
            # No flight found!
            df = pd.DataFrame({"city_from" : city_from,
                               "city_to" : city_to,
                               "date" : date,
                               "flight" : "None",
                               "departure" : "None",
                               "arrival": "None",
                               "price" : 99999}, index = [0])
            
        except:
            # Grab the best offer (automatically sorted)
            xpath_tag = "//li[contains(@class, day-list-item.ItinerariesContainer)]//div//div//article"
            offer = self.browser.find_element_by_xpath(xpath_tag)
        
            # Get the price
            xpath_tag = "//a[contains(@class, 'CTASection__total-price')]"
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
            summary = self.browser.find_element_by_xpath(xpath_tag)
            
            # From the summary get the operator
            xpath_tag = "//span[contains(@class, 'ItineraryLeg__operated-by')]"
            operator = summary.find_element_by_xpath(xpath_tag).text
            
            # From the summary get the departure, arrival times and flight duration
            xpath_tag = "//div//div[contains(@class, 'ItineraryLeg__segment-times')]"
            times = summary.find_element_by_xpath(xpath_tag).text.split('\n')
            dep_time = times[0] # departure time
            arr_time = times[1] # Arrival time
            
            # concatenate results
            df = pd.DataFrame({"city_from" : city_from,
                               "city_to" : city_to,
                               "date" : date,
                               "flight" : operator,
                               "departure" : dep_time,
                               "arrival": arr_time,
                               "price" : price}, index = [0])
        
        
        return df
    
    
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
    
    
if __name__ == "__main__": 
      
    inputs = {
            "no_adults" : 2,
            "city_from" : ["Wroclaw"],
            "city_to" : ["Milan"],
            "departure_dates" : ["02/07/2019"]}
    
    f = Flight_Scraper()
    
    res = f.run(inputs)
    
                   
