import { useState } from 'react'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix for default marker icon
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const DEFAULT_CENTER = [37.7749, -122.4194]
const DEFAULT_ZOOM = 13

function LocationMarker({ onLocationSelect }) {
  const [position, setPosition] = useState(null)
  
  useMapEvents({
    click(e) {
      setPosition(e.latlng)
      onLocationSelect(e.latlng.lat, e.latlng.lng)
    },
  })
  
  return position === null ? null : <Marker position={position} />
}

// Side selector component
function SideSelector({ selectedSides, onToggleSide }) {
  const validSides = ['E', 'W', 'N', 'S']
  
  return (
    <div style={{ marginLeft: '15px', display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
      {validSides.map(s => (
        <button
          key={s}
          className={selectedSides.includes(s) ? 'btn btn-success' : 'btn-secondary'}
          onClick={() => onToggleSide(s)}
          style={{ fontSize: '10px', padding: '2px 6px' }}
          title={`${s} side only`}
        >
          {s}
        </button>
      ))}
      {selectedSides.length === 0 && (
        <span style={{ marginLeft: '10px', fontSize: '12px', color: '#666' }}>
          All sides
        </span>
      )}
    </div>
  )
}

export default function Home() {
  const [address, setAddress] = useState('')
  const [sides, setSides] = useState({ E: false, W: false, N: false, S: false })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [schedule, setSchedule] = useState(null)
  const [lat, setLat] = useState(null)
  const [lng, setLng] = useState(null)
  
  // Toggle side selection
  const toggleSide = (sideKey) => {
    setSides(prev => ({ ...prev, [sideKey]: !prev[sideKey] }))
  }

  // Filter sides
  const selectedSides = Object.keys(sides).filter(s => sides[s])

  const searchAddress = async () => {
    if (!address.trim()) return
    
    setLoading(true)
    setError(null)
    setSchedule(null)
    
    // Combine geocode and sweep in parallel
    const [geoRes, sweepRes] = await Promise.allSettled([
      fetch('/api/v1/geocode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address }),
      }),
      fetch('/api/v1/sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          address, 
          ...(selectedSides.length > 0 && { side: selectedSides[0] }) 
        }),
      }),
    ])
    
    setSchedule(null)

    if (geoRes.status === 'fulfilled' && geoRes.value.ok) {
      const geoData = await geoRes.value.json()
      setLat(geoData.latitude)
      setLng(geoData.longitude)
      
      if (sweepRes.status === 'fulfilled' && sweepRes.value.ok) {
        const sweepData = await sweepRes.value.json()
        setSchedule(sweepData)
      } else if (sweepRes.status === 'rejected') {
        setError('Failed to fetch sweep schedule')
      }
    } else {
      setError('Could not geocode address')
    }
    
    setLoading(false)
  }
  
  const handleLocationSelect = async (latitude, longitude) => {
    setLat(latitude)
    setLng(longitude)
    setLoading(true)
    setError(null)
    setSchedule(null)
    
    try {
      const sweepRes = await fetch('/api/v1/sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          address: `${latitude}, ${longitude}`,
          ...(selectedSides.length > 0 && { side: selectedSides[0] })
        })
      })
      
      if (!sweepRes.ok) {
        const err = await sweepRes.json()
        throw new Error(err.detail || 'No sweeping schedule found')
      }
      
      const sweepData = await sweepRes.json()
      setSchedule(sweepData)
      setAddress(sweepData.address || '')
      
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  
  const saveLocation = () => {
    // TODO: Implement save to local storage
    alert('Saved! (Demo)')
  }
  
  return (
    <div>
      <div className="search-box">
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'nowrap' }}>
          <input
            type="text"
            className="search-input"
            placeholder="Enter address or tap map..."
            value={address}
            onChange={e => setAddress(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && searchAddress()}
            style={{ flex: 1 }}
          />
          <SideSelector selectedSides={selectedSides} onToggleSide={toggleSide} />
          <button 
            className="btn btn-primary" 
            onClick={searchAddress}
            disabled={loading}
          >
            {loading ? '..' : 'Search'}
          </button>
        </div>
      </div>
      
      {error && <div className="error">{error}</div>}
      
      {loading && <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>Searching...</div>}
      
      <div className="map-container">
        <MapContainer 
          center={lat ? [lat, lng] : DEFAULT_CENTER} 
          zoom={DEFAULT_ZOOM} 
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {lat && lng && <Marker position={[lat, lng]} />}
          <LocationMarker onLocationSelect={handleLocationSelect} />
        </MapContainer>
      </div>
      
      {schedule && schedule.message && !schedule.schedule?.length && (
        <div className="schedule-card" style={{ backgroundColor: '#fff3cd', border: '1px solid #ffc107' }}>
          <h3>Street Sweeping Schedule</h3>
          <p>{schedule.message}</p>
          <div style={{ borderTop: '1px solid #eee', marginTop: '1rem', paddingTop: '1rem' }}>
            <strong>Nearby streets in database:</strong>
            <ul style={{ marginTop: '0.5rem', maxHeight: '200px', overflowY: 'auto' }}>
              {schedule.available_corridors?.slice(0, 5).map((corridor, idx) => (
                <li key={idx}>{corridor.corridor} ({corridor.blockside})</li>
              ))}
            </ul>
            <p style={{ fontSize: '12px', marginTop: '0.5rem', color: '#856404' }}>
              Use the side buttons (E, W, N, S) to filter results.
            </p>
          </div>
        </div>
      )}
      
      {schedule && schedule.schedule && schedule.schedule.length > 0 && (
        <div className="schedule-card">
          <h3>Street Sweeping Schedule
            {selectedSides.length > 0 && (
              <span style={{ fontSize: '12px', color: '#666', marginLeft: '10px' }}>
                ({selectedSides.join(', ')})
              </span>
            )}
          </h3>
          <div className="schedule-info">
            <div className="schedule-row">
              <span className="schedule-label">Address:</span>
              <span className="schedule-value">{schedule.address}</span>
            </div>
            {schedule.schedule.length === 1 && schedule.schedule[0].distance_meters && (
              <div className="schedule-row">
                <span className="schedule-label">Distance:</span>
                <span className="schedule-value">
                  {Math.round(schedule.schedule[0].distance_meters)}m
                </span>
              </div>
            )}
            {schedule.schedule.map((item, idx) => (
              <div key={idx} style={{ borderTop: '1px solid #eee', padding: '10px 0' }}>
                <div
                  className="schedule-row"
                  style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '5px' }}
                >
                  <span style={{ marginRight: '10px' }}>{item.corridor}</span>
                  <span style={{ fontSize: '12px', color: '#666', fontWeight: 'normal' }}>
                    {item.limits}
                  </span>
                  <div style={{ marginLeft: 'auto' }}>
                    <SideSelector selectedSides={selectedSides} onToggleSide={toggleSide} />
                  </div>
                </div>
                <div className="schedule-row">
                  <span className="schedule-label">Side:</span>
                  <span className="schedule-value" style={{ display: 'inline-block' }}>
                    <strong>{item.blockside}</strong>
                  </span>
                </div>
                <div className="schedule-row">
                  <span className="schedule-label">Sweeps:</span>
                  <span className="schedule-value">
                    {item.weekday} - {item.fromhour}:00 to {item.tohour}:00
                  </span>
                </div>
                <div className="schedule-row">
                  <span className="schedule-label">Weeks:</span>
                  <span className="schedule-value">{item.fullname}</span>
                </div>
              </div>
            ))}
          </div>
          <button 
            className="btn btn-success" 
            style={{ marginTop: '1rem', width: '100%' }}
            onClick={saveLocation}
          >
            Save Location(s)
          </button>
        </div>
      )}
    </div>
  )
}