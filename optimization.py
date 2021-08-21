import pandas as pd
import numpy as np

import pulp as plp
from itertools import product


# Return all past or future date_list from a given at_date for the entire trip
def remaining_date_list(date_array, cur_date, at_date_type):
    
    (cur_date_idx, ) = np.where(date_array == cur_date)
        
    if at_date_type == 'post':
        return date_list[cur_date_idx[0] + 1:]
    elif at_date_type == 'pre':
        return date_list[0: cur_date_idx[0]]
    else:
        raise ValueError('Wrong at_date type')


if __name__ == "__main__":
    
    # Read-in the data
    hotels = pd.read_excel('hotels.xlsx')
    flights = pd.read_excel('flights.xlsx')
    
    active_cities = ['Amsterdam', 'Wroclaw', 'Hvar', 'Riga', 'Milan', 'Athens', 'Budapest', 'Lisbon', 'Bohinj', 'Bilbao', 'Colmar']
    
    active_dates = ['07/01/2019', '08/01/2019', '07/02/2019', '07/03/2019', '07/04/2019', '07/05/2019', '07/06/2019', '07/07/2019',
       '07/08/2019', '07/09/2019', '07/10/2019', '07/11/2019', '07/12/2019', '07/13/2019', '07/14/2019', '07/15/2019',
       '07/16/2019', '07/17/2019', '07/18/2019', '07/19/2019', '07/20/2019', '07/21/2019', '07/22/2019', '07/23/2019',
       '07/24/2019', '07/25/2019', '07/26/2019', '07/27/2019', '07/28/2019', '07/29/2019', '07/30/2019', '07/31/2019']
    
    # active_cities = active_cities[0:7]
    # active_dates = active_dates[0:15] 
    
    flights = flights[flights['date'].isin(active_dates) & flights['city_from'].isin(active_cities) & flights['city_to'].isin(active_cities)]
    hotels = hotels[hotels['city'].isin(active_cities) & hotels['check_in'].isin(active_dates) & hotels['check_out'].isin(active_dates)]
    
    
    # Necessary constants
    start_date = "07/01/2019"
    end_date = "08/01/2019"
    home = "Amsterdam"
    min_stay = 4              # Minimum number of nights to spend in each city
    min_cities_to_visit = 7 
    
    
    # Make two dicts with cities and date_list (will be needed for the constraints)
    city_list = flights['city_from'].unique()
    date_list = flights['date'].unique()
    
    city_list.sort()
    date_list.sort()
    
    flights.set_index(['city_from', 'city_to', 'date'], inplace = True)
    hotels.set_index(['city', 'check_in', 'check_out'], inplace = True)
    
    # Instantiate problem
    model = plp.LpProblem("Traveling Costs", plp.LpMinimize)
    
    # Generate variables
    getting_flight = plp.LpVariable.dicts("getting_flight",
                                         ((from_city, to_city, at_date) \
                                          for from_city, to_city, at_date in flights.index),
                                         cat = 'Binary')
    
    sleeping_at = plp.LpVariable.dicts("sleeping_at",
                                         ((city, check_in, check_out) \
                                          for city, check_in, check_out in hotels.index),
                                         cat = 'Binary' )
    
    
    # Generate constraints
    
    
    # Starting flight only from AMS at 07/01/2019
    flights_from_home_at_start_date = [getting_flight[home, to_city, start_date]  \
                                       for to_city in city_list \
                                       if to_city != home]
    
    model += plp.lpSum(flights_from_home_at_start_date) == 1, \
    "Starting flight only from AMS at 07/01/2019 constraint 1/2" 
    
    flights_not_from_home_at_start_date = [getting_flight[from_city, to_city, start_date] \
                                           for from_city, to_city in product(city_list, city_list) \
                                           if from_city != to_city and from_city != home and to_city != home]
    
    model += plp.lpSum(flights_not_from_home_at_start_date) == 0, \
    "Starting flight only from AMS at 07/01/2019 constraint 2/2" 
   
    
    # Returning flight only to AMS at 08/01/2019
    flights_towards_home_on_end_date = [getting_flight[from_city, home, end_date] \
                                        for from_city in city_list \
                                        if from_city != home]
    
    model += plp.lpSum(flights_towards_home_on_end_date) == 1, \
    "Returning flight only to AMS at 08/01/2019 - constraint 1/2" 

    flights_not_towards_home_on_end_date = [getting_flight[from_city, to_city, end_date] \
                                            for from_city, to_city, at_date in flights.index \
                                            if to_city != home and at_date == end_date]
    
    model += plp.lpSum(flights_not_towards_home_on_end_date) == 0, \
    "Returning flight only to AMS at 08/01/2019 - constraint 2/2" 
                        
    
    # Manage connections: Flight at_date must match check_in at_date for inbound city and check_out at_date for the outbound city
    for from_city, to_city, flight_date in flights.index:
        
        # Is it the first flight we'll take as we start out?
        initial_flight = from_city == home and flight_date == start_date
        
        # Is it the final flight we'll take (going home)?
        final_flight = to_city == home and flight_date == end_date
        
        # Is it a flight from leaving from home, or returning to home?
        intermediate_flight = not(initial_flight) and not(final_flight)
        
       
        if intermediate_flight:
            current_flight = getting_flight[from_city, to_city, flight_date]
            
            prior_possible_checkouts_if_on_current_flight = [sleeping_at[from_city, from_date, flight_date] \
                                                             for from_date in remaining_date_list(date_list, flight_date, 'pre') \
                                                             if from_date != flight_date]
            
            post_possible_checkins_if_on_current_flight = [sleeping_at[to_city, flight_date, at_date] \
                                                            for at_date in remaining_date_list(date_list, flight_date, 'post') \
                                                            if at_date != flight_date]
            
            # Check out at_date <check-out> for city <city from> matching flight <city from> at at_date <check-out>
            model += current_flight <= plp.lpSum(prior_possible_checkouts_if_on_current_flight), \
            'Check out: traveling from {} to {} at {}'.format(from_city, to_city, flight_date)
        
            # Check in at_date <check-in> for city <city to> matching flight <city to> at at_date <check-in>
            model += current_flight <= plp.lpSum(post_possible_checkins_if_on_current_flight), \
            'Check_in: traveling from {} to {} at {}'.format(from_city, to_city, flight_date)
        
        
        elif initial_flight:
            # Check in at hotel of first city
            current_flight = getting_flight[from_city, to_city, flight_date]
            
            post_possible_checkins_if_on_current_flight = [sleeping_at[to_city, flight_date, from_date] \
                                                           for from_date in remaining_date_list(date_list, flight_date, 'post') \
                                                           if from_date != flight_date]
            
            model += current_flight == plp.lpSum(post_possible_checkins_if_on_current_flight), \
            'Check_in: traveling from {} to {} at {}'.format(from_city, to_city, flight_date)
        
        elif final_flight: 
            
            # date_before_flight  = date_list[np.where(date_list == flight_date)[0][0] - 1]
            
            current_flight = getting_flight[from_city, to_city, flight_date]
            
            prior_possible_checkouts_if_on_current_flight = [sleeping_at[from_city, from_date, flight_date] \
                                                             for from_date in remaining_date_list(date_list, flight_date, 'pre') \
                                                             if from_date != flight_date] # and from_date != date_before_flight]
            
            # Check out of hotel of last city 
            model += current_flight == plp.lpSum(prior_possible_checkouts_if_on_current_flight), \
            'Check_out: traveling from {} to {} at {}'.format(from_city, to_city, flight_date)
    
    
    # At most one visit (check in / check out pair) per city
    for city_name in city_list:
        if city_name != home:
            
            possible_checkins_at_city = [sleeping_at[city, check_in, check_out] \
                                         for city, check_in, check_out in hotels.index \
                                         if city == city_name]
            
            model += plp.lpSum(possible_checkins_at_city) <= 1, "At most one visit at {}".format(city_name)
         
    
    # At most one flight per date (apart from start and end dates, which need exactly one flight)
    for date in date_list:
        if date != start_date and date != end_date:
            
            possible_flights_at_date = [getting_flight[from_city, to_city, at_date] \
                                        for from_city, to_city, at_date in flights.index \
                                        if at_date == date]
            
            model += plp.lpSum(possible_flights_at_date) <= 1, "At most one flight at {}".format(date) 
             

    # Each city must be visited at most once = At most one flight connecting any two cities
    for city_1, city_2 in product(city_list, city_list):
        
        if city_1 != city_2 and city_1 != home and city_2 != home: # (home is the only city with two flights. One at the beginning and one at the end of the holidays)
            
            flights_from_city1_to_city2 = [getting_flight[city_1, city_2, at_date] for at_date in date_list]
            flights_from_city2_to_city1 = [getting_flight[city_2, city_1, at_date] for at_date in date_list]
            
            model += plp.lpSum(flights_from_city1_to_city2) + plp.lpSum(flights_from_city2_to_city1) <= 1, \
            "Travel between {} and {} at most once".format(city_1, city_2)
    
    
    # Minimum stay at each city = No flights allowed before and after N days
    for cur_city, cur_date in product(city_list, date_list):
        if cur_city != home and cur_date != end_date:
            
            flights_from_current_city_at_current_date = [getting_flight[from_city, to_city, at_date] \
                                                         for from_city, to_city, at_date in flights.index \
                                                         if to_city == cur_city and at_date == cur_date]
            
            no_flight_dates = remaining_date_list(date_list, cur_date, 'post')[0 : min_stay - 1] 
            
            forbidden_flights_from_current_city_at_current_date = [getting_flight[from_city, to_city, at_date] \
                                                                   for from_city, to_city, at_date in flights.index \
                                                                   if from_city == cur_city and at_date in no_flight_dates]
        
            x = plp.lpSum(flights_from_current_city_at_current_date)
            
            y = plp.lpSum(forbidden_flights_from_current_city_at_current_date)
        
            # If x == 1: y == 0 else if x == 0: y >= 0 -> y <= M(1-x)
            model += y <= 1e5 * (1 - x), 'Minimum stay at {} if visited on {}'.format(cur_city, cur_date)
            
    
    # No flights or checkins allowed after the start date for at least N days
    forbidden_flight_dates = remaining_date_list(date_list, start_date, 'post')[0 : min_stay - 1]
    
    forbidden_flights = [getting_flight[from_city, to_city, at_date] \
                         for from_city, to_city, at_date in flights.index \
                         if at_date in forbidden_flight_dates]
    
    model += plp.lpSum(forbidden_flights) == 0, 'Minimum stay on first node - flights'
        
    
    # No checkins allowed after the start date for at least N days
    cur_date = start_date
    
    for cur_city in city_list:    
        
        if cur_city != home:
            
            forbidden_checkins = [sleeping_at[cur_city, check_in, check_out] \
                               for cur_city, check_in, check_out in hotels.index \
                               if check_in == cur_date and check_out in forbidden_flight_dates]
            
            model += plp.lpSum(forbidden_checkins) == 0, "Minimum stay on first node - hotels at {}".format(cur_city)
    
    
    # At least (or exactly - its the same when minimizing cost) N cities must be visited: at least N check ins + at least (N + 1) flights: + 1 for the return at home node
    total_checkins = [sleeping_at[city, from_date, to_date] \
                        for city, from_date, to_date in hotels.index if city != home]
    
    model += plp.lpSum(total_checkins) >= min_cities_to_visit, "No cities to visit"
    
    total_flights = [getting_flight[from_city, to_city, at_date] \
                       for from_city, to_city, at_date in flights.index]
        
    model += plp.lpSum(total_flights) >= min_cities_to_visit + 1, 'No flights to take'
    
    
    # Make sure number of flights agrees with number of check-ins
    model += plp.lpSum(total_checkins) + 1 == plp.lpSum(total_flights), 'Match no flights with no cities'
    
    
    
    # Generate objective function
    total_flight_costs = [getting_flight[from_city, to_city, at_date] * flights.loc[(from_city, to_city, at_date), "price"] \
                        for from_city, to_city, at_date in flights.index]
    
    total_hotel_costs = [sleeping_at[city, check_in, check_out] * hotels.loc[(city, check_in, check_out), "price"] \
                        for city, check_in, check_out in hotels.index]
    
    
    model += plp.lpSum(total_flight_costs + total_hotel_costs), "Total cost minimization"
    
    
    model.writeLP("out.lp")
    
    
    from time import time
    
    t = time()
    model.solve() # plp.PULP_CBC_CMD(maxSeconds = 300))
    elapsed = time() - t
    
    print("-------------------------")
    print("Status =", plp.LpStatus[model.status])
    print("-------------------------")
    print("Elasped time [s] =", round(elapsed, 3))
    print("-------------------------")
