# SF Street Sweeper

A San Francisco street sweeping reminder application that helps you know when to move your car. Fetches real SF Open Data and notifies you before street cleaning.

## Background

San Francisco sweeps streets on predictable schedules, but the data is scattered across hundreds of street segments. This application aggregates that information and provides a simple interface to find when your parking spot will be cleaned.

### This app offers:

- **Offline-first**: Data cached locally
- **Open Source**: Free forever
- **Privacy-focused**: No required account
- **Cross-platform**: Runs anywhere (web, mobile, desktop)

### Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Frontend (React/Vite)               │
│                          :5173                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Map (Leaflet)                                  │   │
│  │  Schedule Display                               │   │
│  │  Saved Locations (localStorage)                 │   │
│  │  Calendar Integration                           │   │
│  │  └─────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
                          ↕ REST API
┌────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                    │
│                         :8765                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  /health                                        │   │
│  │  /api/v1/geocode   → Nominatim API              │   │
│  │  /api/v1/sweep     → SF Open Data + Shapely     │   │
│  │  /api/v1/calendar  → Google Calendar URL        │   │
│  │  /api/v1/subscribe → Notification stub          │   │
│  └─────────────────────────────────────────────────┘   │
│                         ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  sf_sweep_data.json (37,878 street segments)    │   │
│  │  Shapely STRtree (spatial index)                │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘

     Architecture Overview                                                            

     ┌─────────────────────────────────────────────────────────┐                      
     │                 Frontend (React/Vite)                   │                     
     │   - React Router (3 pages: Home, Saved, Settings)       │                     
     │   - Leaflet map with React-Leaflet                      │                     
     │   - PWA (Service Worker for offline support)            │                     
     └────────────────────┬────────────────────────────────────┘                      
                          │ REST API calls                                            
                          ▼                                                           
     ┌─────────────────────────────────────────────────────────┐                      
     │              Backend (FastAPI/Python)                   │                     
     │  ┌─────────────┬─────────────┬──────────────┐           │                       
     │  │   main.py   │   api.py    │   models.py  │           │                       
     │  └──────┬──────┴──────┬──────┴──────┬───────┘           │                       
     │         │             │             │                   │                      
     │  ┌──────▼─────────────▼───▼─────────┤                   │                      
     │  │      Services Layer              │                   │                      
     │  │  - sf_data.py  - geocoding.py    │                   │                      
     │  │  - calendar.py                   │                   │                             
     │  └──────────────────────────────────┘                   │                           
     └─────────────────────────────────────────────────────────┘  
```

## Starting the Application

### Option 1: Docker Containers (Recommended)

**Prerequisites**:

- Docker installed

**Setup**:

```bash
cd sf-street-sweeper

# Build backend
cd backend
uv pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8765 &
cd ..

# Build frontend
cd frontend
npm install
cd ..

# Start containers
docker compose up -d
```

**Result**:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8765
- API Docs: http://localhost:8765/docs

**Access from another computer**:
Replace `localhost` with your server IP:

```
frontend: http://localhost:5173
backend:  http://localhost:8765
```

Check your IP:

```bash
hostname -I
```

**View logs**:

```bash
# Both containers
docker compose logs -f

# Backend only
docker logs sf-street-sweeper-backend-1 -f

# Frontend only
docker logs sf-street-sweeper-frontend-1 -f
```

**Stop containers**:

```bash
docker compose down
```

---

### Option 2: Bare Metal (Development)

**Prerequisites:**

- Python 3.12
- Node.js 20+
- npm

**Backend Setup:**

```bash
# Navigate to backend directory
cd sf-street-sweeper/backend

# Create virtual environment
uv venv    # or: python -m venv venv
source .venv/bin/activate    # or: source venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Start the server
uv run uvicorn main:app --host 0.0.0.0 --port 8765
```

**Frontend Setup:**

```bash
# In a new terminal, navigate to frontend directory
cd sf-street-sweeper/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Access:**

- Frontend: http://localhost:5173 (Vite dev server)
- Backend: http://localhost:8765

**Production Build:**

```bash
# Build optimized frontend
npm run build

# The built files are in frontend/dist/
# Deploy to any static host with nginx serving /dist/ and proxying /api/
```

---

## Using the Application

### Main Features

#### 1. Map View (Home)

**Search by Address:**

1. Type an address in the search box
2. Click "Search"
3. Results show on map with full schedule details

**Search by Map Click:**

1. Click anywhere on the map
2. Automatic reverse geocoding
3. Find nearest street sweeping route

**Side Selection:**

- Click E, W, N, S buttons to filter results
- Shows only that side of the street
- Useful when address geocodes near street but side unclear

**Results Display:**

- Street name and limits (block range)
- Side (E/W/N/S)
- Sweep days (e.g., "Tue 2nd & 4th")
- Times (e.g., "9:00-11:00")
- Distance from your query

#### 2. Google Calendar Integration

1. Find your street schedule
2. Click "Add to Google Calendar"
3. Opens Google Calendar with reminder event
4. Event set for 24 hours before sweep
5. Shows next 3 months of sweep dates

**Why 24 hours before?**

- SF streets typically sweep 9-11am
- Gives you time to move car before sweep starts
- Better than last-minute panic

#### 3. Saved Locations

Save frequently parked spots:

1. Click "Save Location(s)" button
2. Stored in browser localStorage
3. Accessible from "Saved" tab
4. Can delete individual locations

### Scheduled Streets (SF Conventions)

Streets use "named weeks" for their 2-week cycle:

