library(openxlsx)
library(data.table)
library(stringr)
#Change path here, this is where your data is
path.det = "C:\\Analysis_Studies\\Alentis POC QP\\detection results"
path.ano = "C:\\Analysis_Studies\\Alentis POC QP\\annotation results"

setwd(path.det)

#Tells it to look for all .txt files in the path given above
filelist_raw <- dir(path.det,pattern = ".txt") #Need this janky code because QP2 exports the detections files with "Detections" after the .mrxs extension...
filelist_int <- strsplit(filelist_raw, " Detections")
filelist <- unlist(filelist_int)[2*(1:length(filelist_raw))-1]

#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 69))

#QP string names
#cell_name = "FITC neg: TRITC Neg: Cy5 Neg: Cy7 Neg"
#FITC_posName = "FITC pos: TRITC Neg: Cy5 Neg: Cy7 Neg"
#TRITC_posName = "FITC neg: TRITC Pos: Cy5 Neg: Cy7 Neg"
#Cy5_posName = "FITC neg: TRITC Neg: Cy5 Pos: Cy7 Neg"
#Cy7_posName = "FITC neg: TRITC Neg: Cy5 Neg: Cy7 Pos"

FITC_posName = "FITC Pos"
TRITC_posName = "TRITC Pos"
Cy5_posName = "Cy5 Pos"
Cy7_posName = "Cy7 Pos"

markerF = "CD8" #FITC
markerT = "PD-1" #TRITC
markerC = "PDL1" #Cy5
markerD = "CD68" #cy7

onlyF = paste(markerF,'+/ ', markerT, '-/ ', markerC, '-/ ', markerD,'-', sep='')
onlyT = paste(markerF, '-/ ', markerT, '+/ ', markerC, '-/ ', markerD,'-', sep='')
onlyC = paste(markerF, '-/ ', markerT, '-/ ', markerC, '+/ ', markerD,'-', sep='')
onlyD = paste(markerF, '-/ ', markerT, '-/ ', markerC, '-/ ', markerD,'+', sep='')

colocFT = paste(markerF,'+/ ', markerT, '+/ ', markerC, '-/ ', markerD,'-', sep='')
colocFC = paste(markerF,'+/ ', markerT, '-/ ', markerC, '+/ ', markerD,'-', sep='')
colocFD = paste(markerF,'+/ ', markerT, '-/ ', markerC, '-/ ', markerD,'+', sep='')
colocTC = paste(markerF,'-/ ', markerT, '+/ ', markerC, '+/ ', markerD,'-', sep='')
colocTD = paste(markerF,'-/ ', markerT, '+/ ', markerC, '-/ ', markerD,'+', sep='')
colocCD = paste(markerF,'-/ ', markerT, '-/ ', markerC, '+/ ', markerD,'+', sep='')


colocFTC = paste(markerF,'+/ ', markerT, '+/ ', markerC, '+/ ', markerD,'-', sep='')
colocFTD = paste(markerF,'+/ ', markerT, '+/ ', markerC, '-/ ', markerD,'+', sep='')
colocFCD = paste(markerF,'+/ ', markerT, '-/ ', markerC, '+/ ', markerD,'+', sep='')
colocTCD = paste(markerF,'-/ ', markerT, '+/ ', markerC, '+/ ', markerD,'+', sep='')

colocFTCD = paste(markerF,'+/ ', markerT, '+/ ', markerC, '+/ ', markerD,'+', sep='')


#This is a counter, set it equal to 1 outside of the for loop, within the for loop we increase it (k = k + 1) 
#through each pass through the loop to have a counter for each row of data, so first .txt file goes in k = 1 row, second is k = k + 1 row etc..

k = 1

