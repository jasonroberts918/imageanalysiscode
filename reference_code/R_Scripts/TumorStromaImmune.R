#install.packages("scales")
library(scales)

 #Change path here, this is where your data is
path.det = "C:\\Studies\\Study\\det\\"
path.ano = "C:\\Studies\\Study\\ano\\"

setwd(path.ano)
filelistano <- sort(dir(path.ano,pattern = ".txt"))

setwd(path.det)
filelist <- sort(dir(path.det,pattern = ".txt"))


#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 15))

#This is a counter, set it equal to 1 outside of the for loop, within the for loop we increase it (k = k + 1) 
#through each pass through the loop to have a counter for each row of data, so first .txt file goes in k = 1 row, second is k = k + 1 row etc..

k = 1

#For loop, for every file ending in .txt in that path, we will run through this loop of calculations once.  
#perhaps change this to a while loop --> while filelist[1] == filelistano[1]  (kills 2 birds with 1 stone)
while(k <= length(filelist) & filelist[k] == filelistano[k]){
  
  #Declare some tables for data
  Read.Data <- data.frame()
  Positive <- data.frame()  
  
  #This line reads the .txt file and places it into a table we can look at
  setwd(path.ano)
  Read.Dataano <- read.table(filelistano[k], header = T, sep="\t", fill = TRUE)
  Read.Dataano <- subset(Read.Dataano, Read.Dataano$Name == "PathAnnotationObject" & Read.Dataano$Area.µm.2 > 0)
  setwd(path.det)
  Read.Data <- read.table(filelist[k], header=T, sep="\t", fill = TRUE)
  
  Read.Data[is.na(Read.Data)] <- 0
  Read.Dataano[is.na(Read.Dataano)] <- 0
  #Basic calculations from the data, Negatives are all the things that are given the class Negative in the data etc, can be changed to be whatever
  
  Negative <- subset(Read.Data, Read.Data$Name == "Stroma")
  Positive <- subset(Read.Data, Read.Data$Name == "Immune cells")
  Tumor <- subset(Read.Data, Read.Data$Name == "Tumor")
  
  NegativeArea <- sum(Negative$Cell..Area) / 1000000 #division for conversion frum um^2 to mm^2
  PositiveArea <- sum(Positive$Cell..Area) / 1000000
  TumorArea <- sum(Tumor$Cell..Area) / 1000000
  
  Intensity <- mean(Positive$Nucleus..Hematoxylin.OD.mean)
  
  AnnotationArea <- sum(Read.Dataano$Area.µm.2)/1000000
  totCellArea <- NegativeArea + PositiveArea + TumorArea
  #This DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
  #so k,1, if k = 1, would go in the first row, first column etc...
  filename <- gsub(".txt", "", filelist[k])
  DataDraft[k,1] <- filename
  DataDraft[k,2] <- nrow(Positive)
  DataDraft[k,3] <- nrow(Negative)
  DataDraft[k,4] <- nrow(Tumor)
  DataDraft[k,5] <- PositiveArea
  DataDraft[k,6] <- PositiveArea / totCellArea
  DataDraft[k,7] <- NegativeArea
  DataDraft[k,8] <- NegativeArea / totCellArea
  DataDraft[k,9] <- TumorArea
  DataDraft[k,10] <- TumorArea / totCellArea
  DataDraft[k,11] <- Intensity
  
  DataDraft[k,12] <- nrow(Positive) / totCellArea
  DataDraft[k,13] <- nrow(Negative) / totCellArea
  DataDraft[k,14] <- nrow(Tumor) / totCellArea
  
  DataDraft[k,15] <- AnnotationArea
  DataDraft[k,16] <- totCellArea
  
  print(filelist[k])
  #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
  k = k + 1
}

colnames(DataDraft) <- c("Sample", 
                         "Immune Cell Count", 
                         "Negative Cell Count",
                         "Tumor Cell Count",
                         "Immune Cell Area (mm^2)", 
                         "Immune Cell Area %",
                         "Negative Cell Area (mm^2)",
                         "Negative Cell Area %",
                         "Tumor Cell Area (mm^2)",
                         "Tumor Cell Area %",
                         "Immune Cell Intensity",
                         
                         "Immune Cell Cell Density (cells/mm^2)",
                         "Negative Cell Density (cells/mm^2)",
                         "Tumor Cell Density (cells/mm^2)",
                         
                         "Annotation Area (mm^2)",
                         "Total Cell Area (mm^2)"
                          )


write.csv(DataDraft,paste("Data",k,".csv",row.names=FALSE))
