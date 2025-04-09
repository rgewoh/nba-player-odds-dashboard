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

resp = requests.post(graphql_url, json=fixture_query)

try:
    fixtures_data = resp.json()
    fixtures = fixtures_data['data']['slugTournament']['fixtures']
except (ValueError, KeyError):
    st.error("Failed to parse fixtures data from Stake.com. Please try again later.")
    st.stop()

fixture_options = {f["name"]: f["id"] for f in fixtures}
selected_fixture = st.selectbox("Select a Game", list(fixture_options.keys()))
event_id = fixture_options[selected_fixture]

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

try:
    markets = market_resp.json()['data']['event']['markets']
except (ValueError, KeyError):
    st.error("Failed to retrieve player odds for the selected fixture.")
    st.stop()

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
    st.subheader(f"Player Props for: {selected_fixture}")
    st.dataframe(df)

    # Export to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Player Odds", index=False)
    output.seek(0)

    st.download_button(
        label="📥 Download as Excel",
        data=output,
        file_name=f"{selected_fixture}_player_odds.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("No player prop odds found for this game.")
