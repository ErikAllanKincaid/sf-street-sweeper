# SF Street Sweeping Schedule - Research

## Data Source

**Dataset**: Street Sweeping Schedule
**Publisher**: City and County of San Francisco
**Portal**: DataSF (Socrata/OpenData)
**Dataset ID**: `yhqp-riqs`
**API Endpoint**: `https://data.sfgov.org/resource/yhqp-riqs.json`

## API Access

- **No API key required** for public read-only access
- **Rate limited**: Recommended to cache data (sweeping schedules change infrequently)
- **Format**: JSON, CSV, GeoJSON available

## Data Schema

| Field | Type | Description |
|-------|------|-------------|
| `cnn` | string | Street segment ID |
| `corridor` | string | Street name |
| `limits` | string | Block range (e.g., "Larkin St - Polk St") |
| `cnnrightleft` | string | L/R indicator for side of street |
| `blockside` | string | Side description (North, South, East, West, etc.) |
| `fullname` | string | Full schedule name (e.g., "Tue 1st, 3rd, 5th") |
| `weekday` | string | Day of week (Mon, Tues, Wed, Thu, Fri) |
| `fromhour` | string | Start hour (24hr format) |
| `tohour` | string | End hour |
| `week1` - `week5` | string | Which weeks sweeping occurs (1=yes, 0=no) |
| `holidays` | string | Holiday handling flag |
| `blocksweepid` | string | Unique sweep block ID |
| `line` | GeoJSON | Street segment geometry (LineString) |

## Query Examples

### Get all sweeping routes
```
https://data.sfgov.org/resource/yhqp-riqs.json
```

### Filter by street name
```
https://data.sfgov.org/resource/yhqp-riqs.json?corridor=Market%20St
```

### Filter by day of week
```
https://data.sfgov.org/resource/yhqp-riqs.json?weekday=Tues
```

### Spatial query - within bounding box (using SoQL)
```
https://data.sfgov.org/resource/yhqp-riqs.json?$where=within_box(line, 37.7, -122.5, 37.8, -122.3)
```

## SDKs Available

| Language | Library |
|----------|---------|
| Python | `sodapy` |
| JavaScript | `soda-js` |
| R | `RSocrata` |
| Ruby | `soda-ruby` |
| PHP | `soda-php` |
| Java | `soda-java` |

## Implementation Notes

### Data Strategy
1. **Cache the full dataset** - Street sweeping schedules rarely change
2. **Update weekly** - Check for changes on Monday mornings
3. **Local database recommended** - SQLite for offline capability

### Matching Algorithm
1. Get user's parked location (GPS or manual address input)
2. Geocode to coordinates
3. Find nearest street segment within ~50 meters
4. Parse schedule from `weekday`, `week1-5`, `fromhour`, `tohour`

### Schedule Parsing
- `week1-week5`: Binary flags for 1st-5th week of month
- `weekday`: Day of week
- `fromhour`/`tohour`: Start/end hour (local time)
- Example: `fullname: "Tue 1st, 3rd, 5th"` means Tuesday of weeks 1, 3, 5

### Push Notifications
- Check current week of month: `(day - 1) // 7 + 1`
- Send reminder 12-24 hours before sweeping time
- Consider: Push (Firebase), SMS (Twilio), or in-app alerts

## Reference URLs

- Dataset: https://data.sfgov.org/City-Infrastructure/Street-Sweeping-Schedule/yhqp-riqs
- API Docs: https://dev.socrata.com/foundry/data.sfgov.org/yhqp-riqs
- Python SDK: https://github.com/xmunoz/sodapy
