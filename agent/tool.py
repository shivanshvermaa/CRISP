import os
import shutil
import sqlite3

import pandas as pd
import requests

from langchain_core.tools import tool
import us
from typing import List,Dict,LiteralString

@tool
def get_disaster_declaration(state: str,
                             declarationType: str,
                             limit: int = 3) -> list:
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
       >>> get_disaster_declaration(state="TX", declarationType="DR", limit=2)
       ["Disaster ID: 5530...", "Disaster ID: 5531..."]

       Notes:
       ------
       - Uses pagination; `limit` restricts records per call.
       - Requires `requests` library.
       """
    base_url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"


    params = {
        "state": state,      # Filter by state (e.g., Texas)
        "declarationType": declarationType,   # Declaration type (e.g., DR for major disaster)
        "limit": limit        # Limit the number of results
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()  # Convert response to JSON
        disaster_summaries = data.get("DisasterDeclarationsSummaries", [])
        disaster_summaries = disaster_summaries[:limit]
        formatted_disasters = []
        for disaster in disaster_summaries:
            formatted_disasters.append(
                f"Declaration String: {disaster['femaDeclarationString']}\n"
                f"State: {disaster['state']}\n"
                f"Declaration Type: {disaster['declarationType']}\n"
                f"Title: {disaster['declarationTitle']}\n"
                f"Incident Type: {disaster['incidentType']}\n"
                f"Declaration Date: {disaster['declarationDate']}\n"
                f"Incident Begin Date: {disaster['incidentBeginDate']}\n"
                f"Incident End Date: {disaster['incidentEndDate']}\n"
                f"Designated Area: {disaster['designatedArea']}\n"
                # f"Programs Declared: "
                # f"IH: {disaster['ihProgramDeclared']}, "
                # f"IA: {disaster['iaProgramDeclared']}, "
                # f"PA: {disaster['paProgramDeclared']}, "
                # f"HM: {disaster['hmProgramDeclared']}\n"
                f"Region: {disaster['region']}\n"
                f"Last Refresh: {disaster['lastRefresh']}"
            )
        return formatted_disasters
    else:
        return [f"Failed to retrieve data: {response.status_code}"]


@tool
def is_in_evacuation_zone(state: str,
                          latitude: float,
                          longitude: float) -> str:
    
    """
    Determines if a given location is within an evacuation zone by querying the relevant state-specific API.

    Parameters:
    ----------
    state : str
        The state code for which to check the evacuation zone (e.g., "FL" for Florida, "TX" for Texas).
    latitude : float
        The latitude of the location to check.
    longitude : float
        The longitude of the location to check.

    Returns:
    str
        A message indicating the evacuation zone(s) for the location, or an error message if the data could not be retrieved.

    Notes:

    - For Florida (FL)  function uses a point-based query (`esriGeometryPoint`) to check if the location
      lies within any evacuation zone.
    - For Texas (TX)  function approximates a point query by using a small bounding box (envelope) with
      an intersect relationship (`esriGeometryEnvelope`) to determine if the location falls within any evacuation zone.

    Example:
    -------
    >>> is_in_evacuation_zone("FL", 27.994402, -81.760254)
    'Your location is in Evacuation Zone(s) A.'
    """

    # TODO: Reduce the returned answers to < 15K tokens and DocuString < 1024 characters.


    print(f"state:{state}||latitude:{latitude}||longitude:{longitude}")


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
    
    if state == "FL":
        base_url = "https://services.arcgis.com/3wFbqsFPLeKqOlIK/arcgis/rest/services/KYZ_ZL_Vector_Enriched_Calculated_20230608/FeatureServer/28/query"
        params["geometry"] = f"{latitude},{longitude}"
        params["geometryType"] = "esriGeometryPoint"
        params["spatialRel"] = "esriSpatialRelWithin"
        
        
    elif state == "TX":
        base_url = "https://services.arcgis.com/su8ic9KbA7PYVxPS/arcgis/rest/services/HurricaneEvac_Zones/FeatureServer/0/query"

        offset = 10000  

        xmin = latitude - offset
        ymin = longitude - offset
        xmax = latitude + offset
        ymax = longitude + offset

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

            print(f"Your location is in Evacuation Zone(s) {zone}.")
            return f"Your location is in Evacuation Zone(s) {zone}."
        else:
            print("The location is not within an evacuation zone.")
            return "The location is not within an evacuation zone."

    print(f"Failed to retrieve data: {response.status_code}")
    
    return f"Failed to retrieve data: {response.status_code}"


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
                ## TODO extract only important keys Very Imp
                print(alerts_data["features"][0])
                return alerts_data["features"][:10]
            else:
                return f"No active alerts for {state.abbr.upper()}."

        except requests.exceptions.RequestException as e:
            return f"An error occurred: {e}"
    return "A state by this name doesn't exist in USA"

# @tool
# def weather_forecast(city:str,units:str)->Dict:
#     pass