- **Mon/Fri 1st & 3rd**: Sweeps week 1 (Mon-Fri 1st), week 3 (Mon-Fri 3rd)
- **Tue 2nd & 4th**: Sweeps week 2 (Tue 2nd), week 4 (Tue 4th)
- **Wed 1st-5th**: Sweeps every week
- **Every Week**: Sweeps all days

### API Reference

**Health Check:**

```bash
curl http://localhost:8765/health
# Returns: {"status": "healthy"}
```

**Geocode:**

```bash
curl -X POST http://localhost:8765/api/v1/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "301 Clipper Street, San Francisco"}'

# Returns:
# {
#   "address": "359, Clipper Street, ...",
#   "latitude": 37.7488919,
#   "longitude": -122.4319063
# }
```

**Get Sweep Schedule:**

```bash
curl -X POST http://localhost:8765/api/v1/sweep \
  -H "Content-Type: application/json" \
  -d '{"address": "359 Clipper Street, San Francisco", "side": "South"}'

# Returns full schedule with multiple segments
```

**Create Calendar Event:**

```bash
curl -X POST http://localhost:8765/api/v1/calendar \
  -H "Content-Type: application/json" \
  -d '{
    "address": "359 Clipper Street, San Francisco",
    "corridor": "Clipper St",
    "blockside": "South",
    "limits": "Noe St - Castro St",
    "weekday": "Tues",
    "fullname": "Tue 2nd & 4th",
    "fromhour": 9,
    "tohour": 11,
    "week1": false,
    "week2": true,
    "week3": false,
    "week4": true,
    "week5": false,
    "reminder_hours": 24
  }'

# Returns: {
#   "calendar_url": "https://calendar.google.com/...",
#   "next_sweep_dates": ["2024-03-15 09:00", "..."]
# }
```

### Data Sources

**Street Sweeping Schedule:**

- Source: SF Open Data (Dataset: `xsry-uuyt`)
- 37,878 street segments
- Last updated: Jan 27, 2025
- Cached locally for offline use

**Geocoding:**

- Source: Nominatim (OpenStreetMap)
- Free, no API key required
- SF-bounding box validation

---

## Development

### Project Structure

```
sf-street-sweeper/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile
│   └── app/
│       ├── api.py              # API routes
│       ├── models.py           # Pydantic schemas
│       ├── services/
│       │   ├── sf_data.py      # SF Open Data + spatial queries
│       │   ├── geocoding.py    # Nominatim integration
│       │   ├── calendar.py     # Google Calendar generation
│       │   └── scheduler.py    # Notification stub
│       └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Router
│   │   ├── main.jsx            # React entry
│   │   ├── pages/
│   │   │   ├── Home.jsx        # Map + search
│   │   │   ├── Saved.jsx       # Saved locations
│   │   │   └── Settings.jsx    # Preferences
│   │   └── index.css           # Styles
│   ├── package.json
│   ├── vite.config.js          # Build config
│   ├── Dockerfile
│   └── nginx.conf              # API proxy config
├── sf_sweep_data.json          # Cached SF data
├── docker-compose.yml
└── RESEARCH.md
```

### Running Tests

```bash
# Backend tests
pytest backend/tests/

# Frontend tests
npm run test -- frontend/src/
```

### Adding New Features

1. **Frontend:**
   
   - Add component in `frontend/src/pages/`
   - Import in `App.jsx`
   - Add route
   - Style in `index.css`

2. **Backend:**
   
   - Add route in `backend/app/api.py`
   - Add service method in appropriate `backend/app/services/`
   - Add Pydantic models in `backend/app/models.py`

3. **API Proxy:**
   
   - Frontend proxies `/api` to backend automatically
   - No config needed for same-origin
   - Docker uses nginx proxy config in `frontend/nginx.conf`

---

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8765
lsof -ti:8765 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Container Won't Start

```bash
# Check logs
docker logs sf-street-sweeper-backend-1

# Rebuild
docker compose build --no-cache

# Restart
docker compose restart
```

### Data Not Updating

The SF data is cached in `sf_sweep_data.json` to work offline. To refresh:

```bash
# Delete cache to force reload
cd sf-street-sweeper
rm sf_sweep_data.json

# Backend will fetch fresh data on next request
```

### CORS Issues

Backend has CORS enabled for development (`allow_origins=["*"]`).
In production, restrict to your frontend domain.

### Slow Performance

- Backend caches SF data after first load
- Geocoding results cached
- Reduce timeout for external APIs if needed

---

## Contributing

Contributions welcome! Areas needed:

- [ ] Real-time notifications (Pusher/SignalR)
- [ ] User accounts (GitHub Auth)
- [ ] Garage deal integration
- [ ] Linux desktop app (Tauri/Qt)
- [ ] Mobile apps (React Native)
- [ ] Predictive parking availability
- [ ] Street-level photos

### Development Setup

```bash
# Clone and navigate
git clone https://github.com/you/sf-street-sweeper.git
cd sf-street-sweeper

# Start with Docker
docker compose up -d

# Or development mode
# Terminal 1: cd backend && uv run uvicorn main:app
# Terminal 2: cd frontend && npm run dev
```

---

## Acknowledgments

- SF Open Data API for street sweeping schedules
- OpenStreetMap/Nominatim for geocoding
- Leaflet for mapping
- FastAPI for backend framework
- Vite for frontend build

## Changelog

### v0.1.0 (2026-03-08)

- Initial release
- Map search and schedule lookup
- Google Calendar integration
- Saved locations
- Offline data cache
- Docker containerization
- API documentation
