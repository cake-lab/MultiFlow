import DashVideo from './DashVideo'
import { useEffect, useRef, useState } from 'react'
function SingleVideo({cameras, setCameras, getCameras}) {
    const [selectedCamera, setSelectedCamera] = useState(cameras.length > 0 ? cameras[0] : null);
    useEffect(() => {
        setSelectedCamera(cameras.length > 0 ? cameras[0] : null);
    }, [cameras]);
    return (
        <>
            {cameras.length > 0 ? (
                <div className="card">
                    <div style={{marginBottom:8}}>
                        <select className="select" value={selectedCamera} onChange={(e) => setSelectedCamera(e.target.value)}>
                            {cameras.map((camera, index) => (
                                <option key={index} value={camera}>
                                    {camera}
                                </option>
                            ))}
                        </select>
                    </div>
                    <DashVideo url={`/dash/${selectedCamera}/manifest.mpd`} />
                </div>
            ) : (
                <div className="empty-state">No cameras available</div>
            )}
        </>
    )
}
export default SingleVideo
