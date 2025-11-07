#!/usr/bin/env python3
import requests, base64, json
from pathlib import Path

IDF_API = "https://web-production-3092c.up.railway.app"
EPLUS_API = "https://web-production-1d1be.up.railway.app"

address = "147 Sutter St, San Francisco, CA 94104"
building_params = {"building_type": "Office", "stories": 3, "floor_area": 10000}

def find_epws_preferred():
    # Return a preference-ordered list of EPWs to try
    candidates = []
    globs = [
        "/Applications/EnergyPlus-*/WeatherData/*.epw",
        "/Applications/EnergyPlus-*/EnergyPlus installation files/WeatherData/*.epw",
        "/usr/local/EnergyPlus-*/WeatherData/*.epw",
    ]
    files = []
    for g in globs:
        files.extend(Path("/").glob(g[1:]))
    # Prefer SF then Chicago, then any others
    preferred = []
    for p in files:
        if "San.Francisco" in p.name or "724940" in p.name:
            preferred.append(p)
    for p in files:
        if ("Chicago" in p.name or "725300" in p.name) and p not in preferred:
            preferred.append(p)
    for p in files:
        if p not in preferred:
            preferred.append(p)
    return preferred

def main():
    print("Step 1: Generate IDF")
    gen_resp = requests.post(
        f"{IDF_API}/api/generate",
        json={"address": address, **building_params},
        timeout=120,
    )
    print("  status:", gen_resp.status_code)
    gen_resp.raise_for_status()
    gen = gen_resp.json()
    if not gen.get("success"):
        print("Generation failed:", json.dumps(gen, indent=2))
        return 1
    download_url = gen.get("download_url")
    if download_url and download_url.startswith("/"):
        download_url = f"{IDF_API}{download_url}"
    filename = gen.get("filename", "building.idf")
    print("  IDF:", filename)

    print("Step 2: Download IDF")
    idf_resp = requests.get(download_url, timeout=60)
    idf_resp.raise_for_status()
    idf_txt = idf_resp.text
    print("  IDF size (chars):", len(idf_txt))

    epws = find_epws_preferred()
    if not epws:
        print("No EPWs found in system EnergyPlus WeatherData paths")
        return 2

    # Try EPWs sequentially until success or all tried
    for idx, epw in enumerate(epws, 1):
        print(f"Step 3: Try Weather file [{idx}/{len(epws)}] -> {epw}")
        try:
            with open(epw, "rb") as f:
                epw_b64 = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print("  Skipping EPW due to read error:", e)
            continue

        print("Step 4: Simulate")
        # Exact request shape required by the service: raw text JSON (no base64, no multipart)
        try:
            try:
                weather_text = Path(epw).read_text(encoding='utf-8')
            except Exception:
                weather_text = Path(epw).read_text(encoding='latin-1', errors='ignore')
            payload = {
                "idf_content": idf_txt,
                "weather_content": weather_text,
            }
            sim_resp = requests.post(
                f"{EPLUS_API}/simulate",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=600,
            )
            print("  simulate status:", sim_resp.status_code)
            data = sim_resp.json()
        except Exception as e:
            print("  simulate error:", e)
            data = {}

        print("\n=== Simulation Result (summary) ===")
        print("simulation_status:", data.get("simulation_status"))
        print("energyplus_version:", data.get("energyplus_version"))
        if data.get("energy_results"):
            print("energy_results keys:", list(data["energy_results"].keys())[:8])
        warnings = data.get("warnings", [])
        print("warnings count:", len(warnings))
        if warnings:
            print("\n=== Detailed Warnings (first 20) ===")
            for i, w in enumerate(warnings[:20], 1):
                print(f"{i}. {w[:200]}")
        if data.get("error_message"):
            print("\nerror_message:", data["error_message"][:500])

        if data.get("simulation_status") == "success" or data.get("energy_results"):
            return 0
        print("  Simulation failed, trying next EPW...")

    print("All EPWs tried; no successful simulation.")
    return 3

if __name__ == "__main__":
    raise SystemExit(main())
