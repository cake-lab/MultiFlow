import DashVideo from './DashVideo';
import React, { useState, useEffect } from 'react';
function AllVideos({cameras, setCameras, getCameras}) {
    return (
    	<>
    	  {cameras.length > 0 ? (
    	    <div className="grid">
    	      {cameras.map((camera, index) => (
    		<div key={index} className="card">
    		  <h3>Camera {camera}</h3>
    		  <DashVideo url={`/dash/${camera}/manifest.mpd`} />
    		</div>
    	      ))}
    	    </div>
    	  ) : (
    	    <div className="empty-state">No cameras available</div>
    	  )}
    	</>
    )
}
export default AllVideos
