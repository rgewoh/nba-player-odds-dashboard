import streamlit as st
import requests
import pandas as pd
from io import BytesIO

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

# Send request to fetch fixtures
resp = requests.post(graphql_url, json=fixture_query)

if resp.status_code != 200:
    st.error(f"❌ Failed to fetch fixtures. HTTP Status Code: {resp.status_code}")
    st.stop()

try:
    fixtures_data = resp.json()
    if 'data' not in fixtures_data or 'slugTournament' not in fixtures_data['data']:
        raise KeyError("Invalid response structure from Stake.com.")
    
    fixtures = fixtures_data['data']['slugTournament']['fixtures']
except Exception as e:
    st.error("❌ Failed to parse fixtures data from Stake.com.")
    st.code(str(e))
    st.stop()

# Create a dropdown for selecting a fixture (game)
fixture_options = {f["name"]: f["id"] for f in fixtures}
selected_fixture = st.selectbox("Select a Game", list(fixture_options.keys()))
event_id = fixture_options[selected_fixture]

# Step 2: Fetch markets for the selected event
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

if market_resp.status_code != 200:
    st.error(f"❌ Failed to fetch markets. HTTP Status Code: {market_resp.status_code}")
    st.stop()

try:
    market_data = market_resp.json()
    if 'data' not in market_data or 'event' not in market_data['data']:
        raise KeyError("Invalid response structure for market data.")
    
    markets = market_data['data']['event']['markets']
except Exception as e:
    st.error("❌ Failed to retrieve player odds for the selected fixture.")
    st.code(str(e))
    st.stop()

# Step 3: Filter only player props markets
player_markets = [m for m in markets if "Player" in m['name'] or "Points" in m['name']]

# Step 4: Prepare data for display and export
data = []
for market in player_markets:
    for outcome in market['outcomes']:
        data.append({
            "Market": market['name'],
            "Player": outcome['label'],
            "Odds": outcome['odds']
        })

if data:
    # Convert data to a DataFrame
    df = pd.DataFrame(data)
    
    # Display the data in Streamlit
    st.subheader(f"Player Props for: {selected_fixture}")
    st.dataframe(df)

    # Export the data to an Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Player Odds", index=False)
        writer.save()
    
    output.seek(0)

    # Add a download button for the Excel file
    st.download_button(
        label="📥 Download as Excel",
        data=output,
        file_name=f"{selected_fixture}_player_odds.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    # Show a warning if no player props are available
    st.warning("No player prop odds found for this game.")