#For loop, for every file ending in .txt in that path, we will run through this loop of calculations once.  
for(f in 1:length(filelist)){
  
  #Declare some tables for data
  Read.Data <- data.frame()
  cells <- data.frame()
  
  #This line reads the .txt file and places it into a table we can look at
  setwd(path.ano)
  Read.Data.ano <- read.table(paste(filelist[f], ".txt", sep=""), header=T, sep="\t", fill = TRUE) #janky code continued
  setwd(path.det)
  Read.Data <- read.table(filelist_raw[f], header=T, sep="\t", fill = TRUE)
  
  for(regionName in unique(Read.Data$Parent)){
    print(regionName)
    cells <- subset(Read.Data, Read.Data$Parent == regionName)
  
    FITC_only <- subset(cells, grepl(FITC_posName, cells$Class, fixed=TRUE) &  !grepl(TRITC_posName, cells$Class, fixed=TRUE) & !grepl(Cy5_posName, cells$Class, fixed=TRUE) & !grepl(Cy7_posName, cells$Class, fixed=TRUE))
    TRITC_only <- subset(cells, !grepl(FITC_posName, cells$Class, fixed=TRUE) &  grepl(TRITC_posName, cells$Class, fixed=TRUE) & !grepl(Cy5_posName, cells$Class, fixed=TRUE) & !grepl(Cy7_posName, cells$Class, fixed=TRUE))
    Cy5_only <- subset(cells, !grepl(FITC_posName, cells$Class, fixed=TRUE) &  !grepl(TRITC_posName, cells$Class, fixed=TRUE) & grepl(Cy5_posName, cells$Class, fixed=TRUE) & !grepl(Cy7_posName, cells$Class, fixed=TRUE))
    Cy7_only <- subset(cells, !grepl(FITC_posName, cells$Class, fixed=TRUE) &  !grepl(TRITC_posName, cells$Class, fixed=TRUE) & !grepl(Cy5_posName, cells$Class, fixed=TRUE) & grepl(Cy7_posName, cells$Class, fixed=TRUE))
  
  
    FITC_TRITC <- subset(cells, grepl(FITC_posName, cells$Class, fixed=TRUE) &  grepl(TRITC_posName, cells$Class, fixed=TRUE) & !grepl(Cy5_posName, cells$Class, fixed=TRUE) & !grepl(Cy7_posName, cells$Class, fixed=TRUE))
    FITC_Cy5 <- subset(cells, grepl(FITC_posName, cells$Class, fixed=TRUE) &  !grepl(TRITC_posName, cells$Class, fixed=TRUE) & grepl(Cy5_posName, cells$Class, fixed=TRUE) & !grepl(Cy7_posName, cells$Class, fixed=TRUE))
    TRITC_Cy5 <- subset(cells, !grepl(FITC_posName, cells$Class, fixed=TRUE) &  grepl(TRITC_posName, cells$Class, fixed=TRUE) & grepl(Cy5_posName, cells$Class, fixed=TRUE) & !grepl(Cy7_posName, cells$Class, fixed=TRUE))
    FITC_Cy7 <- subset(cells, grepl(FITC_posName, cells$Class, fixed=TRUE) &  !grepl(TRITC_posName, cells$Class, fixed=TRUE) & !grepl(Cy5_posName, cells$Class, fixed=TRUE) & grepl(Cy7_posName, cells$Class, fixed=TRUE))
    TRITC_Cy7 <- subset(cells, !grepl(FITC_posName, cells$Class, fixed=TRUE) &  grepl(TRITC_posName, cells$Class, fixed=TRUE) & !grepl(Cy5_posName, cells$Class, fixed=TRUE) & grepl(Cy7_posName, cells$Class, fixed=TRUE))
    Cy5_Cy7 <- subset(cells, !grepl(FITC_posName, cells$Class, fixed=TRUE) &  !grepl(TRITC_posName, cells$Class, fixed=TRUE) & grepl(Cy5_posName, cells$Class, fixed=TRUE) & grepl(Cy7_posName, cells$Class, fixed=TRUE))
  
  
    FITC_TRITC_Cy5 <- subset(cells, grepl(FITC_posName, cells$Class, fixed=TRUE) &  grepl(TRITC_posName, cells$Class, fixed=TRUE) & grepl(Cy5_posName, cells$Class, fixed=TRUE) & !grepl(Cy7_posName, cells$Class, fixed=TRUE))
    FITC_TRITC_Cy7 <- subset(cells, grepl(FITC_posName, cells$Class, fixed=TRUE) &  grepl(TRITC_posName, cells$Class, fixed=TRUE) & !grepl(Cy5_posName, cells$Class, fixed=TRUE) & grepl(Cy7_posName, cells$Class, fixed=TRUE))
    FITC_Cy5_Cy7 <- subset(cells, grepl(FITC_posName, cells$Class, fixed=TRUE) &  !grepl(TRITC_posName, cells$Class, fixed=TRUE) & grepl(Cy5_posName, cells$Class, fixed=TRUE) & grepl(Cy7_posName, cells$Class, fixed=TRUE))
    TRITC_Cy5_Cy7 <- subset(cells, !grepl(FITC_posName, cells$Class, fixed=TRUE) &  grepl(TRITC_posName, cells$Class, fixed=TRUE) & grepl(Cy5_posName, cells$Class, fixed=TRUE) & grepl(Cy7_posName, cells$Class, fixed=TRUE))
  
    FITC_TRITC_Cy5_Cy7 <- subset(cells, grepl(FITC_posName, cells$Class, fixed=TRUE) &  grepl(TRITC_posName, cells$Class, fixed=TRUE) & grepl(Cy5_posName, cells$Class, fixed=TRUE) & grepl(Cy7_posName, cells$Class, fixed=TRUE))
  
    Negative <- subset(cells, !grepl(FITC_posName, cells$Class, fixed=TRUE) &  !grepl(TRITC_posName, cells$Class, fixed=TRUE) & !grepl(Cy5_posName, cells$Class, fixed=TRUE) & !grepl(Cy7_posName, cells$Class, fixed=TRUE))
  
    totCellCount <- sum(nrow(Negative), nrow(FITC_only), nrow(TRITC_only), nrow(Cy5_only), nrow(Cy7_only), nrow(FITC_TRITC), nrow(FITC_Cy5), nrow(TRITC_Cy5), nrow(FITC_Cy7), nrow(TRITC_Cy7), nrow(Cy5_Cy7), nrow(FITC_TRITC_Cy5), nrow(FITC_TRITC_Cy7), nrow(FITC_Cy5_Cy7), nrow(TRITC_Cy5_Cy7), nrow(FITC_TRITC_Cy5_Cy7))
  
    totCellArea <- sum(sum(FITC_only$Cell..Area), 
                     sum(TRITC_only$Cell..Area), 
                     sum(Cy5_only$Cell..Area), 
                     sum(Cy7_only$Cell..Area),
                     sum(FITC_TRITC$Cell..Area), 
                     sum(FITC_Cy5$Cell..Area), 
                     sum(FITC_Cy7$Cell..Area), 
                     sum(TRITC_Cy5$Cell..Area),
                     sum(TRITC_Cy7$Cell..Area), 
                     sum(Cy5_Cy7$Cell..Area), 
                     sum(FITC_TRITC_Cy5$Cell..Area),
                     sum(FITC_TRITC_Cy7$Cell..Area),
                     sum(FITC_Cy5_Cy7$Cell..Area),
                     sum(TRITC_Cy5_Cy7$Cell..Area),
                     sum(FITC_TRITC_Cy5_Cy7$Cell..Area),
                     sum(Negative$Cell..Area)) / (1000000) #converting from um^2 to mm^2 
  
    tissueRegion <- subset(Read.Data.ano, Read.Data.ano$Name == regionName)
    regionArea <- sum(tissueRegion$Area.µm.2)  / (1000000) #converting from px^2 to mm^2 (px == 0.2431um)
    
  
    #This DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
    #so k,1, if k = 1, would go in the first row, first column etc...
  
    #manually fixing file names
    filename <- str_split(filelist[f], ".ome.tiff")[[1]][1]
    #filename <- str_split(filename, "-SMA ")[[1]][2]
  
    DataDraft[k,1] <- filename
    DataDraft[k,2] <- regionName
  
    DataDraft[k,3] <- nrow(FITC_only) / totCellArea
    DataDraft[k,4] <- nrow(FITC_only)
    DataDraft[k,5] <- sum(FITC_only$Cell..Area) / 1000000
    DataDraft[k,6] <- nrow(FITC_only) / totCellCount
    DataDraft[k,7] <- mean(FITC_only$FITC..Cell..Mean)
  
    DataDraft[k,8] <- nrow(TRITC_only) / totCellArea
    DataDraft[k,9] <- nrow(TRITC_only)
    DataDraft[k,10] <- sum(TRITC_only$Cell..Area)/ 1000000
    DataDraft[k,11] <- nrow(TRITC_only) / totCellCount
    DataDraft[k,12] <- mean(TRITC_only$TRITC..Cell..Mean)
  
    DataDraft[k,13] <- nrow(Cy5_only) / totCellArea
    DataDraft[k,14] <- nrow(Cy5_only)
    DataDraft[k,15] <- sum(Cy5_only$Cell..Area)/ 1000000
    DataDraft[k,16] <- nrow(Cy5_only) / totCellCount
    DataDraft[k,17] <- mean(Cy5_only$Cy5..Cell..Mean)

    DataDraft[k,18] <- nrow(Cy7_only) / totCellArea
    DataDraft[k,19] <- nrow(Cy7_only)
    DataDraft[k,20] <- sum(Cy7_only$Cell..Area)/ 1000000
    DataDraft[k,21] <- nrow(Cy7_only) / totCellCount
    DataDraft[k,22] <- mean(Cy7_only$Cy7..Cell..Mean)
  
    DataDraft[k,23] <- nrow(FITC_TRITC) / totCellArea
    DataDraft[k,24] <- nrow(FITC_TRITC)
    DataDraft[k,25] <- sum(FITC_TRITC$Cell..Area)/ 1000000
    DataDraft[k,26] <- nrow(FITC_TRITC) / totCellCount

    DataDraft[k,27] <- nrow(FITC_Cy5) / totCellArea
    DataDraft[k,28] <- nrow(FITC_Cy5)
    DataDraft[k,29] <- sum(FITC_Cy5$Cell..Area)/ 1000000
    DataDraft[k,30] <- nrow(FITC_Cy5) / totCellCount
  
    DataDraft[k,31] <- nrow(FITC_Cy7) / totCellArea
    DataDraft[k,32] <- nrow(FITC_Cy7)
    DataDraft[k,33] <- sum(FITC_Cy7$Cell..Area)/ 1000000
    DataDraft[k,34] <- nrow(FITC_Cy7) / totCellCount
  
    DataDraft[k,35] <- nrow(TRITC_Cy5) / totCellArea
    DataDraft[k,36] <- nrow(TRITC_Cy5)
    DataDraft[k,37] <- sum(TRITC_Cy5$Cell..Area)/ 1000000
    DataDraft[k,38] <- nrow(TRITC_Cy5) / totCellCount
  
    DataDraft[k,39] <- nrow(TRITC_Cy7) / totCellArea
    DataDraft[k,40] <- nrow(TRITC_Cy7)
    DataDraft[k,41] <- sum(TRITC_Cy7$Cell..Area)/ 1000000
    DataDraft[k,42] <- nrow(TRITC_Cy7) / totCellCount
  
    DataDraft[k,43] <- nrow(Cy5_Cy7) / totCellArea
    DataDraft[k,44] <- nrow(Cy5_Cy7)
    DataDraft[k,45] <- sum(Cy5_Cy7$Cell..Area)/ 1000000
    DataDraft[k,46] <- nrow(Cy5_Cy7) / totCellCount
  
    DataDraft[k,47] <- nrow(FITC_TRITC_Cy5) / totCellArea
    DataDraft[k,48] <- nrow(FITC_TRITC_Cy5)
    DataDraft[k,49] <- sum(FITC_TRITC_Cy5$Cell..Area)/ 1000000
    DataDraft[k,50] <- nrow(FITC_TRITC_Cy5) / totCellCount
  
    DataDraft[k,51] <- nrow(FITC_TRITC_Cy7) / totCellArea
    DataDraft[k,52] <- nrow(FITC_TRITC_Cy7)
    DataDraft[k,53] <- sum(FITC_TRITC_Cy7$Cell..Area)/ 1000000
    DataDraft[k,54] <- nrow(FITC_TRITC_Cy7) / totCellCount
  
    DataDraft[k,55] <- nrow(FITC_Cy5_Cy7) / totCellArea
    DataDraft[k,56] <- nrow(FITC_Cy5_Cy7)
    DataDraft[k,57] <- sum(FITC_Cy5_Cy7$Cell..Area)/ 1000000
    DataDraft[k,58] <- nrow(FITC_Cy5_Cy7) / totCellCount

    DataDraft[k,59] <- nrow(TRITC_Cy5_Cy7) / totCellArea
    DataDraft[k,60] <- nrow(TRITC_Cy5_Cy7)
    DataDraft[k,61] <- sum(TRITC_Cy5_Cy7$Cell..Area)/ 1000000
    DataDraft[k,62] <- nrow(TRITC_Cy5_Cy7) / totCellCount
  
    DataDraft[k,63] <- nrow(FITC_TRITC_Cy5_Cy7) / totCellArea
    DataDraft[k,64] <- nrow(FITC_TRITC_Cy5_Cy7)
    DataDraft[k,65] <- sum(FITC_TRITC_Cy5_Cy7$Cell..Area)/ 1000000
    DataDraft[k,66] <- nrow(FITC_TRITC_Cy5_Cy7) / totCellCount
  
    DataDraft[k,67] <- totCellCount
    DataDraft[k,68] <- totCellArea
    DataDraft[k,69] <- regionArea
  
    print(filelist[f])
  
    #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
    k = k + 1
  }  
      
}

