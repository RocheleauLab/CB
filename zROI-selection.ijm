dir = getDirectory("Choose a Directory ");
list = getFileList(dir);

for (i=0; i<list.length; i++) {
	path = dir+list[i];
	// Open .lsm files
	if (endsWith(path,".lsm")) { 
		open(path);
		origname=getTitle();
		fname=replace(origname, ".lsm", "");
		basepath = dir + fname;
		
		// Apply LUT (view-only)
		for (j=1; j<nSlices; j++) {
			setSlice(j);
			if ((j%3)!=0){
				run("HiLo");
			}
		}
		
		// Background ROI selection
		setSlice(1);
		setTool("rectangle");
		if (isOpen("ROI Manager")) {
			roiManager("reset");
		}
		else {
			run("ROI Manager...");
		}
		roiManager("Show All with labels");
		bg_roi_path = basepath + "--BGROI.zip";
		
		if (File.exists(bg_roi_path)) { // Open pre-existing
			roiManager("open",bg_roi_path);
			roiManager("Select", 0);
		}
		else{		
			makeRectangle(5, 5, 50, 50); // Default: top-left
		}
		waitForUser("Select Background", "Select background!");
		if (roiManager("count")==0) {
			roiManager("Add");
		}

		if (roiManager("count")==1) {
			roiManager("save", bg_roi_path);
		}
		else{
			waitForUser("Warning!", "BG ROI !=1");
			if (roiManager("count")==1) {
				roiManager("save", bg_roi_path);
			}
		}

		// Background ROI subtraction and apply median filter (view-only)
		roiManager("Multi Measure");
		roiManager("reset");
		run("Select None");
		for (j=1; j<nSlices; j++) {		
			setSlice(j);
			if ((j%3)!=0){
				bgmean=getResult("Mean1",j-1);
				run("Subtract...", "value=bgmean slice");
			}			
		}
		selectWindow("Results");
		run("Close");

		rename(fname);			
		run("Median...", "radius=2 stack");
		
		// Islet ROI selection, open pre-existing
		setSlice(1);
		roiManager("reset");
		roiManager("Show All with labels");
		roi_path = basepath + "--ROI.zip";
		
		if (File.exists(roi_path)) {
			roiManager("open",roi_path);
		}
		
		waitForUser("Select ISLET/ROI and add to the ROI manager");
		if (roiManager("count")!=0) {
			roiManager("save", roi_path);
		} // Default: entire image
		
		// Debris ROI selection, open pre-existing
		setSlice(1);
		roiManager("reset");
		roiManager("Show All with labels");
		xroi_path = basepath + "--xROI.zip";
		if (File.exists(xroi_path)) {
			roiManager("open",xroi_path);
		}
		
		waitForUser("Select xROI and add to the ROI manager");
		if (roiManager("count")!=0) {
			roiManager("save", xroi_path);
		}  // Default: no debris
		
		selectWindow(fname);
		close();
		roiManager("reset");
	}
}

waitForUser("We're done!", "Woohoo!");