//Use these lines to get the order of the channels
def viewer = getCurrentViewer()
def channels = viewer.getImageDisplay().availableChannels()
print(channels)


//Then manually put the names you need in order as strings and run
setChannelNames("DAPI-quad", "TRITC", "Cy5-quad", "FITC-quad")

//Rerun cell detection to update metrics