colnames(DataDraft) <- c("Sample",
                         
                         "Region",
                         
                         paste(onlyF, "Cell Density (Cells/mm^2)"),
                         paste(onlyF, "Cell Count"),
                         paste(onlyF, "Cell Area (mm^2)"),
                         paste(onlyF, "Cell %"),
                         paste(onlyF, "Intensity"),
                         
                         paste(onlyT, "Cell Density (Cells/mm^2)"),
                         paste(onlyT, "Cell Count"),
                         paste(onlyT, "Cell Area (mm^2)"),
                         paste(onlyT, "Cell %"),
                         paste(onlyT, "Intensity"),
                         
                         paste(onlyC, "Cell Density (Cells/mm^2)"),
                         paste(onlyC, "Cell Count"),
                         paste(onlyC, "Cell Area (mm^2)"),
                         paste(onlyC, "Cell %"),
                         paste(onlyC, "Intensity"),
                         
                         paste(onlyD, "Cell Density (Cells/mm^2)"),
                         paste(onlyD, "Cell Count"),
                         paste(onlyD, "Cell Area (mm^2)"),
                         paste(onlyD, "Cell %"),
                         paste(onlyD, "Intensity"),
                         
                         paste(colocFT, "Cell Density (Cells/mm^2)"),
                         paste(colocFT, "Cell Count"),
                         paste(colocFT, "Cell Area (mm^2)"),
                         paste(colocFT, "Cell %"),
                         
                         paste(colocFC, "Cell Density (Cells/mm^2)"),
                         paste(colocFC, "Cell Count"),
                         paste(colocFC, "Cell Area (mm^2)"),
                         paste(colocFC, "Cell %"),
                         
                         paste(colocFD, "Cell Density (Cells/mm^2)"),
                         paste(colocFD, "Cell Count"),
                         paste(colocFD, "Cell Area (mm^2)"),
                         paste(colocFD, "Cell %"),
                         
                         paste(colocTC, "Cell Density (Cells/mm^2)"),
                         paste(colocTC, "Cell Count"),
                         paste(colocTC, "Cell Area (mm^2)"),
                         paste(colocTC, "Cell %"),
                         
                         paste(colocTD, "Cell Density (Cells/mm^2)"),
                         paste(colocTD, "Cell Count"),
                         paste(colocTD, "Cell Area (mm^2)"),
                         paste(colocTD, "Cell %"),
                         
                         paste(colocCD, "Cell Density (Cells/mm^2)"),
                         paste(colocCD, "Cell Count"),
                         paste(colocCD, "Cell Area (mm^2)"),
                         paste(colocCD, "Cell %"),
                         
                         paste(colocFTC, "Cell Density (Cells/mm^2)"),
                         paste(colocFTC, "Cell Count"),
                         paste(colocFTC, "Cell Area (mm^2)"),
                         paste(colocFTC, "Cell %"),
                         
                         paste(colocFTD, "Cell Density (Cells/mm^2)"),
                         paste(colocFTD, "Cell Count"),
                         paste(colocFTD, "Cell Area (mm^2)"),
                         paste(colocFTD, "Cell %"),
                         
                         paste(colocFCD, "Cell Density (Cells/mm^2)"),
                         paste(colocFCD, "Cell Count"),
                         paste(colocFCD, "Cell Area (mm^2)"),
                         paste(colocFCD, "Cell %"),
                         
                         paste(colocTCD, "Cell Density (Cells/mm^2)"),
                         paste(colocTCD, "Cell Count"),
                         paste(colocTCD, "Cell Area (mm^2)"),
                         paste(colocTCD, "Cell %"),
                         
                         paste(colocFTCD, "Cell Density (Cells/mm^2)"),
                         paste(colocFTCD, "Cell Count"),
                         paste(colocFTCD, "Cell Area (mm^2)"),
                         paste(colocFTCD, "Cell %"),
                         
                         "Total Cell Count",
                         "Total Cell Area (mm^2)",
                         "Total Tissue Area (mm^2)")


#Writes a csv file with the data in the path
write.csv(DataDraft,paste("Round 1 Cell Data",f,".csv"), row.names = F)
#write.xlsx(DataDraft, paste("IF Data Excel",f,".xlsx")) #excel files make for easier formatting

print(paste("DONE! csv written to", getwd()))





