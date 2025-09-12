import {useState, useEffect, useRef} from "react"
import dashjs from "dashjs"

function DashVideo({player, url}) {
    const video = useRef(null);
    useEffect(() => {
        if (video.current && url && player) {
            player.initialize(video.current, url, true);
            return () => {
                player.reset();
            };
        }
    }, [url]);
    return (
        <video ref={video} controls style={{ width: "100%", height: "auto" }} />
    )
}
export default DashVideo