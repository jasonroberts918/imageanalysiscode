library("openxlsx")
library("stringr")

path = "G:\\Studies\\Study\\DetCTRLfin\\"
setwd(path)

filelist <- dir(path,pattern = ".txt")


DataDraft <- data.frame(matrix(ncol=19))

Marker1 = 'CCL24' #QP Green Pos
Marker2 = 'CD68' #QP Red Pos
colnames(DataDraft) <- c("Core", 
                         
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
                         
                         "Total Cell Count", 
                         "Total Cell Area (mm^2)")
k=1
for(f in 1:length(filelist)){
  print(filelist[f])
  
  initialdata <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  initialdata[is.na(initialdata)] <- 0 #if any "NA" entries, make them "0"

  for(regionName in unique(initialdata$Name)){
    print(regionName)
    coredata <- subset(initialdata, initialdata$Name == regionName)
    
    Negative <- subset(coredata, coredata$Class == "Cell")
    GreenPos <- subset(coredata, coredata$Class == "Positive Green") 
    RedPos <- subset(coredata, coredata$Class == "Positive Red")
    BothPos <- subset(coredata, coredata$Class == "Positive Both")
    #Background <- subset(coredata, coredata$Class == "Other" )
    
    NegativeArea <- sum(Negative$Cell..Area) / 1000000
    GreenPosArea <- sum(GreenPos$Cell..Area)  / 1000000
    RedPosArea <- sum(RedPos$Cell..Area)  / 1000000
    BothArea <- sum(BothPos$Cell..Area) / 1000000
    #ExcludedArea <- sum(Background$Cell..Area)
    
    Intensity_GreenPos <- mean(GreenPos$Cell..Channel.2.mean)
    Intensity_RedPos <- mean(RedPos$Cell..Channel.1.mean)
    
    Tot.Cells <- nrow(GreenPos) + nrow(RedPos) + nrow(Negative) + nrow(BothPos)
    Tot.Cell.Area <- NegativeArea + GreenPosArea + RedPosArea + BothArea
    
    
    DataDraft[k,1] <- regionName
    
    DataDraft[k,2] <- nrow(GreenPos) / Tot.Cell.Area
    DataDraft[k,3] <- nrow(GreenPos)
    DataDraft[k,4] <- GreenPosArea
    DataDraft[k,5] <- nrow(GreenPos) / Tot.Cells
    DataDraft[k,6] <- Intensity_GreenPos
    
    DataDraft[k,7] <- nrow(RedPos) / Tot.Cell.Area
    DataDraft[k,8] <- nrow(RedPos)
    DataDraft[k,9] <- RedPosArea
    DataDraft[k,10] <- nrow(RedPos) / Tot.Cells
    DataDraft[k,11] <- Intensity_RedPos
    
    DataDraft[k,12] <- nrow(BothPos) / Tot.Cell.Area
    DataDraft[k,13] <- nrow(BothPos)
    DataDraft[k,14] <- BothArea
    DataDraft[k,15] <- nrow(BothPos) / Tot.Cells
    
    DataDraft[k,16] <- Tot.Cells
    DataDraft[k,17] <- Tot.Cell.Area
    
    
    k = k + 1
  }
  k = k + 1
  print(filelist[f])
}
write.csv(DataDraft,paste("Final_Regional_Data",k,".csv"), row.names=FALSE)
