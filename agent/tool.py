import os
import shutil
import sqlite3

import requests
import pandas as pd
import requests

from langchain_core.tools import tool
import us

from typing import List,Dict

from map_utils import arcgis_to_gmaps, gmaps_to_arcgis, get_distance_google_maps
from googleplaces import GooglePlaces, types, lang 
import requests 
import json 
import googlemaps

from dotenv import load_dotenv
load_dotenv("../.env")


GOOGLE_MAPS_API_KEY=os.environ['GOOGLE_MAPS_API_KEY']

@tool
def get_disaster_declaration(state: str,
                             declarationType: str,
                             limit: int = 10) -> str:
    """
       Retrieves formatted disaster declaration summaries from the OpenFEMA API for a specified state and type.

       Connects to the OpenFEMA Disaster Declarations Summaries API, fetching disaster declarations by state and type,
       and formats results into readable strings.

       Parameters:
       ----------
       state : str
           Two-letter state code (e.g., "TX") Just use the state ID
       declarationType : str
           Declaration type, such as "DR" (major disaster) or "EM" (emergency).
       limit : int, optional
           Max number of results (default is 10).

       Returns:
       -------
       list of str
           A list of formatted summaries, each containing:
           - Disaster ID, Declaration String, State, Title, Type, Dates, Area, Programs Declared, Region, Last Refresh Date.
           If request fails, returns an error message.

       Examples:
       --------
       >>> get_disaster_declaration(state="TX", declarationType="DR", limit=10)
       ["Disaster ID: 5530...", "Disaster ID: 5531..."]

       Notes:
       ------
       - Uses pagination; `limit` restricts records per call.
       - Requires `requests` library.
       """
    base_url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"

    # Parameters for the API request
    params = {
        "state": state,                     # Filter by state (e.g., Texas)
        "declarationType": declarationType, # Declaration type (e.g., DR for major disaster)
    }

    try:
        # Make the request
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Convert response to JSON
        data = response.json()
        disaster_summaries = data.get("DisasterDeclarationsSummaries", [])

        # Format each disaster entry as a string
        formatted_disasters = []
        for disaster in disaster_summaries:

            if state== disaster.get('state'):
                formatted_disasters.append(
                    [f"Disaster ID: {disaster.get('disasterNumber')}\n"
                    f"Declaration String: {disaster.get('femaDeclarationString')}\n"
                    f"State: {disaster.get('state')}\n"
                    f"Declaration Type: {disaster.get('declarationType')}\n"
                    f"Title: {disaster.get('declarationTitle')}\n"
                    f"Incident Type: {disaster.get('incidentType')}\n"
                    f"Declaration Date: {disaster.get('declarationDate')}\n"
                    f"Incident Begin Date: {disaster.get('incidentBeginDate')}\n"
                    f"Incident End Date: {disaster.get('incidentEndDate')}\n"
                    f"Programs Declared: "
                    f"IH: {disaster.get('ihProgramDeclared')}, "
                    f"IA: {disaster.get('iaProgramDeclared')}, "
                    f"PA: {disaster.get('paProgramDeclared')}, "
                    f"HM: {disaster.get('hmProgramDeclared')}\n"
                    f"Region: {disaster.get('region')}\n"
                    f"Last Refresh: {disaster.get('lastRefresh')}\n"]
                )

        print(len(formatted_disasters[-limit:]))

        formatted_disasters = formatted_disasters[-limit:]

        result = ""

        for disaster in formatted_disasters:
            result += f"{disaster[0]}\n"

        return result
    except requests.RequestException as e:
        return [f"Failed to retrieve data: {e}"]


