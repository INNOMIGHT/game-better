
from riot.client import RiotClient

PUUID = "Sj4KXs7EcIrXcU0T-JMaWvJ2z18G-93TC68dvh3I_qAg6rppAoJuqZ9RoeHuSkhHwuRFZa3ZG9XiAw"
REGION = "EUROPE"

with RiotClient() as riot:

    match_ids = riot.get_ranked_match_ids(
        puuid=PUUID,
        region=REGION,
        start=0,
        count=5,
        queue=420,
    )

    print("MATCH IDS:")
    print(match_ids)

    if match_ids:
        match = riot.get_match_by_id(
            match_id=match_ids[0],
            region=REGION,
        )

        timeline = riot.get_match_timeline(
            match_id=match_ids[0],
            region=REGION,
        )

        print("\nMATCH ID:")
        print(match["metadata"]["matchId"])

        print("\nGAME VERSION:")
        print(match["info"]["gameVersion"])

        print("\nQUEUE ID:")
        print(match["info"]["queueId"])

        print("\nPARTICIPANTS:")
        print(len(match["info"]["participants"]))

        print("\nTIMELINE FRAMES:")
        print(len(timeline["info"]["frames"]))

        print("\nFIRST FRAME TIMESTAMP:")
        print(timeline["info"]["frames"][0]["timestamp"])