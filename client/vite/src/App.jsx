import { useState, useEffect } from 'react'
import './styles.css'
import SingleVideo from './components/SingleVideo'
import AllVideos from './components/AllVideos'
import ConvertPanel from './components/ConvertPanel'

function App() {
  const [videoMode, setVideoMode] = useState(0);
  const [cameras, setCameras] = useState([]);
  const [pastCameras, setPastCameras] = useState([]);
  const [convertedFiles, setConvertedFiles] = useState([])
  const [converting, setConverting] = useState([])
  const getInfo = () => {
    fetch('/info')
      .then(res => res.json())
      .then(data => {
        setCameras(data.cameras);
        setPastCameras(data.past_recordings);
        setConvertedFiles(data.converted_files)
        setConverting(data.conversions_in_progress)
      })
      .catch(err => {
        console.error("Error fetching camera info:", err);
      })
  }

  useEffect(() => {
    getInfo();
  }, []);
  const renderMode = () => {
    switch (videoMode) {
      case 0:
        return <SingleVideo cameras={cameras} setCameras={setCameras} getCameras={getInfo} />;
      case 1:
        return <AllVideos cameras={cameras} setCameras={setCameras} getCameras={getInfo} />;
      case 2:
        return <SingleVideo cameras={pastCameras} getCameras={getInfo} />;
      case 3:
        return <ConvertPanel
            pastRecordings={pastCameras}
            convertedFiles={convertedFiles}
            converting={converting}
            setConverting={setConverting}
            fetchInfo={getInfo}
          />;
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
          {videoMode !== 3 && <button onClick={() => setVideoMode(3)}>Switch to Convert/Downloads</button>}
          <button onClick={getInfo}>{cameras.length > 0 || pastCameras.length > 0 ? "Refresh" : "Get"} Past/Current Recordings</button>
        </div>
      </div>

      <div>
        {renderMode()}
      </div>
    </div>
  )
}

export default App

