run("Split Channels");
close();
run("Duplicate...", "title=Green");
run("Duplicate...", "title=Dev");
run("Variance...", "radius=0.5");
selectWindow("Green");
imageCalculator("Subtract create", "Green","Dev");
selectWindow("Result of Green");
run("Options...", "iterations=1 count=1 do=Nothing");
run("Options...", "iterations=1 count=1 black");
setOption("BlackBackground", true);
run("Make Binary");
run("Options...", "iterations=1 count=1 do=Nothing");
run("Make Binary");
//run invert for blocks where original method fails
//run("Invert");
run("Despeckle");
run("Despeckle");
run("Analyze Particles...", "size=0-2500 show=[Overlay Masks] add");
if (Overlay.size > 0) {

	if (nImages > 0) {
		run("Send Overlay to QuPath", "choose_object_type=Detection");
      		while (nImages>0) { 
          		selectImage(nImages); 
          		close(); 
      					}
			} 
}
