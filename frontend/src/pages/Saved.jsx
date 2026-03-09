import { useState, useEffect } from 'react'

// Demo data for saved locations
const DEMO_LOCATIONS = [
  {
    id: '1',
    address: '123 Market St, San Francisco',
    latitude: 37.7749,
    longitude: -122.4194,
    schedule: {
      corridor: 'Market St',
      limits: 'Larkin St - Polk St',
      weekday: 'Tuesday',
      fullname: 'Tuesday',
      fromhour: 5,
      tohour: 6,
    },
    nextSweep: 'Tomorrow',
  },
  {
    id: '2',
    address: '456 Valencia St, San Francisco',
    latitude: 37.7649,
    longitude: -122.4214,
    schedule: {
      corridor: 'Valencia St',
      limits: '14th St - 15th St',
      weekday: 'Wednesday',
      fullname: 'Wed 1st & 3rd',
      fromhour: 8,
      tohour: 10,
    },
    nextSweep: 'Wednesday',
  },
]

export default function Saved() {
  const [locations, setLocations] = useState([])
  
  useEffect(() => {
    // Load from localStorage or use demo data
    const saved = localStorage.getItem('savedLocations')
    if (saved) {
      setLocations(JSON.parse(saved))
    } else {
      setLocations(DEMO_LOCATIONS)
    }
  }, [])
  
  const deleteLocation = (id) => {
    const updated = locations.filter(loc => loc.id !== id)
    setLocations(updated)
    localStorage.setItem('savedLocations', JSON.stringify(updated))
  }
  
  if (locations.length === 0) {
    return (
      <div className="empty-state">
        <h3>No saved locations</h3>
        <p>Go to Map to add parking spots</p>
      </div>
    )
  }
  
  return (
    <div className="location-list">
      {locations.map(loc => (
        <div key={loc.id} className="location-item">
          <div className="location-info">
            <h4>{loc.address}</h4>
            <p>
              {loc.schedule.weekday} {loc.schedule.fullname} &bull; {loc.schedule.fromhour}:00-{loc.schedule.tohour}:00
            </p>
            <p className="schedule-value danger">Next: {loc.nextSweep}</p>
          </div>
          <div className="location-actions">
            <button 
              className="btn btn-danger btn-small"
              onClick={() => deleteLocation(loc.id)}
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
