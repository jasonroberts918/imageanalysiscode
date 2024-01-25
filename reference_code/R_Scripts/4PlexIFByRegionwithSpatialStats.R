library(openxlsx)
library(data.table)
library(stringr)
#Change path here, this is where your data is
path.det = "C:\\Analysis_Studies\\Alentis POC QP\\spatial results"
#path.ano = "C:\\Analysis_Studies\\Alentis POC QP\\annotation results"

setwd(path.det)

#Tells it to look for all .txt files in the path given above
filelist_raw <- dir(path.det,pattern = ".csv") #Need this janky code because QP2 exports the detections files with "Detections" after the .mrxs extension...
filelist_int <- strsplit(filelist_raw, " Detections")
filelist <- unlist(filelist_int)[2*(1:length(filelist_raw))-1]

#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 76))

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
  setwd(path.det)
  Read.Data <- read.table(filelist_raw[f], header=T, sep=",", fill = TRUE)
  print(filelist_raw[f])
  
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
    
    
    
    #This DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
    #so k,1, if k = 1, would go in the first row, first column etc...
    
    #manually fixing file names
    filename <- str_split(filelist_raw[f], ".ome.tiff")[[1]][1]
    #filename <- str_split(filename, "-SMA ")[[1]][2]
    
    DataDraft[k,1] <- filename
    DataDraft[k,2] <- regionName
    
    DataDraft[k,3] <- mean(FITC_only$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,4] <- median(FITC_only$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,5] <- quantile(FITC_only$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(FITC_only$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,6] <- quantile(FITC_only$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,7] <- quantile(FITC_only$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,8] <- mean(TRITC_only$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,9] <- median(TRITC_only$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,10] <- quantile(TRITC_only$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(TRITC_only$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,11] <- quantile(TRITC_only$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,12] <- quantile(TRITC_only$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,13] <- mean(Cy5_only$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,14] <- median(Cy5_only$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,15] <- quantile(Cy5_only$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(Cy5_only$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,16] <- quantile(Cy5_only$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,17] <- quantile(Cy5_only$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,18] <- mean(Cy7_only$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,19] <- median(Cy7_only$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,20] <- quantile(Cy7_only$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(Cy7_only$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,21] <- quantile(Cy7_only$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,22] <- quantile(Cy7_only$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,23] <- mean(FITC_TRITC$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,24] <- median(FITC_TRITC$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,25] <- quantile(FITC_TRITC$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(FITC_TRITC$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,26] <- quantile(FITC_TRITC$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,27] <- quantile(FITC_TRITC$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,28] <- mean(FITC_Cy5$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,29] <- median(FITC_Cy5$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,30] <- quantile(FITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(FITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,31] <- quantile(FITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,32] <- quantile(FITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,33] <- mean(FITC_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,34] <- median(FITC_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,35] <- quantile(FITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(FITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,36] <- quantile(FITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,37] <- quantile(FITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,38] <- mean(TRITC_Cy5$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,39] <- median(TRITC_Cy5$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,40] <- quantile(TRITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(TRITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,41] <- quantile(TRITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,42] <- quantile(TRITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,43] <- mean(TRITC_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,44] <- median(TRITC_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,45] <- quantile(TRITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(TRITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,46] <- quantile(TRITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,47] <- quantile(TRITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,48] <- mean(Cy5_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,49] <- median(Cy5_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,50] <- quantile(Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,51] <- quantile(Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,52] <- quantile(Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,53] <- mean(FITC_TRITC_Cy5$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,54] <- median(FITC_TRITC_Cy5$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,55] <- quantile(FITC_TRITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(FITC_TRITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,56] <- quantile(FITC_TRITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,57] <- quantile(FITC_TRITC_Cy5$Distance.to.annotation.with.Tumor.µm, 0.75)
  
    DataDraft[k,58] <- mean(FITC_TRITC_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,59] <- median(FITC_TRITC_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,60] <- quantile(FITC_TRITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(FITC_TRITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,61] <- quantile(FITC_TRITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,62] <- quantile(FITC_TRITC_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,63] <- mean(FITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,64] <- median(FITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,65] <- quantile(FITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(FITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,66] <- quantile(FITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,67] <- quantile(FITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,68] <- mean(TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,69] <- median(TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,70] <- quantile(TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,71] <- quantile(TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,72] <- quantile(TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75)
    
    DataDraft[k,73] <- mean(FITC_TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,74] <- median(FITC_TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm)
    DataDraft[k,75] <- quantile(FITC_TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75) - quantile(FITC_TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,76] <- quantile(FITC_TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.25)
    DataDraft[k,77] <- quantile(FITC_TRITC_Cy5_Cy7$Distance.to.annotation.with.Tumor.µm, 0.75)

    
    print(filelist[f])
    
    #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
    k = k + 1
  }  
  
}

colnames(DataDraft) <- c("Sample",
                         
                         "Region",
                         
                         paste(onlyF, " to Tumor Beds: Mean Distance (um)"),
                         paste(onlyF, " to Tumor Beds: Median Distance (um)"),
                         paste(onlyF, " to Tumor Beds: Interquartile Range (um)"),
                         paste(onlyF, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(onlyF, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(onlyT, " to Tumor Beds: Mean Distance (um)"),
                         paste(onlyT, " to Tumor Beds: Median Distance (um)"),
                         paste(onlyT, " to Tumor Beds: Interquartile Range (um)"),
                         paste(onlyT, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(onlyT, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(onlyC, " to Tumor Beds: Mean Distance (um)"),
                         paste(onlyC, " to Tumor Beds: Median Distance (um)"),
                         paste(onlyC, " to Tumor Beds: Interquartile Range (um)"),
                         paste(onlyC, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(onlyC, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(onlyD, " to Tumor Beds: Mean Distance (um)"),
                         paste(onlyD, " to Tumor Beds: Median Distance (um)"),
                         paste(onlyD, " to Tumor Beds: Interquartile Range (um)"),
                         paste(onlyD, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(onlyD, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocFT, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocFT, " to Tumor Beds: Median Distance (um)"),
                         paste(colocFT, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocFT, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocFT, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocFC, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocFC, " to Tumor Beds: Median Distance (um)"),
                         paste(colocFC, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocFC, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocFC, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocFD, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocFD, " to Tumor Beds: Median Distance (um)"),
                         paste(colocFD, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocFD, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocFD, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocTC, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocTC, " to Tumor Beds: Median Distance (um)"),
                         paste(colocTC, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocTC, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocTC, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocTD, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocTD, " to Tumor Beds: Median Distance (um)"),
                         paste(colocTD, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocTD, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocTD, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocCD, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocCD, " to Tumor Beds: Median Distance (um)"),
                         paste(colocCD, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocCD, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocCD, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocFTC, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocFTC, " to Tumor Beds: Median Distance (um)"),
                         paste(colocFTC, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocFTC, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocFTC, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocFTD, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocFTD, " to Tumor Beds: Median Distance (um)"),
                         paste(colocFTD, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocFTD, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocFTD, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocFCD, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocFCD, " to Tumor Beds: Median Distance (um)"),
                         paste(colocFCD, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocFCD, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocFCD, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocTCD, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocTCD, " to Tumor Beds: Median Distance (um)"),
                         paste(colocTCD, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocTCD, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocTCD, " to Tumor Beds: 75th Percentile Distance (um)"),
                         
                         paste(colocFTCD, " to Tumor Beds: Mean Distance (um)"),
                         paste(colocFTCD, " to Tumor Beds: Median Distance (um)"),
                         paste(colocFTCD, " to Tumor Beds: Interquartile Range (um)"),
                         paste(colocFTCD, " to Tumor Beds: 25th Percentile Distance (um)"),
                         paste(colocFTCD, " to Tumor Beds: 75th Percentile Distance (um)")
                         
                         )


#Writes a csv file with the data in the path
write.csv(DataDraft,paste("Round 1 Spatial Data",f,".csv"), row.names = F)
#write.xlsx(DataDraft, paste("IF Data Excel",f,".xlsx")) #excel files make for easier formatting

print(paste("DONE! csv written to", getwd()))





