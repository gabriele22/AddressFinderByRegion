import sys
import threading
import random
import math
import re
import requests
import toml
import pandas as pd
import more_itertools 
import plotly.express as px
import plotly.graph_objects as go
from progress.bar import IncrementalBar


def radiants_distance(lat1, lon1, lat2, lon2):
    '''return differenze from point in latitude and longitude'''
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Applicare la formula dell'averseno per calcolare la distanza angolare
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return c

def plot_points_with_perimeter(lat_c, lon_c,
                               per_lat: list, per_lon: list,
                               points_lat: list, points_lon: list):
    '''plot point in blue in black perimeter'''
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
                        lat=per_lat,
                        lon=per_lon,
                        marker=go.scattermapbox.Marker(
                                size=8,
                                color='rgb(0, 0, 0)',
                                opacity=0.7
                            )
                    )
    )

    fig.add_trace(go.Scattermapbox(
                        lat=points_lat,
                        lon=points_lon,
                        marker=go.scattermapbox.Marker(
                                size=5,
                                color='rgb(0, 50, 200)',
                                opacity=0.9
                            )
                    )
    )
    #TODO zoom to points
    fig.update_layout(mapbox_style="open-street-map",
                        autosize=True,
                        hovermode='closest',
                        showlegend=False
    )
    fig.show()

def get_rnd_point_in_limits(lat_c, lon_c, raggio,
                            min_lat=-math.pi / 2 , max_lat=math.pi / 2,
                            min_lon=-math.pi,max_lon=math.pi, n=10):
    '''return n random point in limit defined as input parameter '''
    punti = []

    # Iterare fino a che non si raggiunge il numero desiderato di punti
    while len(punti) < n:
        # Generare una latitudine e una longitudine casuali tra -$\pi$/2 e $\pi$/2 radianti
        lat_p = random.uniform(min_lat, max_lat)
        lon_p = random.uniform(min_lon, max_lon)

        # Calcolare la distanza tra il punto casuale e il centro dell'area circolare
        distanza = radiants_distance(lat_c, lon_c, lat_p, lon_p)

        # Se la distanza è minore o uguale al raggio, aggiungere il punto alla lista dei punti
        if distanza <= raggio:
            punti.append((math.degrees(lat_p), math.degrees(lon_p)))

    # Restituire la lista dei punti in gradi
    return punti


def get_rnd_point_on_circle_and_print_map(lat_c, lon_c, raggio, n = 100):
    '''return n random point on a circle defined by latitude, longitude and radius (in radiants)'''
    # Creare una lista vuota per contenere i punti
    punti = []
    punti_lat_perimeto_cerchio = []
    punti_lon_perimeto_cerchio = []

    n_punti_perimetro = 100
    # Calcolare l'angolo tra ogni punto in radianti
    angolo = 2 * math.pi / n_punti_perimetro

    # Iterare su ogni punto
    for i in range(n_punti_perimetro):
        # Calcolare la latitudine e la longitudine del punto in radianti
        lat_p = math.asin(math.sin(lat_c) * math.cos(raggio) + math.cos(lat_c) * math.sin(raggio) * math.cos(i * angolo))
        lon_p = lon_c + math.atan2(math.sin(i * angolo) * math.sin(raggio) * math.cos(lat_c), math.cos(raggio) - math.sin(lat_c) * math.sin(lat_p))
        punti_lat_perimeto_cerchio.append(lat_p)
        punti_lon_perimeto_cerchio.append(lon_p)
        # Convertire la latitudine e la longitudine del punto in gradi
        lat_p = math.degrees(lat_p)
        lon_p = math.degrees(lon_p)

        #punti.append((lat_p, lon_p))

    min_lat = min(punti_lat_perimeto_cerchio)
    max_lat = max(punti_lat_perimeto_cerchio)
    min_lon = min(punti_lon_perimeto_cerchio)
    max_lon = max(punti_lon_perimeto_cerchio)

    punti_rnd = get_rnd_point_in_limits(lat_c, lon_c, raggio,
                                        min_lat, max_lat, min_lon, max_lon, n)
    for punto_rnd in punti_rnd:
        punti.append(punto_rnd)

    per_lat = [math.degrees(i) for i in punti_lat_perimeto_cerchio ]
    per_lon = [math.degrees(i) for i in punti_lon_perimeto_cerchio ]
    rnd_lat = [l[0] for l in punti ]
    rnd_lon = [l[1] for l in punti ]

    #plot point and perimeter points
    plot_points_with_perimeter(math.degrees(lat_c), math.degrees(lon_c),
                               per_lat, per_lon, rnd_lat, rnd_lon)

    # Restituire la lista dei punti
    return punti


