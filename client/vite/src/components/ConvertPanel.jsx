import React, { useEffect, useRef } from 'react'

function ConvertPanel({ 
  pastRecordings,
  convertedFiles,
  converting, setConverting,
  fetchInfo
}) {
  const eventSources = useRef({})

  useEffect(() => {
    // Ensure event sources exist for active conversions
    converting.forEach(id => {
      if (!eventSources.current[id]) {
        const es = new EventSource(`/convert-status/${encodeURIComponent(id)}`)
        es.onmessage = (e) => {
          const status = (e.data || '').trim()
          if (status === 'in_progress') {
            setConverting(prev => Array.from(new Set([...prev, id])))
          } else if (status === 'completed') {
            // conversion done — remove from converting and refresh info
            setConverting(prev => prev.filter(x => x !== id))
            fetchInfo()
            es.close()
            delete eventSources.current[id]
          } else if (status === 'not_found') {
            setConverting(prev => prev.filter(x => x !== id))
            es.close()
            delete eventSources.current[id]
            fetchInfo()
          }
        }
        es.onerror = () => {
          // keep trying; close if readyState closed
          if (es.readyState === EventSource.CLOSED) {
            es.close()
            delete eventSources.current[id]
          }
        }
        eventSources.current[id] = es
      }
    })
  }, [converting])

  const startConversion = (cameraId) => {
    fetch(`/convert/${encodeURIComponent(cameraId)}`, { method: 'POST' })
      .then(res => {
        if (res.status === 202) return res.json()
        return res.json().then(err => Promise.reject(err))
      })
      .then(() => {
        // add to converting and open eventsource (effect hook will do the rest)
        setConverting(prev => Array.from(new Set([...prev, cameraId])))
      })
      .catch(err => {
        console.error('Failed to start conversion', err)
        alert('Failed to start conversion: ' + (err && err.error ? err.error : JSON.stringify(err)))
      })
  }

  const downloadFile = (filename) => {
    // open the download endpoint in a new tab/window to trigger download
    window.open(`/download/${encodeURIComponent(filename)}`, '_blank')
  }

  // compute lists
  const convertedBasenames = new Set((convertedFiles || []).map(f => f.replace(/\.mp4$/i, '')))
  const availableToConvert = (pastRecordings || []).filter(id => !convertedBasenames.has(id) && !(converting || []).includes(id))

  return (
    <div className="card">
      <h2>Conversions & Downloads</h2>
      <div style={{display:'flex', gap:16, alignItems:'flex-start'}}>
        <div style={{flex:1}}>
          <h3>Converting</h3>
          {converting.length === 0 ? <div className="empty-state">No conversions in progress</div> : (
            <ul>
              {converting.map(id => (
                <li key={id} style={{marginBottom:8}}>
                  <strong>{id}</strong>
                  <span style={{marginLeft:8}}>⏳ in progress</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div style={{flex:1}}>
          <h3>Available for conversion</h3>
          {availableToConvert.length === 0 ? <div className="empty-state">No available recordings to convert</div> : (
            <ul>
              {availableToConvert.map(id => (
                <li key={id} style={{marginBottom:8}}>
                  <span>{id}</span>
                  <button style={{marginLeft:8}} onClick={() => startConversion(id)}>Convert</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div style={{flex:1}}>
          <h3>Available downloads</h3>
          {convertedFiles.length === 0 ? <div className="empty-state">No converted files</div> : (
            <ul>
              {convertedFiles.map(f => (
                <li key={f} style={{marginBottom:8}}>
                  <span>{f}</span>
                  <button style={{marginLeft:8}} onClick={() => downloadFile(f)}>Download</button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}

export default ConvertPanel
