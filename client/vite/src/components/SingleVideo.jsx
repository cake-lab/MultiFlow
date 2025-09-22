import DashVideo from './DashVideo'
import { useEffect, useRef, useState } from 'react'
function SingleVideo({player, cameras, setCameras, getCameras}) {
    const [selectedCamera, setSelectedCamera] = useState(cameras.length > 0 ? cameras[0] : null);
    return (
        <>
            {
                cameras.length > 0 &&
                    <>
                        <select value={selectedCamera} onChange={(e) => setSelectedCamera(e.target.value)}>
                            {cameras.map((camera, index) => (
                                <option key={index} value={camera}>
                                    {camera}
                                </option>
                            ))}
                        </select>
                        <DashVideo player={player} url={`/dash/${selectedCamera}/manifest.mpd`} />
                    </>
            }
        </>
    )
}
export default SingleVideo
