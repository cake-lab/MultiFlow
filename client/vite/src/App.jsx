import { useMemo } from 'react'
import { MediaPlayer } from "dashjs"
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import DashVideo from './components/DashVideo'

function App() {
  const player = useMemo(() => {
    return MediaPlayer().create();
  }, []);
  return (
    <>
      <DashVideo player={player} url="/dash/0/manifest.mpd"/>
    </>
  )
}

export default App
