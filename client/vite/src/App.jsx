import { useMemo } from 'react'
import { MediaPlayer } from "dashjs"
import './App.css'
import SingleVideo from './components/SingleVideo'

function App() {
  const player = useMemo(() => {
    return MediaPlayer().create();
  }, []);
  return (
    <>
      <SingleVideo player={player} />
    </>
  )
}

export default App