@tool
def is_in_evacuation_zone(state: str,
                          address: str) -> str:
    
    """
    Determines if a given location is within an evacuation zone using state-specific APIs.

    Parameters:
    ----------
    state : str
        State code (e.g., "FL" for Florida, "TX" for Texas).
    adsress : str
        Address of the location

    Returns:
    --------
    str
        A message indicating the evacuation zone(s) or an error message if data retrieval fails.

    Notes:
    ------
    - For Florida (FL): Uses a point-based query (`esriGeometryPoint`) to check evacuation zones.
    - For Texas (TX): Uses a small bounding box (`esriGeometryEnvelope`) with an intersect relationship to approximate point queries.

    Example:
    --------
    >>> is_in_evacuation_zone("FL", 27.994402, -81.760254)
    'Your location is in Evacuation Zone(s) A.'
    """

    # Define query parameters
    params = {
        "f": "json", 
        "geometry": "",  
        "geometryType": "",  
        "spatialRel": "",  
        "outFields": "*",  
        "where": "1=1", 
        "defaultSR": 102100  
    }

    # TODO Decode location
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    geocode_result = gmaps.geocode(address)

    if geocode_result:

        latitude = geocode_result[0]['geometry']['location']['lat']
        longitude = geocode_result[0]['geometry']['location']['lng']

        geometry_user_arcgis = (gmaps_to_arcgis(latitude, longitude))
        
        if state == "FL":
            base_url = "https://services.arcgis.com/3wFbqsFPLeKqOlIK/arcgis/rest/services/KYZ_ZL_Vector_Enriched_Calculated_20230608/FeatureServer/28/query"
            params["geometry"] = f"{geometry_user_arcgis[0]},{geometry_user_arcgis[1]}"
            params["geometryType"] = "esriGeometryPoint"
            params["spatialRel"] = "esriSpatialRelWithin"
            
            
        elif state == "TX":
            base_url = "https://services.arcgis.com/su8ic9KbA7PYVxPS/arcgis/rest/services/HurricaneEvac_Zones/FeatureServer/0/query"

            offset = 10000  

            xmin = geometry_user_arcgis[0] - offset
            ymin = geometry_user_arcgis[1] - offset
            xmax = geometry_user_arcgis[0] + offset
            ymax = geometry_user_arcgis[1] + offset

            params["geometry"] = f"{xmin},{ymin},{xmax},{ymax}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"

        # Make the request
        response = requests.get(base_url, params=params)
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            zone_features = data.get("features", [])

            if zone_features:
                res_zones = set()
                for feature in zone_features:
                    attributes = feature["attributes"]
                    zone = attributes.get("Zone") or attributes.get("EZone")
                    #status = attributes.get("STATUS", '')
                    res_zones.add(zone)

                return f"Your location is in Evacuation Zone(s) {zone}."
            else:
                return "The location is not within an evacuation zone."

    print(f"Failed to retrieve data: {response.status_code}")
    
    return f"Failed to retrieve data: {response.status_code}"

def extract_alerts(data):
    alerts = []
    
    for feature in data.get('features', []):
        properties = feature.get('properties', {})
        
        alert = {
            "Event": properties.get("event"),
            "Affected Areas": properties.get("areaDesc"),
            "Severity": properties.get("severity"),
            "Certainty": properties.get("certainty"),
            "Urgency": properties.get("urgency"),
            "Start Time": properties.get("onset"),
            "End Time": properties.get("ends"),
            "Headline": properties.get("headline"),
            "Description": properties.get("description"),
            "Instructions": properties.get("instruction"),
            "Source": properties.get("senderName")
        }
        alerts.append(alert)
    
    return alerts
