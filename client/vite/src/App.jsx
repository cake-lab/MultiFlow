import { useState, useEffect } from 'react'
import './styles.css'
import SingleVideo from './components/SingleVideo'
import AllVideos from './components/AllVideos' 
function App() {
  // Each DashVideo creates its own MediaPlayer instance now.
  const [singleVideo, setSingleVideo] = useState(true);
  const [cameras, setCameras] = useState([]);
  const getCameras = () => {
    fetch('/info').then(res => res.json()).then(data => {
	setCameras(data.cameras);
    }).catch(err => {
	console.error("Error fetching camera info:", err);
    })
  }
  useEffect(() => {
    getCameras();
  }, []);
  return (
    <div>
      <div className="topbar">
        <div className="controls">
          {singleVideo ? (
            <button onClick={() => setSingleVideo(false)}>Switch to Multi Video</button>
          ) : (
            <button onClick={() => setSingleVideo(true)}>Switch to Single Video</button>
          )}
          <button onClick={getCameras}>{cameras.length > 0? "Reload" : "Get" } Cameras</button>
        </div>
      </div>

      {singleVideo ? (
        <div>
          <SingleVideo cameras={cameras} setCameras={setCameras} getCameras={getCameras} />
        </div>
      ) : (
        <div>
          <AllVideos cameras={cameras} setCameras={setCameras} getCameras={getCameras} />
        </div>
      )}
    </div>
  )
}

export default App
