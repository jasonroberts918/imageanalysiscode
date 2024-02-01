
#Change path here, this is where your data is
path.det = "C:\\Analysis_Studies\\Study\\detection results"
path.ano = "C:\\Analysis_Studies\\Study\\annotation results"
setwd(path.det)

#Tells it to look for all .txt files in the path given above
filelist <- dir(path.det, pattern = ".txt")

#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 6))

#This is a counter, set it equal to 1 outside of the for loop, within the for loop we increase it (k = k + 1) 
#through each pass through the loop to have a counter for each row of data, so first .txt file goes in k = 1 row, second is k = k + 1 row etc..

k = 1

#For loop, for every file ending in .txt in that path, we will run through this loop of calculations once.  
for(f in 1:length(filelist)){
  
  #Declare some tables for data
  Read.Data <- data.frame()
  Positive <- data.frame()  
  
  #This line reads the .txt file and places it into a table we can look at
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  
  setwd(path.ano)
  filename <- gsub(" Detections", "", filelist[f])
  Read.Data.ano <- read.table(filename, header=T, sep="\t", fill = TRUE)
  setwd(path.det)
  #Basic calculations from the data, Negatives are all the things that are given the class Negative in the data etc, can be changed to be whatever
  
  Negative <- subset(Read.Data, Read.Data$Class == "Negative")
  Positive <- subset(Read.Data, Read.Data$Class == "Positive")
  
  PositiveArea <- sum(Positive$Area.µm.2) / 1000000
  NegativeArea <- sum(Negative$Area.µm.2) / 1000000
  totalTissueArea <- PositiveArea + NegativeArea 
  
  
  realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "PathAnnotationObject")
  anoArea <- sum(realAnnotations$Area.µm.2)
  #This DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
  #so k,1, if k = 1, would go in the first row, first column etc...
  
  DataDraft[k,1] <- gsub(".mrxs.txt", "", filename)
  DataDraft[k,2] <- PositiveArea / totalTissueArea * 100
  DataDraft[k,3] <- PositiveArea
  DataDraft[k,4] <- NegativeArea
  DataDraft[k,5] <- totalTissueArea
  DataDraft[k,6] <- mean(Positive$ROI..1.00.µm.per.pixel..DAB..Mean) #may need to update column name that's selected here
  
  print(filelist[f])
  
  #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
  k = k + 1
}

colnames(DataDraft) <- c("Sample",
                         "Positive Percent",
                         "Positive Area (mm^2)",
                         "Negative Area (mm^2)", 
                         "Total Tissue Area Analyzed",
                         "Mean Positive Area DAB Intensity")

#Writes a csv file with the data in the path
write.csv(DataDraft,paste("Data",f,".csv"))









