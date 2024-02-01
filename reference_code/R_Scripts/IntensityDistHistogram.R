#Change path here, this is where your data is
path.det = "C://Analysis_Studies//Study//detections"
path.ano = "C://Analysis_Studies//Study//annotations"
path.hist = "C://Analysis_Studies//Study//histo"
setwd(path.det)

#Tells it to look for all .txt files in the path given above
filelist <- dir(path.det,pattern = ".txt")

#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 23))

#This is a counter, set it equal to 1 outside of the for loop, within the for loop we increase it (k = k + 1) 
#through each pass through the loop to have a counter for each row of data, so first .txt file goes in k = 1 row, second is k = k + 1 row etc..
k = 1

#For loop, for every file ending in .txt in that path, we will run through this loop of calculations once.  
for(f in 1:length(filelist)){
  
  #Declare some tables for data
  Read.Data <- data.frame()
  Low <- data.frame()  
  
  #This line reads the .txt file and places it into a table we can look at
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  
  setwd(path.ano)
  filename <- gsub(" Detections", "", filelist[f])
  Read.Data.ano <- read.table(filename, header=T, sep="\t", fill = TRUE)
  setwd(path.det)
  
  #Read.Data[is.na(Read.Data)] <- 0
  #Read.Data.ano[is.na(Read.Data.ano)] <- 0
  #Basic calculations from the data, Negatives are all the things that are given the class Negative in the data etc, can be changed to be whatever
  Negative <- subset(Read.Data, Read.Data$Class == "negative")
  Low <- subset(Read.Data, Read.Data$Class == "low")
  Medium <- subset(Read.Data, Read.Data$Class == "medium")
  High <- subset(Read.Data, Read.Data$Class == "high")
  
  
  Positive <- subset(Read.Data, Read.Data$Class == "negative" | Read.Data$Class == "low" | Read.Data$Class == "medium" | Read.Data$Class == "high")
  
  #histogram
  filename_histo <- gsub(".mrxs Detections.txt", "", filelist[f])
  setwd(path.hist)
  jpeg(file = paste(filename_histo, "Intensity.jpg"))
  hist(Positive$DAB..Cell..Mean, main = paste(filename_histo, ": Intensity"), xlab = "Cell Intensity Mean", xlim = c(0, 1.5), ylim = c(0, 150))
  dev.off()
  setwd(path.det)
  
  #Low_Low_Intensity <- subset(Low, Low$ROI..2.00.Âµm.per.pixel..Green..Mean < 0.1)
  #Low_Med_Intensity <- subset(Low, Low$ROI..2.00.Âµm.per.pixel..Green..Mean >= 0.1 & Low$ROI..2.00.Âµm.per.pixel..Green..Mean <= 0.2)
  #Low_High_Intensity <- subset(Low, Low$ROI..2.00.Âµm.per.pixel..Green..Mean > 0.2)
  
  NegativeArea <- sum(Negative$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  LowArea <- sum(Low$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  MediumArea <- sum(Medium$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  HighArea <- sum(High$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  
  #if IF, use Low$Cell..Green.mean
  #if HDAB, use Low$Cell..DAB.OD.mean
  Negative_MeanIntensity <- mean(Negative$DAB..Nucleus..Mean)
  Low_MeanIntensity <- mean(Low$DAB..Nucleus..Mean)
  Medium_MeanIntensity <- mean(Medium$DAB..Nucleus..Mean)
  High_MeanIntensity <- mean(High$DAB..Nucleus..Mean)
  
  
  Tot.Cells <- nrow(Low) + nrow(Medium) + nrow(High)  + nrow(Negative)
  #realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "PathAnnotationObject")
  #realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "Annotation")
  realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "DRG")
  anoArea <- sum(realAnnotations$Area.Âµm.2)/ 1000000 #division for conversion frum um^2 to mm^2
  
  #DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
  DataDraft[k,1] <- gsub(".mrxs.txt", "", filename)
  DataDraft[k,2] <- nrow(Low) / anoArea
  DataDraft[k,3] <- nrow(Low)
  DataDraft[k,4] <- nrow(Low) / (Tot.Cells) 
  DataDraft[k,5] <- Low_MeanIntensity
  DataDraft[k,6] <- LowArea
  DataDraft[k,7] <- nrow(Medium) / anoArea
  DataDraft[k,8] <- nrow(Medium)
  DataDraft[k,9] <- nrow(Medium) / (Tot.Cells) 
  DataDraft[k,10] <- Medium_MeanIntensity
  DataDraft[k,11] <- MediumArea
  DataDraft[k,12] <- nrow(High) / anoArea
  DataDraft[k,13] <- nrow(High)
  DataDraft[k,14] <- nrow(High) / (Tot.Cells) 
  DataDraft[k,15] <- High_MeanIntensity
  DataDraft[k,16] <- HighArea
  DataDraft[k,17] <- nrow(Negative) / anoArea
  DataDraft[k,18] <- nrow(Negative)
  DataDraft[k,19] <- nrow(Negative) / (Tot.Cells) 
  DataDraft[k,20] <- Negative_MeanIntensity
  DataDraft[k,21] <- NegativeArea
  DataDraft[k,22] <- anoArea
  DataDraft[k,23] <- (Tot.Cells)
  
  print(filelist[f])
  
  #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
  k = k + 1
}

colnames(DataDraft) <- c("Filename", 
                         "Low - Cell Density (cells/mm^2)",
                         "Low - Cell Count", 
                         "Low - Cell %",
                         "Low - Nucleus Intensity",
                         "Low - Cell Area (mm^2)",
                         "Med - Cell Density (cells/mm^2)",
                         "Med - Cell Count", 
                         "Med - Cell %",
                         "Med - Nucleus Intensity",
                         "Med - Cell Area (mm^2)",
                         "High - Cell Density (cells/mm^2)",
                         "High - Cell Count", 
                         "High - Cell %",
                         "High - Nucleus Intensity",
                         "High - Cell Area (mm^2)",
                         "Negative - Cell Density (cells/mm^2)",
                         "Negative - Cell Count", 
                         "Negative - Cell %",
                         "Negative - Nucleus Intensity",
                         "Negative - Cell Area (mm^2)", 
                         "Annotation Area (mm^2)",
                         "Total Cell Count")

#Writes a csv file with the data in the path
write.csv(DataDraft,paste("Data",f,".csv"))
