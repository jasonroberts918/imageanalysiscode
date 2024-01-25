
#Change path here, this is where your data is
path ="G:\\Studies\\stanford\\mtc\\"
setwd(path)

#Tells it to look for all .txt files in the path given above
filelist <- dir(path,pattern = ".txt")

#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 12))


k = 1

#For loop, for every file ending in .txt in that path, we will run through this loop of calculations once.  
for(f in 1:length(filelist)){
  
  #Declare some tables for data
  Read.Data <- data.frame()
  
  #This line reads the .txt file and places it into a table we can look at
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  Positive <- subset(Read.Data, Read.Data$Class == "Immune cells")
  DataDraft[k,1] <- filelist[f]
  DataDraft[k,2] <- sum(Positive$ROI.Shape..Area.�m.2)/1000000

  print(filelist[f])
  
  k = k + 1
}


colnames(DataDraft) <- c("Sample", "Negative Stain Area (mm^2)", "Positive Stain Area (mm^2)", "Positive Area from Detection (mm^2)")

#Writes a csv file with the data in the path
write.csv(DataDraft,paste("Pos Pix Det Data",f,".csv"))