@tool
def get_weather_alerts(state:str) -> Dict:
    """
    Fetches active weather alerts for a given U.S. state using the National Weather Service (NWS) API.

    This function queries the NWS API for active weather alerts in the specified state and returns the
    details of any alerts that are currently in effect. The state is identified by its two-letter 
    abbreviation or its full name (e.g., 'FL', 'Florida', 'NY', 'New York').

    Parameters:
    state (str): The name or two-letter abbreviation of the state for which to fetch weather alerts. 
                 Example: 'FL' for Florida, 'CA' for California.

    Returns:
    dict: A list of active weather alerts for the state in the form of a dictionary. 
          Each alert contains details like the event type, description, and affected areas.
    
    Returns:
    str: If no active alerts are found, returns a message indicating that there are no alerts 
         for the specified state.
    
    Example:
    >>> get_weather_alerts('FL')
    """

    # TODO: Reduce the returned answers to < 15K tokens

    state = us.states.lookup(state)
    if state:
        url = f"https://api.weather.gov/alerts/active?area={state.abbr.upper()}"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check for HTTP errors
            
            alerts_data = response.json()

            # Check if there are any alerts
            if alerts_data.get("features"):
                alerts = extract_alerts(alerts_data)
                for alert in alerts:
                    print(f"Event: {alert['Event']}")
                    print(f"Affected Areas: {alert['Affected Areas']}")
                    print(f"Severity: {alert['Severity']}")
                    print(f"Certainty: {alert['Certainty']}")
                    print(f"Urgency: {alert['Urgency']}")
                    print(f"Start Time: {alert['Start Time']}")
                    print(f"End Time: {alert['End Time']}")
                    print(f"Headline: {alert['Headline']}")
                    print(f"Description: {alert['Description']}")
                    print(f"Instructions: {alert['Instructions']}")
                    print(f"Source: {alert['Source']}")
                    print("\n")
                return f"Above are the current {alerts} for {state.abbr.upper()}. "
            else:
                return f"No active alerts for {state.abbr.upper()}."

        except requests.exceptions.RequestException as e:
            return f"An error occurred: {e}"
    return "A state by this name doesn't exist in USA"

