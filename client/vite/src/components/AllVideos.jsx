import DashVideo from './DashVideo';
import React, { useState, useEffect } from 'react';
function AllVideos({cameras, setCameras, getCameras}) {
    return (
	<>
	  {cameras.length > 0 &&
	    <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '10px'}}>
	      {cameras.map((camera, index) => (
		<div key={index} style={{border: '1px solid black', padding: '10px'}}>
		  <h3>Camera {camera}</h3>
		  <DashVideo url={`/dash/${camera}/manifest.mpd`} />
		</div>
	      ))}
	    </div>
	  }
	</>
    )
}
export default AllVideos
