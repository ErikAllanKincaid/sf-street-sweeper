# SF Street Sweeping Schedule - Research

## Data Source

### Primary Source (Snapshot)

**Dataset**: Archived Street Sweeping data as of Jan 27, 2025
**Publisher**: City and County of San Francisco
**Portal**: DataSF (Socrata/OpenData)
**Dataset ID**: `xsry-uuyt`
**API Endpoint**: `https://data.sfgov.org/resource/xsry-uuyt.json`
**CSV Download**: `https://data.sfgov.org/api/views/xsry-uuyt/rows.csv?accessType=DOWNLOAD`
**Total Rows**: 37,878

**Important**: This is a **frozen snapshot** of the street sweeping schedule as of January 27, 2025. The City of SF states "accuracy not guaranteed" for this snapshot, but it represents the actual historical data.

### Current Live Data (Unreliable)

**Dataset**: Street Sweeping Schedule (Undergoing Maintenance)
**Dataset ID**: `yhqp-riqs`
**Status**: ⚠️ **BROKEN/EMPTY** - only 220 rows, data currently broken

**Do NOT use** the live `yhqp-riqs` dataset - it is undergoing maintenance and essentially empty. The archived snapshot (`xsry-uuyt`) is the only reliable data source.

## API Access

- **No API key required** for public read-only access
- **Rate limited**: Recommended to cache data (sweeping schedules change infrequently, snapshot is frozen)
- **Format**: JSON, CSV, GeoJSON available

## Data Schema

Fields: CNN, Corridor, Limits, CNNRightLeft, BlockSide, FullName, WeekDay, FromHour, ToHour, Week1-Week5, Holidays, BlockSweepID, Line

| Column          | Type   | Meaning                                  |
|-----------------|--------|------------------------------------------|
| CNN             | string | Street segment ID                        |
| Corridor        | string | Street name                              |
| Limits          | string | Block range (e.g. "Market St to Main St")|
| CNNRightLeft    | string | Side of street (L/R)                     |
| BlockSide       | string | North/South/East/West                    |
| FullName        | string | Full street segment name                 |
| WeekDay         | string | Day of week (Mon, Tue, Wed, Thu, Fri)    |
| FromHour        | int    | Start hour (24hr format)                 |
| ToHour          | int    | End hour                                 |
| Week1-Week5     | int    | Which weeks of the month (0/1)           |
| Holidays        | string | Holiday handling flag                    |
| BlockSweepID    | string | Unique route ID                          |
| Line            | GeoJSON| Street segment geometry (LineString)     |

**Note**: Both datasets have 17 fields. The archived snapshot (`xsry-uuyt`) contains 37,878 rows.

## Query Examples

### Get all sweeping routes
```
https://data.sfgov.org/resource/xsry-uuyt.json
```

### Filter by street name
```
https://data.sfgov.org/resource/xsry-uuyt.json?corridor=Market%20St
```

### Filter by day of week
```
https://data.sfgov.org/resource/xsry-uuyt.json?weekday=Tues
```

### Spatial query - within bounding box (using SoQL)
```
https://data.sfgov.org/resource/xsry-uuyt.json?$where=within_box(line, 37.7, -122.5, 37.8, -122.3)
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
1. **Use the snapshot only** - `xsry-uuyt` is the frozen Jan 2025 dataset (37,878 rows)
2. **Do NOT use live API** - `yhqp-riqs` is broken/empty (under maintenance, 220 rows)
3. **Cache the snapshot locally** - Load once, use forever
4. **Local database recommended** - SQLite for offline capability

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

### Primary Data Source (Snapshot)
- Dataset: https://data.sfgov.org/City-Infrastructure/Archived-Street-Sweeping-data-as-of-Jan-27-2025-/xsry-uuyt/data
- API: https://data.sfgov.org/resource/xsry-uuyt.json
- CSV: https://data.sfgov.org/api/views/xsry-uuyt/rows.csv?accessType=DOWNLOAD

### Unreliable (Maintenance Mode)
- Dataset: https://data.sfgov.org/City-Infrastructure/Street-Sweeping-Schedule/yhqp-riqs (BROKEN - do not use)
- API Docs: https://dev.socrata.com/foundry/data.sfgov.org/yhqp-riqs
