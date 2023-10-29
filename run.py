import sys
import random
import math
import pandas as pd
import requests
import toml
import plotly.express as px
from progress.bar import IncrementalBar


def radiants_distance(lat1, lon1, lat2, lon2):
    '''return differenze from point in latitude and longitude'''
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Applicare la formula dell'averseno per calcolare la distanza angolare
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return c


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

    # Calcolare l'angolo tra ogni punto in radianti
    angolo = 2 * math.pi / n

    # Iterare su ogni punto
    for i in range(n):
        # Calcolare la latitudine e la longitudine del punto in radianti
        lat_p = math.asin(math.sin(lat_c) * math.cos(raggio) + math.cos(lat_c) * math.sin(raggio) * math.cos(i * angolo))
        lon_p = lon_c + math.atan2(math.sin(i * angolo) * math.sin(raggio) * math.cos(lat_c), math.cos(raggio) - math.sin(lat_c) * math.sin(lat_p))
        punti_lat_perimeto_cerchio.append(lat_p)
        punti_lon_perimeto_cerchio.append(lon_p)
        # Convertire la latitudine e la longitudine del punto in gradi
        lat_p = math.degrees(lat_p)
        lon_p = math.degrees(lon_p)

        punti.append((lat_p, lon_p))

    min_lat = min(punti_lat_perimeto_cerchio)
    max_lat = max(punti_lat_perimeto_cerchio)
    min_lon = min(punti_lon_perimeto_cerchio)
    max_lon = max(punti_lon_perimeto_cerchio)

    punti_rnd = get_rnd_point_in_limits(lat_c, lon_c, raggio,min_lat, max_lat, min_lon, max_lon, n*10)
    for punto_rnd in punti_rnd:
        punti.append(punto_rnd)


    df_rnd = pd.DataFrame()
    df_rnd['lat'] = [l[0] for l in punti ]
    df_rnd['lon'] = [l[1] for l in punti ]

    fig2 = px.scatter_mapbox(df_rnd,
                        lat="lat",
                        lon="lon",
                        color_discrete_sequence=["blue"],
                        zoom=10,
                        height=1000
                    )
    fig2.update_layout(mapbox_style="open-street-map")
    fig2.show()

    # Restituire la lista dei punti
    return punti

def get_address_by_lat_and_long(api_key_bing,maps_url, lat, long):
    '''return address and postal code near point idenitified by latitude and longitude'''
    list_of_results = []
    url = f"{maps_url}{lat},{long}"

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
        # Estraggo i dati JSON dalla risposta inversa
        try:
            data = response.json()
        except Exception as err:
            print(f'{err=}')
        data_status_code = data["statusCode"]
        # Controllo se ci sono risultati validi
        if data_status_code == 200:
            # Estraggo tutti i risultati (i numeri civici)
            results = data["resourceSets"][0]["resources"]
            # Per ogni risultato, estraggo e stampo il numero civico e l'indirizzo completo
            for result in results:
                indirizzo_e_numero_civico = result["address"]["addressLine"]
                indirizzo_completo = result["address"]["formattedAddress"]
                localita = result["address"]["locality"]
                #codice_postale = result["address"]['postalCode']
                # print(f"{indirizzo_e_numero_civico=}")
                #print(f"{indirizzo_completo=}")
                list_of_results.append( ( indirizzo_e_numero_civico, indirizzo_completo, localita))
        else:
            # Stampo un messaggio di errore se non ci sono risultati validi
            print(f"Non sono stati trovati risultati validi,\
                   la richiesta alla mappe bing ha risposto con stato={data_status_code}")
    else:
        # Stampo un messaggio di errore se la richiesta inversa non è andata a buon fine
        print(f"Errore nella richiesta di recupero indirizzi: {response.status_code}")

    return list_of_results


def recover_address_number_from_city_name ( api_key_bing,
                                           maps_url,
                                           city_name,
                                           radius = 10,
                                           precision=10 ):
    '''retrieve ddress_number from a city name using bing maps api'''

    address_of_city = []
    address_complete = []

    # Definisco i parametri della richiesta
    params = {
        "locality": city_name,
        "key": api_key_bing
    }

    # Invio la richiesta e ottengo la risposta
    response = requests.get(maps_url, params=params)

    # Controllo se la richiesta è andata a buon fine
    if response.status_code == 200:
        # Estraggo i dati JSON dalla risposta
        data = response.json()

        # Controllo se ci sono risultati validi
        if data["statusCode"] == 200:

            # Estraggo il primo risultato (il più rilevante)
            result = data["resourceSets"][0]["resources"][0]

            # Estraggo le coordinate geografiche del comune
            lat = result["point"]["coordinates"][0]
            lng = result["point"]["coordinates"][1]

            # Stampo le coordinate geografiche del comune
            print(f"Le coordinate geografiche di {city_name} sono: {lat}, {lng}")
            lista_coordinate = []
            #recupero la localita del comune per filtare successivamente punti di altri comuni
            (_, _, localita) = get_address_by_lat_and_long(api_key_bing,maps_url, lat, lng)[0]

            lista_coordinate.append( (lat, lng) )
            lista_coordinate = get_rnd_point_on_circle_and_print_map(
                math.radians(lat), math.radians(lng), math.radians(radius), precision)

            user_ctrl =input('in base ai punti visualizzati sulla mappa nel browser, vuoi procedere con le richieste per ottenere gli indirizzi? (s/n)')
            if(user_ctrl == 's' or user_ctrl == 'S'):
                with IncrementalBar('recupero indirizzi...', max=len(lista_coordinate)) as p_bar:
                    for item_lat, item_lng in lista_coordinate:

                        response_list = get_address_by_lat_and_long(
                            api_key_bing, maps_url,item_lat, item_lng)

                        for (indirizzo_e_numero_civico,indirizzo_completo,localita_punto) in response_list:
                            if localita_punto == localita:
                                address_of_city.append(indirizzo_e_numero_civico)
                                address_complete.append(indirizzo_completo)
                        p_bar.next()


        else:
            # Stampo un messaggio di errore se non ci sono risultati validi
            print(f"Nessun risultato trovato per {city_name}")
    else:
        # Stampo un messaggio di errore se la richiesta non è andata a buon fine
        print(f"Errore nella richiesta: {response.status_code}")


                            # Stampo il numero dei risultati trovati
    if len(address_of_city)> 0:
        print(f"Trovati {len(address_of_city)} numeri civici all'interno di un cerchio di raggio {radius} gradi con centro {city_name} ({lat}, {lng})")


    return (address_of_city, address_complete)


def main():
    """ main """
    # Load the TOML data into a Python dictionary
    with open("config.toml", encoding="utf-8") as f:
        data = toml.load(f)

    print(data['api_key'])
    print(data['bing_url'])
    print(data['dimension_searc_area'])
    print(data['search_precision'])
    api_key = data['api_key']
    base_bing_url = data['bing_url']

    dimension_searc_area = data['dimension_searc_area']
    search_precision = data['search_precision']

    city = input('Nome comune: ')

    (address_with_number, address_complete)  = recover_address_number_from_city_name(
        api_key,base_bing_url, city,dimension_searc_area, search_precision)

    df_city = pd.DataFrame()
    df_city['indirizzo'] = address_complete
    df_city['Via_e_civico'] = address_with_number
    df_city.to_csv(f"Indirizzi_{city}.csv", sep=';', index=False, encoding='utf-8' )

    sys.exit(0)

if __name__ == '__main__':
    sys.exit(main())

