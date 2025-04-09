import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="NBA Player Prop Odds", layout="wide")

st.title("🏀 NBA Player Prop Odds from Stake.com")

graphql_url = "https://stake.com/_api/graphql"

# Step 1: Get list of NBA events (games)
fixture_query = {
    "operationName": "TournamentFixtures",
    "variables": {
        "slug": "nba"
    },
    "query": """
    query TournamentFixtures($slug: String!) {
      slugTournament(slug: $slug) {
        fixtures {
          id
          name
          startTime
        }
      }
    }
    """
}

resp = requests.post(graphql_url, json=fixture_query)
fixtures = resp.json()['data']['slugTournament']['fixtures']

st.subheader("Upcoming NBA Games")
for f in fixtures:
    st.write(f"{f['name']} - ID: {f['id']}")

# Step 2: Use one event ID to get player odds (replace with any from above)
if fixtures:
    event_id = fixtures[0]['id']  # Example: use the first one

    market_query = {
        "operationName": "EventMarkets",
        "variables": {
            "eventId": event_id
        },
        "query": """
        query EventMarkets($eventId: ID!) {
          event(id: $eventId) {
            name
            markets {
              name
              outcomes {
                label
                odds
              }
            }
          }
        }
        """
    }

    market_resp = requests.post(graphql_url, json=market_query)
    markets = market_resp.json()['data']['event']['markets']

    # Filter only player props
    player_markets = [m for m in markets if "Player" in m['name'] or "Points" in m['name']]

    data = []
    for market in player_markets:
        for outcome in market['outcomes']:
            data.append({
                "Market": market['name'],
                "Player": outcome['label'],
                "Odds": outcome['odds']
            })

    if data:
        df = pd.DataFrame(data)
        st.subheader(f"Player Props for: {fixtures[0]['name']}")
        st.dataframe(df)
    else:
        st.warning("No player prop odds found for this game.")
else:
    st.error("No NBA fixtures available.")

