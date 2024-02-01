library(openxlsx)
library(data.table)
library(stringr)

#Change path here, this is where your data is
path.det = "C://Analysis_Studies//Study//detection results"
path.ano = "C://Analysis_Studies//Study//annotation results"

setwd(path.det)

#Tells it to look for all .txt files in the path given above
#filelist_raw <- dir(path.det,pattern = ".txt") #Need this janky code because QP2 exports the detections files with "Detections" after the .mrxs extension...
#filelist_int <- strsplit(filelist_raw, " Detections")
#filelist <- unlist(filelist_int)[2*(1:length(filelist_raw))-1]
filelist <- dir(path.det,pattern = ".txt")


#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 12))

#Qupath colors (may not match native image colors)
QPRed = "PARP14" #QP Red
QPGreen = "CD3" #QP Green
QPYellow = "CD68" #QP Yellow

#QP string names
cell_name = "PathCellObject"
FITC_posName = "FITC"
Cy5_posName = "Cy5"
TRITC_posName = "TRITC"
double_positive = "FITC: Cy5"
double_positive_2 = "TRITC: Cy5"

#This is a counter, set it equal to 1 outside of the for loop, within the for loop we increase it (k = k + 1) 
#through each pass through the loop to have a counter for each row of data, so first .txt file goes in k = 1 row, second is k = k + 1 row etc..

k = 1

