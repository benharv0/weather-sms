"""One-time script: resolve the city list to coordinates/timezones via Open-Meteo geocoding.

Run:  python3 build_cities.py   ->  writes cities.json
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request

# "City|ISO country code" (the code disambiguates names like Birmingham or Cordoba)
CITIES = """
Tokyo|JP Delhi|IN Shanghai|CN Dhaka|BD Sao Paulo|BR Cairo|EG Mexico City|MX Beijing|CN Mumbai|IN Osaka|JP
Chongqing|CN Karachi|PK Kinshasa|CD Lagos|NG Istanbul|TR Buenos Aires|AR Kolkata|IN Manila|PH Tianjin|CN Guangzhou|CN
Rio de Janeiro|BR Lahore|PK Bangalore|IN Shenzhen|CN Moscow|RU Chennai|IN Bogota|CO Paris|FR Jakarta|ID Lima|PE
Bangkok|TH Hyderabad|IN Seoul|KR Nagoya|JP London|GB Chengdu|CN Tehran|IR Ho Chi Minh City|VN Luanda|AO Wuhan|CN
Kuala Lumpur|MY Hangzhou|CN Hong Kong|HK Dongguan|CN Foshan|CN Nanjing|CN Ahmedabad|IN Santiago|CL Riyadh|SA Baghdad|IQ
Surat|IN Madrid|ES Suzhou|CN Pune|IN Harbin|CN Houston|US Dallas|US Toronto|CA Dar es Salaam|TZ Miami|US Belo Horizonte|BR
Singapore|SG Philadelphia|US Atlanta|US Fukuoka|JP Khartoum|SD Barcelona|ES Johannesburg|ZA Saint Petersburg|RU Qingdao|CN
Dalian|CN Washington|US Yangon|MM Alexandria|EG Jinan|CN Guadalajara|MX Sydney|AU Melbourne|AU Abidjan|CI Casablanca|MA
Nairobi|KE Addis Ababa|ET Accra|GH Cape Town|ZA Durban|ZA Algiers|DZ Tunis|TN Dubai|AE Abu Dhabi|AE Doha|QA
Kuwait City|KW Amman|JO Beirut|LB Jerusalem|IL Tel Aviv|IL Ankara|TR Izmir|TR Tbilisi|GE Yerevan|AM Baku|AZ
Tashkent|UZ Almaty|KZ Kabul|AF Kathmandu|NP Colombo|LK Chittagong|BD Hanoi|VN Phnom Penh|KH Vientiane|LA Taipei|TW
Busan|KR Pyongyang|KP Ulaanbaatar|MN Novosibirsk|RU Vladivostok|RU Yekaterinburg|RU Kyiv|UA Warsaw|PL Berlin|DE
Hamburg|DE Munich|DE Vienna|AT Prague|CZ Budapest|HU Bucharest|RO Sofia|BG Belgrade|RS Athens|GR Rome|IT Milan|IT
Naples|IT Lisbon|PT Dublin|IE Amsterdam|NL Brussels|BE Copenhagen|DK Stockholm|SE Oslo|NO Helsinki|FI Reykjavik|IS
Zurich|CH Edinburgh|GB Manchester|GB Los Angeles|US New York|US Chicago|US San Francisco|US Seattle|US Denver|US
Phoenix|US Boston|US Detroit|US Minneapolis|US New Orleans|US Las Vegas|US Honolulu|US Anchorage|US Montreal|CA
Vancouver|CA Calgary|CA Ottawa|CA Havana|CU Kingston|JM Panama City|PA San Jose|CR Guatemala City|GT San Salvador|SV
Caracas|VE Quito|EC La Paz|BO Montevideo|UY Asuncion|PY Brasilia|BR Salvador|BR Fortaleza|BR Recife|BR Medellin|CO
Cordoba|AR Monterrey|MX Auckland|NZ Wellington|NZ Perth|AU Brisbane|AU Dakar|SN Kampala|UG Harare|ZW Lusaka|ZM
Maputo|MZ Antananarivo|MG Windhoek|NA Tripoli|LY
Kano|NG Ibadan|NG Zhengzhou|CN Shenyang|CN Jaipur|IN Lucknow|IN Faisalabad|PK Surabaya|ID Medan|ID
"""
PAIRS = [(n.strip(), cc) for n, cc in re.findall(r"([^|]+)\|([A-Z]{2})", CITIES)]

# Extra candidates, used in order until TARGET cities have resolved
EXTRA = """
Xian|CN Changsha|CN Kunming|CN Nanchang|CN Fuzhou|CN Xiamen|CN Hefei|CN Taiyuan|CN Shijiazhuang|CN Urumqi|CN Lanzhou|CN
Nanning|CN Guiyang|CN Changchun|CN Wuxi|CN Ningbo|CN Wenzhou|CN Tangshan|CN Hohhot|CN Haikou|CN Lhasa|CN Yinchuan|CN
Xining|CN Luoyang|CN Yantai|CN Xuzhou|CN Zhuhai|CN Macau|MO Kanpur|IN Nagpur|IN Indore|IN Bhopal|IN Visakhapatnam|IN
Patna|IN Vadodara|IN Ghaziabad|IN Ludhiana|IN Agra|IN Nashik|IN Ranchi|IN Meerut|IN Rajkot|IN Varanasi|IN Srinagar|IN
Amritsar|IN Coimbatore|IN Kochi|IN Thiruvananthapuram|IN Guwahati|IN Chandigarh|IN Bhubaneswar|IN Madurai|IN Jodhpur|IN
Raipur|IN Mysore|IN Panaji|IN Islamabad|PK Peshawar|PK Multan|PK Hyderabad|PK Quetta|PK Gujranwala|PK Rawalpindi|PK
Khulna|BD Rajshahi|BD Sylhet|BD Bandung|ID Semarang|ID Makassar|ID Palembang|ID Denpasar|ID Yogyakarta|ID Balikpapan|ID
Cebu|PH Davao|PH Quezon City|PH Da Nang|VN Haiphong|VN Can Tho|VN Chiang Mai|TH Phuket|TH Johor Bahru|MY
Kota Kinabalu|MY Kuching|MY Sapporo|JP Kyoto|JP Kobe|JP Yokohama|JP Hiroshima|JP Sendai|JP Kawasaki|JP Naha|JP
Kumamoto|JP Niigata|JP Incheon|KR Daegu|KR Daejeon|KR Gwangju|KR Ulsan|KR Kaohsiung|TW Taichung|TW Bishkek|KG
Dushanbe|TJ Ashgabat|TM Samarkand|UZ Astana|KZ Shymkent|KZ Mecca|SA Medina|SA Jeddah|SA Dammam|SA Muscat|OM Manama|BH
Sharjah|AE Basra|IQ Mosul|IQ Erbil|IQ Damascus|SY Aleppo|SY Sanaa|YE Aden|YE Mashhad|IR Isfahan|IR Shiraz|IR Tabriz|IR
Haifa|IL Nicosia|CY Port Harcourt|NG Abuja|NG Benin City|NG Kaduna|NG Kumasi|GH Douala|CM Yaounde|CM Brazzaville|CG
Lubumbashi|CD Mombasa|KE Kigali|RW Bujumbura|BI Mogadishu|SO Djibouti|DJ Asmara|ER Juba|SS Ndjamena|TD Niamey|NE
Bamako|ML Ouagadougou|BF Conakry|GN Freetown|SL Monrovia|LR Lome|TG Cotonou|BJ Nouakchott|MR Banjul|GM Libreville|GA
Malabo|GQ Lilongwe|MW Gaborone|BW Mbabane|SZ Maseru|LS Pretoria|ZA Bloemfontein|ZA Rabat|MA Marrakesh|MA Fez|MA Oran|DZ
Constantine|DZ Sfax|TN Benghazi|LY Luxor|EG Aswan|EG Port Said|EG Mwanza|TZ Arusha|TZ Dodoma|TZ Huambo|AO Beira|MZ
Bulawayo|ZW Ndola|ZM Port Louis|MU Victoria|SC Rotterdam|NL The Hague|NL Antwerp|BE Lyon|FR Marseille|FR Toulouse|FR
Nice|FR Bordeaux|FR Strasbourg|FR Lille|FR Nantes|FR Cologne|DE Frankfurt|DE Stuttgart|DE Dusseldorf|DE Leipzig|DE
Dresden|DE Bremen|DE Nuremberg|DE Hanover|DE Valencia|ES Seville|ES Zaragoza|ES Malaga|ES Bilbao|ES Palma|ES Porto|PT
Turin|IT Palermo|IT Genoa|IT Bologna|IT Florence|IT Venice|IT Bari|IT Catania|IT Glasgow|GB Birmingham|GB Leeds|GB
Liverpool|GB Bristol|GB Sheffield|GB Belfast|GB Cardiff|GB Cork|IE Gothenburg|SE Malmo|SE Bergen|NO Tampere|FI Aarhus|DK
Krakow|PL Lodz|PL Wroclaw|PL Gdansk|PL Poznan|PL Brno|CZ Bratislava|SK Ljubljana|SI Zagreb|HR Split|HR Sarajevo|BA
Skopje|MK Tirana|AL Podgorica|ME Thessaloniki|GR Cluj-Napoca|RO Timisoara|RO Iasi|RO Plovdiv|BG Varna|BG Chisinau|MD
Minsk|BY Vilnius|LT Riga|LV Tallinn|EE Odessa|UA Kharkiv|UA Lviv|UA Dnipro|UA Kazan|RU Nizhny Novgorod|RU Samara|RU
Rostov-on-Don|RU Ufa|RU Krasnoyarsk|RU Omsk|RU Chelyabinsk|RU Perm|RU Volgograd|RU Irkutsk|RU Khabarovsk|RU Murmansk|RU
Sochi|RU Bursa|TR Antalya|TR Adana|TR Konya|TR Gaziantep|TR Valletta|MT Luxembourg|LU San Diego|US San Antonio|US
Austin|US Jacksonville|US Columbus|US Charlotte|US Indianapolis|US Fort Worth|US Nashville|US Memphis|US Louisville|US
Baltimore|US Milwaukee|US Albuquerque|US Tucson|US Fresno|US Sacramento|US Kansas City|US Omaha|US Cleveland|US
Pittsburgh|US Cincinnati|US Tampa|US Orlando|US St. Louis|US Salt Lake City|US Portland|US Raleigh|US Richmond|US
Buffalo|US Oklahoma City|US Boise|US Birmingham|US Charleston|US Savannah|US El Paso|US Des Moines|US Little Rock|US
Jackson|US Providence|US Hartford|US Wichita|US Fargo|US Billings|US Cheyenne|US Spokane|US Edmonton|CA Winnipeg|CA
Quebec City|CA Halifax|CA Saskatoon|CA Regina|CA Victoria|CA St. John's|CA Hamilton|CA Whitehorse|CA Yellowknife|CA
Iqaluit|CA Puebla|MX Tijuana|MX Leon|MX Merida|MX Cancun|MX Chihuahua|MX Culiacan|MX Veracruz|MX Oaxaca|MX Queretaro|MX
Acapulco|MX Santo Domingo|DO Port-au-Prince|HT San Juan|PR Nassau|BS Bridgetown|BB Port of Spain|TT Tegucigalpa|HN
Managua|NI Belize City|BZ Santiago de Cuba|CU Rosario|AR Mendoza|AR Salta|AR Ushuaia|AR Valparaiso|CL Concepcion|CL
Punta Arenas|CL Antofagasta|CL Cali|CO Barranquilla|CO Cartagena|CO Maracaibo|VE Valencia|VE Guayaquil|EC Cuenca|EC
Arequipa|PE Cusco|PE Trujillo|PE Santa Cruz|BO Cochabamba|BO Curitiba|BR Porto Alegre|BR Manaus|BR Belem|BR Goiania|BR
Campinas|BR Natal|BR Florianopolis|BR Cuiaba|BR Georgetown|GY Paramaribo|SR Cayenne|GF Adelaide|AU Canberra|AU Hobart|AU
Darwin|AU Cairns|AU Gold Coast|AU Newcastle|AU Christchurch|NZ Dunedin|NZ Suva|FJ Port Moresby|PG Noumea|NC Papeete|PF
Apia|WS Port Vila|VU Honiara|SB Thimphu|BT Male|MV Bandar Seri Begawan|BN Dili|TL Naypyidaw|MM Mandalay|MM Kandy|LK
Pokhara|NP Yakutsk|RU Magadan|RU Norilsk|RU Tromso|NO Nuuk|GL Torshavn|FO Akureyri|IS Hamilton|BM
"""
EXTRA_PAIRS = [(n.strip(), cc) for n, cc in re.findall(r"([^|]+)\|([A-Z]{2})", EXTRA)]
TARGET = 500


def geocode(name: str, cc: str) -> dict | None:
    q = urllib.parse.urlencode({"name": name, "count": 10, "country_code": cc, "language": "en"})
    url = f"https://geocoding-api.open-meteo.com/v1/search?{q}"
    with urllib.request.urlopen(url, timeout=20) as r:
        results = json.load(r).get("results") or []
    if not results:
        return None
    best = max(results, key=lambda x: x.get("population") or 0)
    return {
        "name": name,
        "country": best.get("country", cc),
        "lat": best["latitude"],
        "lon": best["longitude"],
        "timezone": best["timezone"],
    }


if __name__ == "__main__":
    out, missing, seen = [], [], set()
    for name, cc in PAIRS + EXTRA_PAIRS:
        if len(out) >= TARGET:
            break
        if (name, cc) in seen:
            continue
        seen.add((name, cc))
        try:
            city = geocode(name, cc)
        except Exception as e:  # network hiccup: report and continue
            print(f"error {name}: {e}")
            city = None
        if city:
            out.append(city)
        else:
            missing.append(f"{name}|{cc}")
        time.sleep(0.15)
    with open("cities.json", "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"resolved {len(out)}; skipped: {missing}")
