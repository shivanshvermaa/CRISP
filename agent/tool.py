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