def get_address_by_lat_and_long(api_key_bing, url, lat, lon):
    '''return address and postal code near point idenitified by latitude and longitude'''
    list_of_results = []
    url = f"{url}{lat},{lon}"

    # Definisco i parametri della richiesta inversa
    params = {
        "includeEntityTypes":  "Address",
        "includeNeighborhood": 1,
        "key": api_key_bing
    }

    # Invio la richiesta inversa e ottengo la risposta
    response = requests.get(url, params=params)

    # Controllo se la richiesta inversa è andata a buon fine
    if response.status_code == 200:
        data = None
        data_status_code = None

        # Estraggo i dati JSON dalla risposta inversa
        try:
            data = response.json()
            data_status_code = data["statusCode"]
        except Exception as err:
            print(f'{err=}')
        
        # Controllo se ci sono risultati validi
        if data_status_code == 200 and data["resourceSets"][0]["estimatedTotal"] > 0:
            
            # Estraggo tutti i risultati (i numeri civici)
            results = data["resourceSets"][0]["resources"]
            # Per ogni risultato, estraggo e stampo il numero civico e l'indirizzo completo
            for result in results:
                indirizzo_e_numero_civico = result["address"]["addressLine"]
                numero_civico = [int(s) for s in re.findall(r' \d+', indirizzo_e_numero_civico)]
                indirizzo_completo = result["address"]["formattedAddress"]
                regione = result["address"]["adminDistrict"]
                provincia = result["address"]["adminDistrict2"]
                comune = result["address"]["locality"]
                coordinate = result["geocodePoints"][0]["coordinates"]
                #print(data["resourceSets"][0])

                list_of_results.append( ( regione, provincia, comune, indirizzo_completo, indirizzo_e_numero_civico, numero_civico, coordinate))
        else:
            #print(f"Non sono stati trovati risultati validi, la richiesta alla mappe bing ha risposto con stato={data_status_code}")
            return data_status_code if data_status_code else 500
    else:
        #print(f"Errore nella richiesta di recupero indirizzi: {response.status_code}")
        return data_status_code if data_status_code else 500


    return list_of_results




def find_only_address_in_town_and_with_number(api_key_bing,url,
                                                  points_for_request,
                                                  town_ref,
                                                  provinces,
                                                  towns,
                                                  address_complete,
                                                  address_lite,
                                                  latitudes,
                                                  longitudes,
                                                  response_errors ):  
    '''filter response to get only desired province and only point with number, also add response details to specific list'''
    with IncrementalBar('recupero indirizzi...', max=len(points_for_request)) as p_bar:
        for item_lat, item_lng in points_for_request:

            address_response = get_address_by_lat_and_long(api_key_bing,url, item_lat,  item_lng)

            if (isinstance(address_response, list) and len(address_response)>0):
                for (_ , provincia_resp, comune_resp, indirizzo_completo_resp, indirizzo_e_numero_civico_resp, numero_civico_resp, coordinate_resp) in address_response:
                    if indirizzo_completo_resp and comune_resp == town_ref and len(numero_civico_resp) > 0 and numero_civico_resp[0] > 0 :
                        provinces.append(provincia_resp)
                        towns.append(comune_resp)
                        address_complete.append(indirizzo_completo_resp)
                        address_lite.append(indirizzo_e_numero_civico_resp)
                        latitudes.append(coordinate_resp[0])
                        longitudes.append(coordinate_resp[1])
            else:
                response_errors.append(address_response)


            p_bar.next()