@tool
def get_nearest_shelter(address: str,
                    resCount: int = 5) -> str:
    
    """
    This function gets the 5 nearest shelters on the basis of the given address. 

    Parameters:
    ----------
    address : str
        Address of the location

    Returns:
    --------
    dict
        Details of the nearest shelter, including name, address, and available services, or an error message if no shelters are found.

    Example:
    --------
    >>> get_nearest_shelter('151 Hex Road, FL 70465')
    'Name: Central Shelter | 123 Main St, City, State'
    """

    # API Endpoint
    base_url = "https://services5.arcgis.com/Rvw11bGpzJNE7apK/ArcGIS/rest/services/Warming_Centers_Public_View/FeatureServer/7/queryTopFeatures"
    
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    geocode_result = gmaps.geocode(address)

    if geocode_result:

        latitude = geocode_result[0]['geometry']['location']['lat']
        longitude = geocode_result[0]['geometry']['location']['lng']

        geometry_user_arcgis = (gmaps_to_arcgis(latitude, longitude))

        params = {
            "where": "Status = 'Open'", 
            "topFilter":f"""
                {{
                    "groupByFields": "ShelterName",
                    "topCount": {resCount},
                    "orderByFields": "ShelterName"
                }}
            """,  
            "geometry": f"{geometry_user_arcgis[0]},{geometry_user_arcgis[1]}",  
            "geometryType": "esriGeometryPoint", 
            "spatialRel": "esriSpatialRelIntersects",  
            "distance": 50,  
            "units": "esriSRUnit_StatuteMile",  
            "outFields": "*",  
            "returnGeometry": "true",  
            "resultRecordCount": {resCount},  
            "f": "json"
        }

        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()

            if "features" in data:
                distance_dict = {}
                for feature in data["features"]:
                    attributes = feature['attributes']
                    geometry_feat_gmaps = arcgis_to_gmaps(feature['geometry']['x'], feature['geometry']['y'])
                    dist_dur = get_distance_google_maps(GOOGLE_MAPS_API_KEY, origin = f"{latitude},{longitude}", destination=f"{geometry_feat_gmaps[0]},{geometry_feat_gmaps[1]}")
                    if dist_dur:
                        distance_dict[attributes['OBJECTID']] = dist_dur

                distance_dict_sorted = dict(sorted(distance_dict.items(), key=lambda x: x[1][0]))

                # Create the result list based on dist_dict's order
                res = []
                for obj_id in distance_dict_sorted.keys():
                    matching_feat = next((feat['attributes'] for feat in list(data["features"]) if feat['attributes']['OBJECTID'] == obj_id), None)
                    if matching_feat:
                        address = " ".join([matching_feat[add] for add in ['Address', 'Address2', 'City', 'State', 'Zip'] if matching_feat[add]])
                        
                        fields = [
                            f"Name: {matching_feat['ShelterName']}",
                            f"{address}",
                            f"Distance: {distance_dict_sorted[obj_id][0]} miles - {distance_dict_sorted[obj_id][1]} min",
                            f"{matching_feat.get('Hours').replace('day','')}" if matching_feat.get('Hours') else None,
                            f"Contact: {matching_feat.get('Phone')}, {matching_feat.get('Website')}" 
                            if matching_feat.get('Phone') and matching_feat.get('Website') 
                            else f"Contact: {matching_feat.get('Phone')}" 
                            if matching_feat.get('Phone') 
                            else f"Website: {matching_feat.get('Website')}" 
                            if matching_feat.get('Website') 
                            else None,
                            f"POD Status: {matching_feat.get('POD_Status')}" if matching_feat.get('POD_Status') else None,
                            f"Animals: {matching_feat.get('AllowsAnimals')},{matching_feat.get('AnimalNotes')}" 
                            if matching_feat.get('AllowsAnimals') and matching_feat.get('AnimalNotes') 
                            else f"Animals: {matching_feat.get('AllowsAnimals')}" 
                            if matching_feat.get('AllowsAnimals') 
                            else f"Animals: {matching_feat.get('AnimalNotes')}" 
                            if matching_feat.get('AnimalNotes')
                            else None,
                            f"Additional Info: {matching_feat.get('Additional_Info')}" if matching_feat.get('Additional_Info') else None,
                        ]

                        output = " | ".join([field for field in fields if field])
                        res.append(output)
                if res:
                    return "\n".join(res)
    else:
        f"Failed to retrieve data: {response.status_code}"

    return "No open shelters found within 50 miles."

@tool
def get_power_outage_map(state:str):
    """
    Returns a link containing the power outage map for Florida
    It queries the argis api to get the outage map

    Parameters:
    -----------------
    state: str
          state for which we want to check power outage

    Return:
    -------------------
    link: str
          hyperlink containing the outage map

    Example:
    >>> power_outage('Florida')
    "https://www.arcgis.com/apps/dashboards/4833aec638214268b09683ce78ed2edf"
    """
    if state in ['Florida' , 'FL']:
        return "https://www.arcgis.com/apps/dashboards/4833aec638214268b09683ce78ed2edf"

# @tool
# def weather_forecast(city:str,units:str)->Dict:
#     pass

