import json
import os
from pydantic import BaseModel
from typing import List


class Opportunity(BaseModel):
    profit: str
    sport: str
    event_time: str
    bookmaker1: str
    team1_bk1: str
    team2_bk1: str
    league_bk1: str
    bet_type_bk1: str
    odd_bk1: str
    link_bk1: str
    bookmaker2: str
    team1_bk2: str
    team2_bk2: str
    league_bk2: str
    bet_type_bk2: str
    odd_bk2: str
    link_bk2: str
    detailed_page: bool
    detailed_page_url: str
    matchup: str
    odd_specific: str = ""  # Default to empty string if not provided
    verified: bool = False  # Default to False if not provided


def load_opportunities(file_path: str) -> List[Opportunity]:
    """
    Load arbitrage opportunities from a JSON file.

    Parameters:
        file_path (str): Path to the JSON file.

    Returns:
        List[Opportunity]: A list of opportunities.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            return [Opportunity(**item) for item in data]
    except FileNotFoundError:
        print(f"Error: '{file_path}' file not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []


def filter_opportunities(opportunities: List[Opportunity]) -> List[Opportunity]:
    """
    Filter opportunities to include only DNB1 vs DNB2 bet types, ensure odd_specific is empty,
    and exclude opportunities with "Unknown" values in key fields.

    Parameters:
        opportunities (List[Opportunity]): List of opportunities.

    Returns:
        List[Opportunity]: Filtered opportunities.
    """
    filtered = []
    for opp in opportunities:
        # Normalize bet types to lowercase for comparison
        bet_type_bk1 = opp.bet_type_bk1.lower()
        bet_type_bk2 = opp.bet_type_bk2.lower()

        # Check for "Unknown" values in key fields
        unknown_fields = []
        if opp.team1_bk1.lower() == "unknown":
            unknown_fields.append("team1_bk1")
        if opp.team2_bk1.lower() == "unknown":
            unknown_fields.append("team2_bk1")
        if opp.team1_bk2.lower() == "unknown":
            unknown_fields.append("team1_bk2")
        if opp.team2_bk2.lower() == "unknown":
            unknown_fields.append("team2_bk2")
        if opp.link_bk1.lower() == "unknown":
            unknown_fields.append("link_bk1")
        if opp.link_bk2.lower() == "unknown":
            unknown_fields.append("link_bk2")

        # Debugging: Print the bet types, odd_specific, and unknown fields being checked
        print(f"Checking opportunity: bk1={bet_type_bk1}, bk2={bet_type_bk2}, odd_specific='{opp.odd_specific}', unknown_fields={unknown_fields}")

        # Check for DNB1 vs DNB2 combinations, odd_specific is empty, and no unknown fields
        if (
            ((bet_type_bk1 == "dnb1" and bet_type_bk2 == "dnb2") or 
             (bet_type_bk1 == "dnb2" and bet_type_bk2 == "dnb1")) and
            opp.odd_specific.strip() == "" and
            len(unknown_fields) == 0  # No unknown fields
        ):
            filtered.append(opp)
        elif unknown_fields:
            print(f"  -> Filtered out due to unknown fields: {unknown_fields}")

    return filtered


def save_filtered_opportunities(filtered_opportunities: List[Opportunity], output_file: str):
    """
    Save filtered opportunities to a JSON file.

    Parameters:
        filtered_opportunities (List[Opportunity]): List of filtered opportunities.
        output_file (str): Path to the output JSON file.
    """
    try:
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump([opp.dict() for opp in filtered_opportunities], json_file, ensure_ascii=False, indent=4)
        print(f"Filtered opportunities saved to {output_file}")
    except Exception as e:
        print(f"Error saving filtered opportunities: {e}")


def clear_filtered_opportunities_file(output_file: str):
    """
    Clear the filtered opportunities file by writing an empty array.
    
    Parameters:
        output_file (str): Path to the output JSON file.
    """
    try:
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump([], json_file, ensure_ascii=False, indent=4)
        print(f"✅ Cleared filtered opportunities file: {output_file}")
    except Exception as e:
        print(f"❌ Error clearing filtered opportunities file: {e}")


def main():
    # Load opportunities from arb_opportunities.json
    file_path = os.path.join(os.getcwd(), "arb_opportunities.json")
    opportunities = load_opportunities(file_path)

    # Define output file path
    output_file = os.path.join(os.getcwd(), "filtered_opportunities.json")

    if not opportunities:
        print("No opportunities found.")
        
        # Clear the filtered opportunities file when no source opportunities exist
        print("🧹 Clearing filtered_opportunities.json file (no source opportunities)...")
        clear_filtered_opportunities_file(output_file)
        
        return

    # Filter opportunities
    filtered_opportunities = filter_opportunities(opportunities)

    if not filtered_opportunities:
        print("No opportunities match the specified filters.")
        
        # Clear the filtered opportunities file when no opportunities pass the filter
        print("🧹 Clearing filtered_opportunities.json file (no matching opportunities)...")
        clear_filtered_opportunities_file(output_file)
        
        return

    # Print filtered opportunities
    for opp in filtered_opportunities:
        print("\n--------------------------------")
        print(f"Profit: {opp.profit}")
        print(f"Sport: {opp.sport}")
        print(f"Event Time: {opp.event_time}")
        print(f"Bookmaker 1: {opp.bookmaker1}")
        print(f"Team 1 (Bookmaker 1): {opp.team1_bk1}")
        print(f"Team 2 (Bookmaker 1): {opp.team2_bk1}")
        print(f"League (Bookmaker 1): {opp.league_bk1}")
        print(f"Bet Type (Bookmaker 1): {opp.bet_type_bk1}")
        print(f"Odd (Bookmaker 1): {opp.odd_bk1}")
        print(f"Link (Bookmaker 1): {opp.link_bk1}")
        print(f"Bookmaker 2: {opp.bookmaker2}")
        print(f"Team 1 (Bookmaker 2): {opp.team1_bk2}")
        print(f"Team 2 (Bookmaker 2): {opp.team2_bk2}")
        print(f"League (Bookmaker 2): {opp.league_bk2}")
        print(f"Bet Type (Bookmaker 2): {opp.bet_type_bk2}")
        print(f"Odd (Bookmaker 2): {opp.odd_bk2}")
        print(f"Link (Bookmaker 2): {opp.link_bk2}")
        print(f"Matchup: {opp.matchup}")
        print(f"Detailed Page URL: {opp.detailed_page_url}")

    # Save filtered opportunities to a JSON file
    save_filtered_opportunities(filtered_opportunities, output_file)


if __name__ == "__main__":
    main()