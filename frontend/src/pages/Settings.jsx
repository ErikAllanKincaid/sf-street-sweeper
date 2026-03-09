import { useState, useEffect } from 'react'

export default function Settings() {
  const [settings, setSettings] = useState({
    notificationHours: 12,
    enablePush: true,
    enableSms: false,
    enableEmail: false,
    quietHoursEnabled: false,
    quietHoursStart: 22,
    quietHoursEnd: 7,
  })
  
  useEffect(() => {
    const saved = localStorage.getItem('notificationSettings')
    if (saved) {
      setSettings(JSON.parse(saved))
    }
  }, [])
  
  const updateSetting = (key, value) => {
    const updated = { ...settings, [key]: value }
    setSettings(updated)
    localStorage.setItem('notificationSettings', JSON.stringify(updated))
  }
  
  const requestNotificationPermission = async () => {
    if (!('Notification' in window)) {
      alert('This browser does not support notifications')
      return
    }
    
    const permission = await Notification.requestPermission()
    if (permission === 'granted') {
      alert('Notifications enabled!')
    }
  }
  
  return (
    <div>
      <div className="settings-section">
        <h3>Notifications</h3>
        
        <div className="setting-row">
          <span className="setting-label">Enable Push Notifications</span>
          <input
            type="checkbox"
            checked={settings.enablePush}
            onChange={e => updateSetting('enablePush', e.target.checked)}
          />
        </div>
        
        <div className="setting-row">
          <span className="setting-label">Notify before (hours)</span>
          <select
            className="setting-input"
            value={settings.notificationHours}
            onChange={e => updateSetting('notificationHours', parseInt(e.target.value))}
          >
            <option value={6}>6 hours</option>
            <option value={12}>12 hours</option>
            <option value={24}>24 hours</option>
          </select>
        </div>
        
        <button 
          className="btn btn-primary" 
          style={{ marginTop: '1rem', width: '100%' }}
          onClick={requestNotificationPermission}
        >
          Enable Browser Notifications
        </button>
      </div>
      
      <div className="settings-section">
        <h3>Quiet Hours</h3>
        
        <div className="setting-row">
          <span className="setting-label">Enable Quiet Hours</span>
          <input
            type="checkbox"
            checked={settings.quietHoursEnabled}
            onChange={e => updateSetting('quietHoursEnabled', e.target.checked)}
          />
        </div>
        
        {settings.quietHoursEnabled && (
          <div className="setting-row">
            <span className="setting-label">Quiet time</span>
            <div>
              <select
                className="setting-input"
                value={settings.quietHoursStart}
                onChange={e => updateSetting('quietHoursStart', parseInt(e.target.value))}
              >
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>{i}:00</option>
                ))}
              </select>
              <span> - </span>
              <select
                className="setting-input"
                value={settings.quietHoursEnd}
                onChange={e => updateSetting('quietHoursEnd', parseInt(e.target.value))}
              >
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>{i}:00</option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>
      
      <div className="settings-section">
        <h3>About</h3>
        <p style={{ color: 'var(--gray-500)', fontSize: '0.875rem' }}>
          SF Street Sweeper v0.1.0<br />
          Data from SF Open Data
        </p>
      </div>
    </div>
  )
}