@tool
def query_rag_system(message: str , index:str) -> dict:
    """
    Query the retrieval augmented generation (RAG) system and answer the users question based on information stored in table (index).

    Parameters:
    message (str): Question asked by user. 
                
    index (str): The name of the index based on the user message and given details. 
                Example: 'HurricaneFirstAid' for first aid related message. 
                 
    Returns:
    - answer: A string containing the RAG response.
    """
    # Define the URL of your RAG Flask server
    url = "http://localhost:5015/ask"
    headers = {"Content-Type": "application/json"}


    query_data = {
        "q": message,
        "index": index,
        "prompt": "",
        "top_k": 5,
        "conversation_history": "",
    }

    try:
        response = requests.post(url, json=query_data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            answer = str(result.get("response"))
            return answer
        else:
            return str(f"Server returned status {response.status_code}: {response.text}")
    except requests.RequestException as e:
        return str(f"Request failed: {str(e)}")
    


@tool
def get_nearest_hospital(address:str):
    """
    This Function gets the 10 nearest hospitals for a given address. It expects a well formatted address with street name, city and state as well.
    """

    result = ""
    
    google_places = GooglePlaces(GOOGLE_MAPS_API_KEY)
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    geocode_result = gmaps.geocode(address)


    print(geocode_result)


    if geocode_result:

        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']

        query_result = google_places.nearby_search(
                # lat_lng ={'lat': 46.1667, 'lng': -1.15},
                lat_lng ={'lat': lat, 'lng': lng},
                radius = 5000,
                # types =[types.TYPE_HOSPITAL] or
                # [types.TYPE_CAFE] or [type.TYPE_BAR]
                # or [type.TYPE_CASINO])
                types =[types.TYPE_HOSPITAL])

        # If any attributions related
        # with search results print them
        if query_result.has_attributions: 
            print (query_result.html_attributions)

        
        # Iterate over the search results
        for place in query_result.places[:5]:
            
            print(place)
            # place.get_details()
            print (place.name)

            print (place.name)
            place_geocoded = gmaps.reverse_geocode((place.geo_location['lat'], place.geo_location['lng']))
            if place_geocoded:
                result += f'Place Name : {place.name}\nAddress : {place_geocoded[0]["formatted_address"]}\n' #Latitude : {place.geo_location["lat"]}\nLongitude : {place.geo_location["lng"]}
                print("Address",place_geocoded[0]["formatted_address"])
            else:
                result += f'Place Name : {place.name}\nAddress : Unavailable\nLatitude : {place.geo_location["lat"]}\nLongitude : {place.geo_location["lng"]}\n'
                print("Address Unvailable")
            print("Latitude", place.geo_location['lat'])
            print("Longitude", place.geo_location['lng'])
            print()

        return result

    else:
        result = "Incomplete Address! Please provide a Complete Address"
        print("Incomplete Address! Please provide a Complete Address")
        return result


@tool
def get_nearest_fire_station(address:str):
    """
    This Function gets the 10 nearest firestations for a given address. It expects a well formatted address with street name, city and state as well.
    """

    result = ""
    
    google_places = GooglePlaces(GOOGLE_MAPS_API_KEY)
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    geocode_result = gmaps.geocode(address)


    if geocode_result:

        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']

        query_result = google_places.nearby_search(
                # lat_lng ={'lat': 46.1667, 'lng': -1.15},
                lat_lng ={'lat': lat, 'lng': lng},
                radius = 5000,
                # types =[types.TYPE_HOSPITAL] or
                # [types.TYPE_CAFE] or [type.TYPE_BAR]
                # or [type.TYPE_CASINO])
                types =[types.TYPE_FIRE_STATION])

        # If any attributions related
        # with search results print them
        if query_result.has_attributions: 
            print (query_result.html_attributions)

        
        # Iterate over the search results
        for place in query_result.places[:5]:
            
            print(place)
            # place.get_details()
            print (place.name)

            print (place.name)
            place_geocoded = gmaps.reverse_geocode((place.geo_location['lat'], place.geo_location['lng']))
            if place_geocoded:
                result += f'Place Name : {place.name}\nAddress : {place_geocoded[0]["formatted_address"]}\n' #Latitude : {place.geo_location["lat"]}\nLongitude : {place.geo_location["lng"]}
                print("Address",place_geocoded[0]["formatted_address"])
            else:
                result += f'Place Name : {place.name}\nAddress : Unavailable\nLatitude : {place.geo_location["lat"]}\nLongitude : {place.geo_location["lng"]}\n'
                print("Address Unvailable")
            print("Latitude", place.geo_location['lat'])
            print("Longitude", place.geo_location['lng'])
            print()

        return result

    else:
        result = "Incomplete Address! Please provide a Complete Address"
        print("Incomplete Address! Please provide a Complete Address")
        return result