#For loop, for every file ending in .txt in that path, we will run through this loop of calculations once.  
for(f in 1:length(filelist)){
  
  #Declare some tables for data
  Read.Data <- data.frame()
  Negative <- data.frame()
  
  #This line reads the .txt file and places it into a table we can look at
  
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  setwd(path.ano)
  filename <- gsub(" Detections", "", filelist[f])
  Read.Data.ano <- read.table(filename, header=T, sep="\t", fill = TRUE)
  setwd(path.det)
  
  #Here we subset based off strings within the Name column
  QPred_only <- subset(Read.Data, Read.Data$Name == Cy5_posName)
  QPgreen_only <- subset(Read.Data, Read.Data$Name == FITC_posName)
  QPyellow_only <- subset(Read.Data, Read.Data$Name == TRITC_posName)
  QPboth <- subset(Read.Data, Read.Data$Name == double_positive)
  QPboth_2 <- subset(Read.Data, Read.Data$Name == double_positive_2)
  QPneg <- subset(Read.Data, Read.Data$Name == cell_name)
  
  #Basic calculations from the data, Negatives are all the things that are given the class Negative in the data etc, can be changed to be whatever
  
  NegativeArea <- sum(QPneg$Cell..Area) / 1000000
  posRedArea <- sum(QPred_only$Cell..Area) / 1000000
  posGreenArea <- sum(QPgreen_only$Cell..Area) / 1000000
  posYellowArea <- sum(QPyellow_only$Cell..Area) / 1000000
  posBothArea <- sum(QPboth$Cell..Area) / 1000000
  posBothArea_2 <- sum(QPboth_2$Cell..Area) / 1000000
  totalCellArea <- NegativeArea+posRedArea+posGreenArea+posYellowArea+posBothArea+posBothArea_2
  realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "Annotation" | Read.Data.ano$Name == "PathAnnotationObject")
  anoArea <- sum(realAnnotations$Area) / 1000000
  
  redIntensity <- mean(QPred_only$Cell..Opal.690.mean)
  greenIntensity<-mean(QPgreen_only$Cell..Opal.520.mean)
  yellowIntensity<-mean(QPyellow_only$Cell..Opal.570.mean)
  
  totalCells <- nrow(QPred_only) + nrow(QPgreen_only) + nrow(QPyellow_only) + nrow(QPboth) + nrow(QPboth_2) + nrow(QPneg)
  
  #This DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
  #so k,1, if k = 1, would go in the first row, first column etc...
  
  filename <- gsub(".txt", "", filelist[f])
  filename <- gsub(".mrxs", "", filelist[f])
  
  DataDraft[k,1] <- filename
  
  DataDraft[k,2] <- nrow(QPgreen_only) / anoArea
  DataDraft[k,3] <- nrow(QPgreen_only)
  DataDraft[k,4] <- posGreenArea
  DataDraft[k,5] <- nrow(QPgreen_only) / totalCells
  DataDraft[k,6] <- greenIntensity
  
  DataDraft[k,7] <- nrow(QPred_only) / anoArea
  DataDraft[k,8] <- nrow(QPred_only)
  DataDraft[k,9] <- posRedArea
  DataDraft[k,10] <- nrow(QPred_only) / totalCells
  DataDraft[k,11] <- redIntensity
  
  DataDraft[k,12] <- nrow(QPyellow_only) / anoArea
  DataDraft[k,13] <- nrow(QPyellow_only)
  DataDraft[k,14] <- posYellowArea
  DataDraft[k,15] <- nrow(QPyellow_only) / totalCells
  DataDraft[k,16] <- yellowIntensity
  
  
  DataDraft[k,17] <- nrow(QPboth) / anoArea
  DataDraft[k,18] <- nrow(QPboth)
  DataDraft[k,19] <- posBothArea 
  DataDraft[k,20] <- nrow(QPboth) / totalCells
  
  DataDraft[k,21] <- nrow(QPboth_2) / anoArea
  DataDraft[k,22] <- nrow(QPboth_2)
  DataDraft[k,23] <- posBothArea_2
  DataDraft[k,24] <- nrow(QPboth_2) / totalCells
  
  DataDraft[k,25] <- totalCells
  DataDraft[k,26] <- totalCellArea
  DataDraft[k,27] <- anoArea
  
  print(filelist[f])
  
  #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
  k = k + 1
}
Marker1 <- QPGreen
Marker2 <- QPRed
Marker3 <- QPYellow
colnames(DataDraft) <- c("Sample", 
                         "Marker1 + / Marker2 - Cell Density (cells/mm^2)",
                         "Marker1 + / Marker2 - Cell Count",
                         "Marker1 + / Marker2 - Cell Area (mm^2)",
                         "Marker1 + / Marker2 - Cell Percentage", 
                         "Marker1 + / Marker2 - Intensity",

                         "Marker1 - / Marker2 + Cell Density (cells/mm^2)",
                         "Marker1 - / Marker2 + Cell Count",
                         "Marker1 - / Marker2 + Cell Area (mm^2)",
                         "Marker1 - / Marker2 + Cell Percentage", 
                         "Marker1 - / Marker2 + Intensity",

                         "Marker3 + / Marker2 - Cell Density (cells/mm^2)",
                         "Marker3 + / Marker2 - Cell Count",
                         "Marker3 + / Marker2 - Cell Area (mm^2)",
                         "Marker3 + / Marker2 - Cell Percentage", 
                         "Marker3 + / Marker2 - Intensity",

                         "Marker1 + / Marker2 + Cell Density (cells/mm^2)",
                         "Marker1 + / Marker2 + Cell Count",
                         "Marker1 + / Marker2 + Cell Area (mm^2)",
                         "Marker1 + / Marker2 + Cell Percentage", 

                         "Marker3 + / Marker2 + Cell Density (cells/mm^2)",
                         "Marker3 + / Marker2 + Cell Count",
                         "Marker3 + / Marker2 + Cell Area (mm^2)",
                         "Marker3 + / Marker2 + Cell Percentage", 

                         "Total Cell Count",
                         "Total Cell Area (mm^2)",
                         "Total Annotation Area (mm^2)")



#Writes a csv file with the data in the path
write.csv(DataDraft,paste("IF Data",f,".csv"), row.names = F)
write.xlsx(DataDraft, paste("IF Data Excel",f,".xlsx")) #excel files make for easier formatting

print(paste("DONE! csv written to", getwd())) 
