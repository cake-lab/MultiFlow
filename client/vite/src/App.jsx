import { useState } from 'react'
import './App.css'
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
  return (
    <>
      {singleVideo ? 
        <>
	  <button onClick={() => setSingleVideo(false)}>Switch to Multi Video</button>
    <SingleVideo cameras={cameras} setCameras={setCameras} getCameras={getCameras} />
	  </>
	:
	<>
	  <button onClick={() => setSingleVideo(true)}>Switch to Single Video</button>
    <AllVideos cameras={cameras} setCameras={setCameras} getCameras={getCameras}/>
	</>
	}
	{cameras.length === 0 && <button onClick={getCameras}>Get Cameras</button>}
    </>
  )
}

export default App