#    for v in model.variables():
#        if v.varValue>0:
#            print(v.name, "=", v.varValue)
#    print("-------------------------")
    print("Total cost =", model.objective.value())
    print("-------------------------")
    # getting the value of the constraint  
    #for constraint in model.constraints:
    #    print(model.constraints[constraint].name, model.constraints[constraint].value() - model.constraints[constraint].constant)#
    
    
    # Get results
    
    sol_flights = [flights.loc[from_city, to_city, at_date] \
                   for from_city, to_city, at_date in flights.index \
                   if getting_flight[from_city, to_city, at_date].varValue == 1]
    
    sol_flights = pd.concat(sol_flights, axis = 1).T
    sol_flights.index = sol_flights.index.set_names(['city_from', 'city_to', 'date'])
    sol_flights.reset_index(inplace = True)
    
    sol_hotels = [hotels.loc[city, check_in, check_out] \
                  for city, check_in, check_out in hotels.index \
                  if sleeping_at[city, check_in, check_out].varValue == 1]
    
    sol_hotels = pd.concat(sol_hotels, axis = 1).T
    sol_hotels.index = sol_hotels.index.set_names(['city_from', 'city_to', 'date'])
    sol_hotels.reset_index(inplace = True)
    
    print("Flight Schedule")
    print(sol_flights, '\n\n')
    print("Hotel Schedule")
    print(sol_hotels)
    
    