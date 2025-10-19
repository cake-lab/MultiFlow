import {useEffect, useRef} from "react"
import { MediaPlayer } from "dashjs"

function DashVideo({player, url}) {
    const video = useRef(null);
    const localPlayer = useRef(null);

    // create a local player instance for this component only
    useEffect(() => {
        try {
            localPlayer.current = MediaPlayer().create();
        } catch (e) {
            console.error('Failed to create dash player instance', e);
            localPlayer.current = null;
        }
        return () => {
            try { if (localPlayer.current) localPlayer.current.reset(); } catch (e) { /* ignore */ }
            localPlayer.current = null;
        };
    }, []);

    useEffect(() => {
        const p = localPlayer.current || player;
        if (video.current && url && p) {
            try {
                p.initialize(video.current, url, true);
            } catch (e) {
                console.error('Initialize failed', e);
            }
            return () => {
                try { if (localPlayer.current) localPlayer.current.reset(); else if (player) player.reset(); } catch (e) { /* ignore */ }
            };
        }
    }, [url, player]);

    const reload = () => {
        const p = localPlayer.current || player;
        try {
            if (p) p.reset();
        } catch (e) { /* ignore */ }
        try {
            if (video.current && url && p) p.initialize(video.current, url, true);
        } catch (e) { console.error('Reload failed', e); }
    };

    return (
        <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
            <video ref={video} controls style={{ width: "100%", height: "auto", display: 'block' }} />
            <button
                onClick={reload}
                title="Reload stream"
                style={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    zIndex: 10,
                    background: 'rgba(0,0,0,0.5)',
                    color: 'white',
                    border: 'none',
                    padding: '6px 8px',
                    borderRadius: 4,
                    cursor: 'pointer',
                    fontSize: 12,
                    opacity: 0.9,
                }}
            >⟳</button>
        </div>
    )
}
export default DashVideo