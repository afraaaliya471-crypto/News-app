"""
sources.py

Holds every "where to look" and "what counts" decision for the pipeline,
as plain data. Nothing in this file fetches anything — pipeline.py does
that, by looping over what's defined here.

To tune the pipeline later (add a publisher, add a keyword you notice
we're missing), edit the lists/dicts below. No other file needs to change.
"""

# 1. Publishers we search with Google News site:
TRUSTED_PUBLISHERS = [
    # Major Construction Industry Publications
    "zawya.com",
    "constructionweekonline.com",
    "meed.com",
    "constructionweek.com",  # Additional construction focus
    "middleeastconstructionnews.com",
    
    # Business & Trade Publications
    "tradearabia.com",
    "arabianbusiness.com",
    "gulfbusiness.com",
    "constructionweekonline.in",  # Middle East edition
    "mei.meed.com",  # MEED Middle East Insight
    
    # UAE Daily News - Top News Channels
    "khaleejtimes.com",  # Khaleej Times - major English daily
    "gulfnews.com",  # Gulf News - #1 English daily in UAE
    "thenationalnews.com",  # The National - major English daily
    "wam.ae",  # WAM - Emirates News Agency (official)
    "emirates247.com",  # Emirates 24/7
    "albayan.ae",  # Al Bayan - major Arabic newspaper
    "alittihad.ae",  # Al Ittihad - major UAE Arabic newspaper
    "24.ae",  # 24 News - Dubai Media Incorporated
    "emaratalyoum.com",  # Emarat Al Youm - major UAE Arabic daily
    
    # Saudi Arabia Daily News - Top News Channels
    "arabnews.com",  # Arab News - #1 English daily in Saudi
    "saudigazette.com.sa",  # Saudi Gazette - major English daily
    "spa.gov.sa",  # SPA - Saudi Press Agency (official)
    "argaam.com",  # Argaam - Saudi business & financial news
    "okaz.com.sa",  # Okaz - major Saudi Arabic newspaper
    "aleqt.com",  # Al Eqtisadiah - Saudi economic newspaper
    "alriyadh.com",  # Al Riyadh - major Saudi Arabic newspaper
    "al-jazirah.com",  # Al Jazirah - major Saudi Arabic newspaper
    "sabq.org",  # Sabq - popular Saudi news website
    "ajel.sa",  # Ajel - Saudi news portal
    
    # Regional Coverage
    "albawaba.com",  # Regional Middle East news
    "alarabiya.net",  # Al Arabiya - major pan-Arab news network
    "gulf-times.com",  # Qatar but covers region
    "constructionplusasia.com",  # Asia/Middle East coverage
    
    # Real Estate Focused
    "propertyfinder.ae",
    "bayut.com",
    "dubaiproperties.ae",
    
    # Engineering & Technical
    "engineeringnews-record.com",  # ENR - covers major projects globally
    "globalconstructionreview.com",
]

# 2. Second gate: the story also has to actually be about construction,
#    not sports/defense/finance "winning a contract".
CONSTRUCTION_KEYWORDS = [
    # Core construction
    "construction", "building", "infrastructure", "development",
    "EPC", "contractor", "builder", "developer",
    
    # Residential
    "tower", "towers", "building", "residential", "housing", "homes",
    "villas", "apartments", "units", "real estate",
    
    # Commercial
    "mall", "shopping", "retail", "hotel", "resort", "office",
    "commercial", "mixed-use", "headquarters",
    
    # Infrastructure
    "road", "highway", "bridge", "tunnel", "metro", "railway",
    "airport", "terminal", "port", "harbour", "harbor",
    
    # Utilities
    "water", "sewage", "treatment", "desalination", "pipeline",
    "power plant", "solar", "wind", "energy", "electricity",
    "substation", "transmission",
    
    # Public facilities
    "hospital", "medical", "school", "university", "stadium",
    "sports", "museum", "park", "recreation",
    
    # Industrial
    "factory", "plant", "facility", "industrial", "warehouse",
    "logistics", "manufacturing",
    
    # Project types
    "project", "scheme", "development", "masterplan",
    "phase", "expansion", "renovation", "upgrade",
]

# 3. Country tagging - which cities/spellings imply UAE vs Saudi Arabia.
#    Includes well-known districts/landmarks, not just city/country names,
#    since headlines often name a place ("Palm Jumeirah") instead of
#    saying "Dubai" or "UAE" outright. This list will never be complete -
#    add to it whenever you spot a real headline it missed.
COUNTRY_KEYWORDS = {
    "UAE": [
        # Emirates
        "UAE", "U.A.E", "Emirates", "Dubai", "Abu Dhabi", "Sharjah", "Ajman",
        "Ras Al Khaimah", "Fujairah", "Umm Al Quwain",
        
        # Major Areas/Projects
        "Palm Jumeirah", "Business Bay", "Downtown Dubai", "DIFC", "Al Maktoum",
        "Dubai Marina", "JLT", "Jumeirah Lake Towers", "Dubai Hills", "Dubai South",
        "Dubai Islands", "Deira", "Bur Dubai", "Al Barsha", "Dubai Creek",
        "Yas Island", "Saadiyat", "Al Reem", "Reem Island", "Khalifa City",
        "Masdar City", "Al Ain", "Dubai Silicon Oasis",
        
        # Major UAE Companies/Developers
        "Nakheel", "Emaar", "Aldar", "Damac", "Azizi", "Deyaar",
        "Dubai Properties", "Meraas", "Majid Al Futtaim", "Dubai Holding",
        "Mubadala", "ADQ", "ADNOC", "Abu Dhabi National Oil", "Etihad Rail",
        "RTA", "Roads and Transport Authority", "Dubai Municipality",
        "DEWA", "Dubai Electricity", "Sharjah", "RAK Properties",
        
        # Currencies/Terms
        "AED", "Dirham", "Dh", "DH",
    ],
    "Saudi Arabia": [
        # Country Names
        "Saudi", "KSA", "K.S.A", "Saudi Arabia", "Kingdom of Saudi",
        
        # Major Cities
        "Riyadh", "Jeddah", "Mecca", "Medina", "Dammam", "Khobar", 
        "Jubail", "Yanbu", "Tabuk", "Buraidah", "Hail", "Abha",
        
        # Mega Projects
        "NEOM", "The Line", "Qiddiya", "Red Sea", "Diriyah Gate",
        "Roshn", "King Abdullah", "King Salman", "Prince Mohammed",
        "Trojena", "Oxagon", "Sindalah",
        
        # Major Saudi Companies/Developers
        "Saudi Aramco", "Aramco", "PIF", "Public Investment Fund",
        "Saudi Binladin", "Saudi Oger", "Al Rajhi", "Savola", 
        "SABIC", "Ma'aden", "SEC", "Saudi Electricity",
        "Roshn Group", "Dar Al Arkan", "Jabal Omar",
        
        # Currencies/Terms
        "SAR", "Riyal", "SR",
    ],
}