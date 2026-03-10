import json

with open("/home/erik/code/opencode/sf-street-sweeper/sf_sweep_data.json") as f:
    data = json.load(f)

print(f"Total records: {len(data)}")

# Search for streets in Noe Valley area
noe_streets = [
    r["corridor"].lower()
    for r in data
    if any(
        x in r["corridor"].lower()
        for x in [
            "16th",
            "17th",
            "18th",
            "19th",
            "20th",
            "22nd",
            "noe",
            "glen",
            "palmer",
        ]
    )
]
print(f"\nStreets in Noe Valley area (first 20):")
for s in noe_streets[:20]:
    print(s)

# Check for clipper
has_clipper = any("clipper" in r["corridor"].lower() for r in data)
print(f"\nClipper Street in dataset: {has_clipper}")

if not has_clipper:
    print("\nClipper Street not found - checking nearby streets")
    all_streets = [r["corridor"][:50] for r in data[:50]]
    print("\nFirst 50 corridor values in dataset:")
    for s in all_streets:
        print(s)
