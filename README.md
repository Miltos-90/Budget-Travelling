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

# Getting the Data
<a id="data_gathering"></a>

First things first, we need to define our destinations. We'll use the [Best places to travel in Europe - 2018](https://www.europeanbestdestinations.com/european-best-destinations-2018/), according to which the best destinations are the following:
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

Let us also assume that we will be travelling from July 1st, up to and including August 1st.

## Searching for hotels
<a id="hotel_gather"></a>

Obviously, to answer the question at hand, we need to know how much it costs to stay in a hotel, at any one of the cities listed above, at any time between July 1st to August 1st. Such data can be scraped from various websites available. Here, we'll use [Trivago](https://www.trivago.com/). 

There are a few steps to take:
1. Start Tor
2. Check for captchas or 'enable javascript' error messages (the latter tends to happen on Tor)
3. Set our country to USA (It's goof to ensure consistency of the text that appears on the website)
4. Set the currency to EUR
5. Enter the required destination
6. Select our check-in date from the drop-down menu
7. Select our check-out date from the dropdown menu
8. Grab the best offer

Of course, we have to repeat most steps to gather all the data we need. We'll also implement some 'waiting periods' in-between these actions, as there's no reason to strain the server with our requests. 
All of the above have been implemented in a scraper using Selenium and the Tor web browser (for info on getting Selenium to work nicely with Tor, check: https://stackoverflow.com/questions/15316304/open-tor-browser-with-selenium).


## Searching for flights
<a id="flight_gather"></a>
In a similar way, the data needed for the flights between the destinations can be gathered from [Skyscanner](https://www.skyscanner.com). 

The steps required are:
1. Start Tor
2. Check for captchas or 'enable javascript' error messages (the latter tends to happen on Tor)
3. Choose one-way flights
4. Set the currency to EUR
5. Enter the traveler info
6. Set inbound city
7. Set outbound city
8. Select flight date
9. Grab the result (if results exist)

These steps have also been implemented in a scrapper using Selenium and Tor.

## Gathering the data
<a id="scraper_work"></a>

The easiest thing to do to speed up the process of gathering the data is to set the Scrappers to run in parallel. These have been wrapped in another class, whose aim is to fire up the multiple scrapers (workers), distribute the queries among them, collect the results from each scraping session, and write them to a file.
Gathering the data is now simple:

```python
    # ----------------------- Scrape Hotels --------------------------------
    scraper = Scraper(filename     = 'hotels.csv',
                      scrape_type  = 'hotel',
                      max_job      = 4959,
                      no_processes =  cpu_count() - 1) # cpu_count() - 1
    
    
    scraper.run(destinations = ['Wroclaw', 'Bilbao', 'Colmar', 'Hvar', 'Riga', 'Milan', 'Athens', 'Budapest', 'Lisbon', 'Bohinj'],
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

 Now we have two files containing all the data:

```python
hotels = pd.read_excel('./data/hotels.xlsx')
hotels.head(5)
```

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
