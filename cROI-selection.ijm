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
		
		// Background ROI selection
		setSlice(1);
		run("HiLo");
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
			makeRectangle(450, 5, 50, 50); // Default: top-right
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
		for (j=1; j<3; j++) {		
			setSlice(j);
			run("HiLo");
			bgmean=getResult("Mean1",j-1);
			run("Subtract...", "value=bgmean slice");			
		}
		selectWindow("Results");
		run("Close");

		rename(fname);			
		run("Median...", "radius=2 stack");
		
		// ROI selection, open pre-existing
		setSlice(1);
		roiManager("reset");
		roiManager("Show All with labels");
		roi_path = basepath + "--ROI.zip";
		
		if (File.exists(roi_path)) {
			roiManager("open",roi_path);
		}
		
		waitForUser("Select cells and add to the ROI manager");
		if (roiManager("count")!=0) {
			roiManager("save", roi_path);
		}
		else {
			waitForUser("Warning!", "No ROIs selected");
			if (roiManager("count")!=0) {
				roiManager("save", roi_path);
			}			
		}
		selectWindow(fname);
		close();
		roiManager("reset");
	}
}

waitForUser("We're done!", "Woohoo!");