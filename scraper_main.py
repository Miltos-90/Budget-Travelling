from hotel_scraper import Hotel_Scraper
from flight_scraper import Flight_Scraper

from time import sleep
from tbselenium.utils import start_xvfb, stop_xvfb # pip install Xvfb

from multiprocessing import Pool, cpu_count, Manager
from datetime import datetime as dt
from datetime import timedelta
from itertools import product

import pandas as pd
from functools import partial


class Scraper(object):
    
    # Initialize
    def __init__(self, filename, scrape_type, max_job, no_processes, queries_per_process = 1):
        
        self.scrape_type = scrape_type
        self.max_job = max_job 
        self.no_processes = no_processes 
        self.queries_per_process = queries_per_process
        self.filename = filename
        
        # Input check
        if self.scrape_type not in ['hotel', 'flight']:
            raise ValueError('Invalid scraper type')
            
        # Date format for the flight and hotel scrapers
        self.date_format = "%d/%m/%Y"


    # Return a list of equal query-sized inputs for the flight scraper processes
    @staticmethod
    def flight_scraper_input_list(destinations, start_date, end_date, no_adults, date_format):
        
        # Parse starting and ending dates for the trip
        tStart = dt.strptime(start_date, date_format) 
        tEnd = dt.strptime(end_date, date_format)
        
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
            
            city_from = elem[0][0]
            city_to = elem[0][1]
            departure_dates = list(elem[1])
            
            inputs = {"no_adults" : no_adults,
                      "city_from" : [city_from],
                      "city_to" : [city_to],
                      "departure_dates" : departure_dates,
                      "id" : idx}
            
            flight_scraper_inputs.append(inputs)
            
        return flight_scraper_inputs
        
    
    # Return a list of inputs for the hotel scraper processes
    @staticmethod
    def hotel_scraper_input_list(destinations, start_date, end_date, no_adults, date_format):
        
        # Parse starting and ending dates for the trip
        tStart = dt.strptime(start_date, date_format) 
        tEnd = dt.strptime(end_date, date_format)
        
        date_pairs = [] # Empty list to hold the results
        
        # Derive a day range to loop from for the start date
        tRange_outer = range(0, (tEnd - tStart).days + 1)
            
        # Loop through all the date pairs, and append them to the list
        for tStart_outer in (tStart + timedelta(n) for n in tRange_outer):
                
            # Derive a day range to loop from for the end date
            tRange_inner = range(1, (tEnd - tStart_outer).days + 1)
                
            for date in (tStart_outer + timedelta(n) for n in tRange_inner):
                tCursor_end = dt.strftime(date, date_format)
                tCursor_start = dt.strftime(tStart_outer, date_format)
                date_pairs.append((tCursor_start, tCursor_end))
        
        
        # Iterate over each destination and each date-pair to create a dataframe
        inputs = [] # Empty list to hold the results
        
        for idx, (destination, date_pair) in enumerate(product(destinations, date_pairs)):
            
            # Generate a dictionary with the destination included, and a unique set of start dates
            temp = date_pair.to_dict('list')
            temp["no_adults"] = no_adults
            temp['destinations'] = [destination]
            temp["id"] = idx
            
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
    
    
    # Worker to scrape for hotel data
    def worker(self, job_id, args, queue): 
        
        # Start virtual display
        xvfb_display = start_xvfb()
        
        # Start up the appropriate scraper instance
        if self.scrape_type == 'hotel':
            scraper = Hotel_Scraper()
            
        elif self.scrape_type == 'flight':
            scraper = Flight_Scraper()
            
        # Put it to work
        try:
            df = scraper.run(args)
        except:
            # This exception will pop-up due to random delays to TOR..
            scraper.browser.quit()
            
            # Put an empty dataframe to the queue
            queue.put(pd.DataFrame())
        else:
            # Put the result to the queue
            queue.put((job_id, df))
        
        # Close the virtual display
        stop_xvfb(xvfb_display)
    
        return
        
    
    # Listen for messages on the queue (q) and writes to file
    @staticmethod
    def listener(filename, queue, processes_running):
        
        # While the processes are still running or the queue is not empty:
        while (not processes_running.ready()) or (not queue.empty()):
    
            # Grab an item from the queue
            df = queue.get(block = True)
            
            if not df.empty:
                # Write to file
                print('Writing ', df['id'], end = ' to file ... ')
                
                with open(filename, 'a') as f:
                    df.to_csv(f, header=False)
                
                print('Done')
            
            # Wait a bit
            sleep(2)
        
        return
        
    
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


if __name__ == "__main__":
    # Max no of jobs:
    # Hotels: 4960
    # Flights: 2880
    
    # ----------------------- Scrape Hotels --------------------------------
    scraper = Scraper(filename = 'hotels.csv',
                      scrape_type = 'hotel',
                      max_job = 4959, # For hotels: 4960
                      no_processes =  cpu_count() - 1) # cpu_count() - 1
    
    
    scraper.run(destinations = ['Wroclaw', 'Bilbao', 'Colmar', 'Hvar', 'Riga', 'Milan', 'Athens', 'Budapest', 'Lisbon', 'Bohinj'], # https://www.europeanbestdestinations.com/european-best-destinations-2018/ 
                start_date = "01/07/2019", 
                end_date = "01/08/2019", 
                no_adults = 2)
    
    
    # ----------------------- Scrape Flights --------------------------------
    scraper = Scraper(filename = 'flights.csv',
                      scrape_type = 'flight',
                      max_job = 2879,
    				  no_processes = cpu_count() - 1)
        
        
    scraper.run(destinations = ['Wroclaw', 'Bilbao', 'Colmar', 'Hvar', 'Riga', 'Milan', 'Athens', 'Budapest', 'Lisbon', 'Bohinj'], # Add Home: Amsterdam
                start_date = "01/07/2019", 
                end_date = "01/08/2019", 
                no_adults = 2)
    



# TODO: Write that there's no reason to simulate user behaviour (mouse movements( with the parallel setup we've made
    # we just need to make sure we won's strain the server (no reason to do so). Also write that skyscanner automatically
    # finds the closest airport to the city we want to visit!!
# TODO: Uncomment crossed out enter_room_info() function in hotel scraper (deleted it because it was not working)
