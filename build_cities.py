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
    out, missing = [], []
    for name, cc in PAIRS:
        try:
            city = geocode(name, cc)
        except Exception as e:  # network hiccup: report and continue
            print(f"error {name}: {e}")
            city = None
        (out if city else missing).append(city or f"{name}|{cc}")
        time.sleep(0.15)
    with open("cities.json", "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"resolved {len(out)} of {len(PAIRS)}; missing: {missing}")
