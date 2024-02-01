library(openxlsx)
library(data.table)
library(stringr)
#Change path here, this is where your data is
path.det = "C:\\Analysis_Studies\\Study\\detection results\\"
path.ano =  "C:\\Analysis_Studies\\Study\\annotation results\\"

setwd(path.det)

#Tells it to look for all .txt files in the path given above
filelist_raw <- dir(path.det,pattern = ".txt") #Need this code because QP2 exports the detections files with "Detections" after the .mrxs extension...
filelist_int <- strsplit(filelist_raw, " Detections")
filelist <- unlist(filelist_int)[2*(1:length(filelist_raw))-1]
#Makes the final summary table with 20 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 20))

#Qupath colors (may not match native image colors)
QPRed = "CD59" #QP Red
QPYellow = "MBL" #QP Yellow

#QP string names
cell_name = "Red Negative: Yellow Negative"
Opal690_posName = "Red Positive: Yellow Negative"
Opal570_posName = "Red Negative: Yellow Positive"
#This is a counter, set it equal to 1 outside of the for loop, within the for loop we increase it (k = k + 1) 
#through each pass through the loop to have a counter for each row of data, so first .txt file goes in k = 1 row, second is k = k + 1 row etc..

k = 1

#For loop, for every file ending in .txt in that path, we will run through this loop of calculations once.  
for(f in 1:length(filelist)){
  
  #Declare some tables for data
  Read.Data <- data.frame()
  Negative <- data.frame()
  
  #This line reads the .txt file and places it into a table we can look at
  setwd(path.ano)
  Read.Data.ano <- read.table(paste(filelist[f], ".txt", sep=""), header=T, sep="\t", fill = TRUE) #janky code continued
  setwd(path.det)
  Read.Data <- read.table(filelist_raw[f], header=T, sep="\t", fill = TRUE)
  
  #QP2 has multiple classes separated by ": "
  #Here we subset based off substrings within the Name column
  #cells <- subset(Read.Data, grepl(cell_name, Read.Data$Class, fixed=TRUE))
  
  QPred_only <- subset(Read.Data, Read.Data$Class == "Red Positive: Yellow Negative")
  QPyellow_only <- subset(Read.Data, Read.Data$Class == "Red Negative: Yellow Positive")
  QPboth <- subset(Read.Data, Read.Data$Class == "Red Positive: Yellow Positive")
  QPneg <- subset(Read.Data, Read.Data$Class == "Red Negative: Yellow Negative")
  
  #Basic calculations from the data, Negatives are all the things that are given the class Negative in the data etc, can be changed to be whatever
  
  NegativeArea <- sum(QPneg$Cell..Area) / 1000000
  posRedArea <- sum(QPred_only$Cell..Area) / 1000000
  posYellowArea <- sum(QPyellow_only$Cell..Area) / 1000000
  posBothArea <- sum(QPboth$Cell..Area) / 1000000
  totalCellArea <- NegativeArea+posRedArea+posYellowArea+posBothArea
  realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "Annotation" | Read.Data.ano$Name == "PathAnnotationObject")
  anoArea <- sum(realAnnotations$Area) / 1000000
  
  redIntensity <- mean(QPred_only$Opal.690..Cell..Mean)
  yellowIntensity<-mean(QPyellow_only$Opal.570..Cell..Mean)
  
  totalCells <- nrow(QPred_only) + nrow(QPyellow_only) + nrow(QPboth) + nrow(QPneg)
  
  #This DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
  #so k,1, if k = 1, would go in the first row, first column etc...
  
  filename <- gsub(".txt", "", filelist[f])
  filename <- gsub(".mrxs", "", filelist[f])
  
  DataDraft[k,1] <- filename
  
  DataDraft[k,2] <- nrow(QPred_only) / totalCellArea
  DataDraft[k,3] <- nrow(QPred_only)
  DataDraft[k,4] <- posRedArea
  DataDraft[k,5] <- nrow(QPred_only) / totalCells
  DataDraft[k,6] <- redIntensity
  
  DataDraft[k,7] <- nrow(QPyellow_only) / totalCellArea
  DataDraft[k,8] <- nrow(QPyellow_only)
  DataDraft[k,9] <- posYellowArea
  DataDraft[k,10] <- nrow(QPyellow_only) / totalCells
  DataDraft[k,11] <- yellowIntensity
  
  DataDraft[k,12] <- nrow(QPboth) / totalCellArea
  DataDraft[k,13] <- nrow(QPboth)
  DataDraft[k,14] <- posBothArea
  DataDraft[k,15] <- nrow(QPboth) / totalCells
  
  DataDraft[k,16] <- nrow(QPneg)
  DataDraft[k,17] <- NegativeArea
  DataDraft[k,18] <- totalCells
  DataDraft[k,19] <- totalCellArea
  DataDraft[k,20] <- anoArea
  
  print(filelist[f])
  
  #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
  k = k + 1
}
Marker1 <- QPRed
Marker2 <- QPYellow
colnames(DataDraft) <- c("Sample", 
                         
                         paste(Marker1,'+/', Marker2,'-'," Cell Density (cells/mm^2)", sep=''),
                         paste(Marker1,'+/', Marker2,'-'," Cell Count", sep=''),
                         paste(Marker1,'+/', Marker2,'-'," Cell Area (mm^2)", sep=''),
                         paste(Marker1,'+/', Marker2,'-'," Cell Percentage", sep=''), 
                         paste(Marker1,'+/', Marker2,'-'," Intensity",sep=''),
                         
                         paste(Marker1,'-/', Marker2,'+'," Cell Density (cells/mm^2)", sep=''),
                         paste(Marker1,'-/', Marker2,'+'," Cell Count", sep=''), 
                         paste(Marker1,'-/', Marker2,'+'," Cell Area (mm^2)", sep=''),
                         paste(Marker1,'-/', Marker2,'+'," Cell Percentage", sep=''), 
                         paste(Marker1,'-/', Marker2,'+'," Intensity",sep=''),
                         
                         paste(Marker1,'+/', Marker2,'+'," Cell Density (cells/mm^2)", sep=''),
                         paste(Marker1,'+/', Marker2,'+'," Cell Count", sep=''), 
                         paste(Marker1,'+/', Marker2,'+'," Cell Area (mm^2)", sep=''),
                         paste(Marker1,'+/', Marker2,'+'," Cell Percentage", sep=''), 
                         
                         "Negative Cell Count", 
                         "Negative Cell Area (mm^2)",
                         "Total Cell Count", 
                         "Total Cell Area (mm^2)",
                         "Total Annotation Area (mm^2)")


#Writes a csv file with the data in the path
write.csv(DataDraft,paste("22-1124 Univ of Utah Data",f,".csv"), row.names = F)
write.xlsx(DataDraft, paste("22-1124 Univ of Utah Data Excel",f,".xlsx"))









