import json
from pathlib import Path

OPTIMIZED_METADATA = {
    "1lR4aQLYG_k": {
        "folder": "output/AUTO_SHORTS_1790328835",
        "topic": "PSG Qatari Billions",
        "title": "How PSG Spent $1.5B To Hide This 💸 #shorts",
        "description": """Paris Saint-Germain spent billions in Qatari state funds, smashing world records with Neymar and Mbappe—yet secretly piled up massive annual losses and UEFA financial fair play investigations. How did they dodge severe sanctions, and is state-backed football sustainable?

💬 Did UEFA let PSG off easy, or was their spending legal? Drop your thoughts below! 👇

🔔 Subscribe to @SportStory for daily football finance & scandal stories.

#shorts #football #soccer #psg #sportsfinance #neymar #mbappe #uefa #ligue1""",
        "tags": [
            "psg", "paris saint germain", "neymar", "mbappe", "qsi", "al-khelaifi",
            "psg scandal", "sports finance", "financial fair play", "uefa ffp",
            "football debt", "football finance", "soccer stories", "sportstory",
            "ligue 1", "champions league", "football transfers", "shorts"
        ],
        "pinned_comment": "💬 Did UEFA protect PSG because of their billions, or did they follow the rules? Let's debate below! 👇"
    },
    "dN47nn3TLy4": {
        "folder": "output/AUTO_SHORTS_1790328898",
        "topic": "Portsmouth Bankruptcy & Prison",
        "title": "From Premier League To Prison! 🚨 #shorts",
        "description": """In 2008, Portsmouth FC lifted the FA Cup and played in Europe. Just two years later, hidden debts exploded past £135 million, triggering a 9-point deduction, relegation, and executive fraud prison sentences. The ultimate cautionary tale of reckless Premier League ownership.

💬 Is this the wildest financial collapse in Premier League history? Drop your thoughts below! 👇

🔔 Subscribe to @SportStory for daily football finance & scandal stories.

#shorts #football #soccer #portsmouth #premierleague #sportsfinance #facup #scandal""",
        "tags": [
            "portsmouth fc", "pompey", "premier league", "fa cup", "portsmouth bankruptcy",
            "football administration", "points deduction", "sports finance", "football debt",
            "reckless owners", "football scandal", "soccer documentary", "english football",
            "harry redknapp", "sportstory", "shorts"
        ],
        "pinned_comment": "💬 Portsmouth won the FA Cup in 2008 and went into liquidation by 2010. Worst ownership in Premier League history? 👇"
    },
    "vnpkNvHG7fs": {
        "folder": "output/AUTO_SHORTS_1790328952",
        "topic": "Parma Parmalat Fraud",
        "title": "The $14B Fraud That Killed Parma 🥛 #shorts",
        "description": """Parma Calcio ruled Italian football in the 1990s with superstars like Buffon, Cannavaro, and Crespo. But behind the trophies was Parmalat—a €14 billion corporate dairy fraud that imploded overnight, sending the club into bankruptcy and amateur football.

💬 Did 90s Parma have the greatest squad that never won Serie A? Drop your thoughts below! 👇

🔔 Subscribe to @SportStory for daily football finance & scandal stories.

#shorts #football #soccer #parma #seriea #sportsfinance #buffon #parmalat #scandal""",
        "tags": [
            "parma calcio", "parmalat", "parma fraud", "serie a", "buffon", "cannavaro",
            "crespo", "calisto tanzi", "italian football", "sports finance", "football bankruptcy",
            "football scandal", "calcio", "90s football", "sportstory", "shorts"
        ],
        "pinned_comment": "💬 Buffon, Cannavaro, Crespo, Veron... Was 1999 Parma the best squad in Italian football history? 👇"
    },
    "t9xyy7TB52Q": {
        "folder": "output/AUTO_SHORTS_1790329013",
        "topic": "Rangers FC Liquidation",
        "title": "How Scotland's Biggest Club Died 🏴󠁧󠁢󠁳󠁣󠁴󠁿 #shorts",
        "description": """Rangers FC won 54 Scottish league titles, but catastrophic tax avoidance schemes and £24 million in unpaid liabilities forced the unthinkable: total liquidation in 2012 and banishment to the fourth tier of Scottish football.

💬 Was Rangers' liquidation the biggest shock in British football history? Share your thoughts below! 👇

🔔 Subscribe to @SportStory for daily football finance & scandal stories.

#shorts #football #soccer #rangersfc", "scottishpremiership #sportsfinance #oldfirm #scandal""",
        "tags": [
            "rangers fc", "rangers liquidation", "scottish premiership", "old firm", "craig whyte",
            "ally mccoist", "ibrox", "scottish football", "football administration", "tax avoidance",
            "sports finance", "football debt", "sportstory", "shorts"
        ],
        "pinned_comment": "💬 From 54 league titles to the 4th tier. Did Scottish football punish Rangers fairly or too harshly? 👇"
    }
}

def update_local_files():
    for vid_id, data in OPTIMIZED_METADATA.items():
        meta_path = Path(data["folder"]) / "final_short_en_metadata.json"
        if meta_path.exists():
            payload = {
                "id": vid_id,
                "title": data["title"],
                "description": data["description"],
                "tags": data["tags"],
                "pinned_comment": data["pinned_comment"]
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"✅ Güncellendi: {meta_path} (ID: {vid_id})")

if __name__ == "__main__":
    update_local_files()
