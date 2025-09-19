import { useMemo, useState } from 'react'
import { MediaPlayer } from "dashjs"
import './App.css'
import SingleVideo from './components/SingleVideo'
import AllVideos from './components/AllVideos' 
function App() {
  const player = useMemo(() => {
    return MediaPlayer().create();
  }, []);
  const [singleVideo, setSingleVideo] = useState(true);
  return (
	<>
		{singleVideo ? 
			<>
				<button onClick={() => setSingleVideo(false)}>Switch to Multi Video</button>
				<SingleVideo player={player} />
			</>
       		:
			<>
				<button onClick={() => setSingleVideo(true)}>Switch to Single Video</button>
				<AllVideos player={player} />
			</>
		}
	</>
  )
}

export default App
