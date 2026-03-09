import { useState, useEffect } from 'react'
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

// Default to San Francisco
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

export default function Home() {
  const [address, setAddress] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [schedule, setSchedule] = useState(null)
  const [lat, setLat] = useState(null)
  const [lng, setLng] = useState(null)
  
  const searchAddress = async () => {
    if (!address.trim()) return
    
    setLoading(true)
    setError(null)
    setSchedule(null)
    
    try {
      // Geocode the address
      const geoRes = await fetch('/api/v1/geocode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address })
      })
      
      if (!geoRes.ok) {
        throw new Error('Could not find that address')
      }
      
      const geoData = await geoRes.json()
      setLat(geoData.latitude)
      setLng(geoData.longitude)
      
      // Get sweep schedule
      const sweepRes = await fetch('/api/v1/sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address })
      })
      
      if (!sweepRes.ok) {
        const err = await sweepRes.json()
        throw new Error(err.detail || 'No sweeping schedule found')
      }
      
      const sweepData = await sweepRes.json()
      setSchedule(sweepData)
      
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  
  const handleLocationSelect = async (latitude, longitude) => {
    setLat(latitude)
    setLng(longitude)
    setLoading(true)
    setError(null)
    
    try {
      const sweepRes = await fetch('/api/v1/sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          address: `${latitude}, ${longitude}` 
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
        <input
          type="text"
          className="search-input"
          placeholder="Enter address or tap map..."
          value={address}
          onChange={e => setAddress(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && searchAddress()}
        />
        <button 
          className="btn btn-primary" 
          onClick={searchAddress}
          disabled={loading}
        >
          {loading ? '...' : 'Search'}
        </button>
      </div>
      
      {error && <div className="error">{error}</div>}
      
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
      
      {schedule && (
        <div className="schedule-card">
          <h3>Street Sweeping Schedule</h3>
          <div className="schedule-info">
            <div className="schedule-row">
              <span className="schedule-label">Street:</span>
              <span className="schedule-value">{schedule.schedule?.[0]?.corridor}</span>
            </div>
            <div className="schedule-row">
              <span className="schedule-label">Block:</span>
              <span className="schedule-value">{schedule.schedule?.[0]?.limits}</span>
            </div>
            <div className="schedule-row">
              <span className="schedule-label">Side:</span>
              <span className="schedule-value">{schedule.schedule?.[0]?.blockside}</span>
            </div>
            <div className="schedule-row">
              <span className="schedule-label">Day:</span>
              <span className="schedule-value">{schedule.schedule?.[0]?.weekday}</span>
            </div>
            <div className="schedule-row">
              <span className="schedule-label">Weeks:</span>
              <span className="schedule-value">{schedule.schedule?.[0]?.fullname}</span>
            </div>
            <div className="schedule-row">
              <span className="schedule-label">Time:</span>
              <span className="schedule-value">
                {schedule.schedule?.[0]?.fromhour}:00 - {schedule.schedule?.[0]?.tohour}:00
              </span>
            </div>
            {schedule.schedule?.[0]?.distance_meters && (
              <div className="schedule-row">
                <span className="schedule-label">Distance:</span>
                <span className="schedule-value">
                  {Math.round(schedule.schedule[0].distance_meters)}m
                </span>
              </div>
            )}
          </div>
          <button 
            className="btn btn-success" 
            style={{ marginTop: '1rem', width: '100%' }}
            onClick={saveLocation}
          >
            Save Location
          </button>
        </div>
      )}
    </div>
  )
}
