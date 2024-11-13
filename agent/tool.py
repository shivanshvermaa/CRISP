import os
import shutil
import sqlite3

import pandas as pd
import requests
from langchain_core.tools import tool

import requests

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
    -------
    str
        A message indicating the evacuation zone(s) for the location, or an error message if the data could not be retrieved.
        
    Notes:
    -----
    - For Florida (FL), the function uses a point-based query (`esriGeometryPoint`) to check if the location
      lies within any evacuation zone.
    - For Texas (TX), the function approximates a point query by using a small bounding box (envelope) with 
      an intersect relationship (`esriGeometryEnvelope`) to determine if the location falls within any evacuation zone.
      
    Example:
    -------
    >>> is_in_evacuation_zone("FL", 27.994402, -81.760254)
    'Your location is in Evacuation Zone(s) A.'
    
    >>> is_in_evacuation_zone("TX", 30.267153, -97.743057)
    'The location is not within an evacuation zone.'
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
            
            return f"Your location is in Evacuation Zone(s) {zone}."
        else:
            return "The location is not within an evacuation zone."
    
    return f"Failed to retrieve data: {response.status_code}"



