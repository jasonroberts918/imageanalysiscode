#Change path here, this is where your data is
path.det = "C://Analysis_Studies//Study//detection results"
path.ano = "C://Analysis_Studies//Study//annotation results"
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
  low <- data.frame()  
  
  #This line reads the .txt file and places it into a table we can look at
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  
  setwd(path.ano)
  filename <- gsub(" Detections", "", filelist[f])
  Read.Data.ano <- read.table(filename, header=T, sep="\t", fill = TRUE)
  setwd(path.det)
  #Basic calculations from the data, negatives are all the things that are given the class negative in the data etc, can be changed to be whatever
  negative <- subset(Read.Data, Read.Data$Class == "negative")
  low <- subset(Read.Data, Read.Data$Class == "low")
  medium <- subset(Read.Data, Read.Data$Class == "medium")
  high <- subset(Read.Data, Read.Data$Class == "high")
  
  #low_low_Intensity <- subset(low, low$ROI..2.00.µm.per.pixel..Green..Mean < 0.1)
  #low_Med_Intensity <- subset(low, low$ROI..2.00.µm.per.pixel..Green..Mean >= 0.1 & low$ROI..2.00.µm.per.pixel..Green..Mean <= 0.2)
  #low_high_Intensity <- subset(low, low$ROI..2.00.µm.per.pixel..Green..Mean > 0.2)
  
  negativeArea <- sum(negative$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  lowArea <- sum(low$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  mediumArea <- sum(medium$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  highArea <- sum(high$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  
  #if IF, use low$Cell..Green.mean
  #if HDAB, use low$Cell..DAB.OD.mean
  negative_MeanIntensity <- mean(negative$Nucleus..DAB.OD.mean)
  low_MeanIntensity <- mean(low$Nucleus..DAB.OD.mean)
  medium_MeanIntensity <- mean(medium$Nucleus..DAB.OD.mean)
  high_MeanIntensity <- mean(high$Nucleus..DAB.OD.mean)
  
  
  Tot.Cells <- nrow(low) + nrow(medium) + nrow(high)  + nrow(negative)
  realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "PathAnnotationObject")
  #realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "Annotation")
  # realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "Fat")
  anoArea <- sum(realAnnotations$Area.µm.2)/ 1000000 #division for conversion frum um^2 to mm^2
  
  #DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
  DataDraft[k,1] <- gsub(".mrxs.txt", "", filename)
  DataDraft[k,2] <- nrow(low) / anoArea
  DataDraft[k,3] <- nrow(low)
  DataDraft[k,4] <- nrow(low) / (Tot.Cells) 
  DataDraft[k,5] <- low_MeanIntensity
  DataDraft[k,6] <- lowArea
  DataDraft[k,7] <- nrow(medium) / anoArea
  DataDraft[k,8] <- nrow(medium)
  DataDraft[k,9] <- nrow(medium) / (Tot.Cells) 
  DataDraft[k,10] <- medium_MeanIntensity
  DataDraft[k,11] <- mediumArea
  DataDraft[k,12] <- nrow(high) / anoArea
  DataDraft[k,13] <- nrow(high)
  DataDraft[k,14] <- nrow(high) / (Tot.Cells) 
  DataDraft[k,15] <- high_MeanIntensity
  DataDraft[k,16] <- highArea
  DataDraft[k,17] <- nrow(negative) / anoArea
  DataDraft[k,18] <- nrow(negative)
  DataDraft[k,19] <- nrow(negative) / (Tot.Cells) 
  DataDraft[k,20] <- negative_MeanIntensity
  DataDraft[k,21] <- negativeArea
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
