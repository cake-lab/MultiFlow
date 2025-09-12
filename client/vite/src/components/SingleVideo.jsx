import DashVideo from './DashVideo'
import { useEffect, useRef, useState } from 'react'
function SingleVideo({player}) {
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
            {
                cameras.length > 0 ?
                    <>
                        <select>
                            {cameras.map((camera, index) => (
                                <option key={index} value={camera}>
                                    {camera}
                                </option>
                            ))}
                        </select>
                        <DashVideo player={player} url={`/dash/0/manifest.mpd`} />
                    </>
                    : 
                    <button onClick ={()=> getCameras()}>Reload Video</button>
            }
        </>
    )
}
export default SingleVideo