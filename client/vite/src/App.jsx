import { useState, useEffect } from 'react'
import './styles.css'
import SingleVideo from './components/SingleVideo'
import AllVideos from './components/AllVideos'

function App() {
  const [videoMode, setVideoMode] = useState(0);
  const [cameras, setCameras] = useState([]);
  const [pastCameras, setPastCameras] = useState([]);
  const getCameras = () => {
    fetch('/info')
      .then(res => res.json())
      .then(data => {
        setCameras(data.cameras);
        setPastCameras(data.past_recordings);
      })
      .catch(err => {
        console.error("Error fetching camera info:", err);
      })
  }

  useEffect(() => {
    getCameras();
  }, []);
  const renderMode = () => {
    switch (videoMode) {
      case 0:
        return <SingleVideo cameras={cameras} setCameras={setCameras} getCameras={getCameras} />;
      case 1:
        return <AllVideos cameras={cameras} setCameras={setCameras} getCameras={getCameras} />;
      case 2:
        return <SingleVideo cameras={pastCameras} setCameras={setPastCameras} getCameras={getCameras} />;
      default:
        // Placeholder for future modes
        return <div>Unknown mode: {videoMode}</div>;
    }
  }
  return (
    <div>
      <div className="topbar">
        <div className="controls">
          {videoMode !== 0 && <button onClick={() => setVideoMode(0)}>Switch to Single-Video</button>}
          {videoMode !== 1 && <button onClick={() => setVideoMode(1)}>Switch to Multi-Video</button>}
          {videoMode !== 2 && <button onClick={() => setVideoMode(2)}>Switch to Past Recordings</button>}
          <button onClick={getCameras}>{cameras.length > 0 ? "Reload" : "Get"} Cameras</button>
        </div>
      </div>

      <div>
        {renderMode()}
      </div>
    </div>
  )
}

export default App

