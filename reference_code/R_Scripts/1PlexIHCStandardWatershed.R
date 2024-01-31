
##Change path here, this is where your data is
path.det = "C://Analysis_Studies//Study//detection results"
path.ano = "C://Analysis_Studies//Study//annotation results"
setwd(path.det)

#Tells it to look for all .txt files in the path given above
filelist <- dir(path.det,pattern = ".txt")

#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 10))

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
  
  NegativeArea <- sum(Negative$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  PositiveArea <- sum(Positive$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  
  #Set channel to record intensity here
  #if IF, use Positive$Cell..Green.mean
  #if HDAB, use Positive$Cell..DAB.OD.mean
  Intensity <- mean(Positive$Cell..DAB.OD.mean)
  Tot.Cells <- nrow(Positive) + nrow(Negative)
  realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "PathAnnotationObject")
  anoArea <- sum(realAnnotations$Area.Âµm.2)/ 1000000 #division for conversion frum um^2 to mm^2
  
  #DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
  DataDraft[k,1] <- gsub(".mrxs.txt", "", filename)
  DataDraft[k,2] <- nrow(Positive) / anoArea
  DataDraft[k,3] <- nrow(Positive)
  DataDraft[k,4] <- nrow(Positive) / (nrow(Positive) + nrow(Negative))
  DataDraft[k,5] <- Intensity
  DataDraft[k,6] <- PositiveArea
  DataDraft[k,7] <- nrow(Negative)
  DataDraft[k,8] <- NegativeArea
  DataDraft[k,9] <- anoArea
  DataDraft[k,10] <- nrow(Positive) + nrow(Negative)
  
  print(filelist[f])
  
  #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
  k = k + 1
}

colnames(DataDraft) <- c("Filename", 
                         "Positive Cell Density (cells/mm^2)",
                         "Positive Cell Count", 
                         "Positive Cell %",
                         "Positive Cell Intensity",
                         "Positive Cell Area (mm^2)",
                         "Negative Cell Count", 
                         "Negative Cell Area (mm^2)", 
                         "Tissue Area Analyzed (mm^2)",
                         "Total Cell Count")

#Writes a csv file with the data in the path
write.csv(DataDraft,paste("22-751 P62 Data",f,".csv"))