def recover_address_in_a_town( api_key_bing, url, town_req, radius = 10, precision=10, num_threads=2 ):
    '''retrieve ddress_number from a city name using bing maps api'''

    provinces = []
    towns = []
    address_complete = []
    address_lite = []
    latitudes = []
    longitueds = []
    response_errors = []

    # Definisco i parametri della richiesta
    params = {
        "locality": town_req,
        "key": api_key_bing
    }

    # Invio la richiesta e ottengo la risposta
    response = requests.get(url, params=params)

    # Controllo se la richiesta è andata a buon fine
    if response.status_code == 200:
        # Estraggo i dati JSON dalla risposta
        data = None
        data_status_code = None
        try:
            data = response.json()
            data_status_code = data["statusCode"]
        except Exception as err:
            print(f'{err=}')

        # Controllo se ci sono risultati validi
        if data_status_code == 200 and data["resourceSets"][0]["estimatedTotal"] > 0:
            
            # Estraggo il primo risultato (il più rilevante)
            result = data["resourceSets"][0]["resources"][0]

            # Estraggo le coordinate geografiche del comune
            lat = result["point"]["coordinates"][0]
            lng = result["point"]["coordinates"][1]

            # Stampo le coordinate geografiche della regione
            print(f"Le coordinate geografiche di riferimento usate per {town_req} sono: {lat}, {lng}")
            points = []
            #recupero il admmin_district_ref della regione per filtare successivamente eventuali punti di altri regioni
            (_, _, town_ref,  _, _, _, _ ) = get_address_by_lat_and_long(api_key_bing,url,lat,lng)[0]

            if town_ref:
                points = get_rnd_point_on_circle_and_print_map(
                    math.radians(lat), math.radians(lng), math.radians(radius), precision)


                user_ctrl =input('in base ai punti visualizzati sulla mappa nel browser, vuoi procedere con le richieste per ottenere gli indirizzi? (s/n)')
                if(user_ctrl == 's' or user_ctrl == 'S'):
                    diveded_points = list(more_itertools.chunked(points, len(points) // num_threads))
                    threads = list()

                    for sub_points in diveded_points:
                        t = threading.Thread(target=find_only_address_in_town_and_with_number,args=
                                                (api_key_bing,
                                                url,
                                                sub_points,
                                                town_ref,
                                                provinces,
                                                towns,
                                                address_complete,
                                                address_lite,
                                                latitudes,
                                                longitueds,
                                                response_errors )
                                                )

                        threads.append(t)
                        t.start()

                    for t in threads:
                        t.join()

            else:
                print(f"Fallito recupero informazioni in {town_ref}, codice risposta http: {data_status_code}")                
        else:
            # Stampo un messaggio di errore se non ci sono risultati validi
            print(f"Nessun risultato trovato in {town_ref}")
    else:
        # Stampo un messaggio di errore se la richiesta non è andata a buon fine
        print(f"Errore nella richiesta: {response.status_code}")

    df_address_region = pd.DataFrame()
    df_address_region['Provincia'] = provinces
    df_address_region['Comune'] = towns
    df_address_region['Indirizzo completo'] = address_complete
    df_address_region['Indirizzo'] = address_lite
    df_address_region['latitudine'] = latitudes
    df_address_region['longitudine'] = longitueds

    if len(response_errors)> 0:
        print(f"{len(response_errors)} su {precision} richieste non hanno dato risposta")
        print(f"{precision - (len(response_errors) + len(address_complete))} su {precision} richieste hanno risposto con un indirizzo NON valido")

    df_address_region.drop_duplicates(inplace=True)
    # Stampo il numero dei risultati trovati
    if len(address_complete)> 0:
        print(f"Trovati {len(address_complete)} numeri civici (senza duplicati) all'interno di un cerchio di raggio {radius*111} km con centro {town_ref} ({lat}, {lng})")

    #rimozione indirizzi duplicati
    df_address_region.drop_duplicates(inplace=True)
    df_address_region.sort_values(by=['Comune', 'Indirizzo completo'], inplace=True)
    return df_address_region


def main():
    """ main """
    # Load the TOML data into a Python dictionary
    with open("config.toml", encoding="utf-8") as f:
        data = toml.load(f)

    api_key = data['api_key']
    base_bing_url = data['bing_url']
    search_precision = data['search_precision']
    num_threads = data['num_threads']

    town = input('Nome comune: ')
    radius = input('Raggio di ricerca(km): ')
    ## a kind of km approximation in degrees
    dimension_searc_area = int(radius)/111
    print(dimension_searc_area)

    df_town = recover_address_in_a_town(api_key,base_bing_url,
                                                            town,
                                                            dimension_searc_area,
                                                            search_precision,
                                                            num_threads)

    df_town.to_csv(f"Indirizzi_{town}.csv", sep=';', index=False, encoding='utf-8' )

    sys.exit(0)

if __name__ == '__main__':
    sys.exit(main())
