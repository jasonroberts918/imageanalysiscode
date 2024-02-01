

#Change path here, this is where your data is
#Path needs to have double backslashes 
path.det = "C:\\Analysis_Studies\\Study\\detection results\\"
path.ano = "C:\\Analysis_Studies\\Study\\annotation results\\"

#set working directory
setwd(path.det)

#Tells it to look for all .txt files in the path given above
filelist <- dir(path.det,pattern = ".txt")

#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 9))
DataDraft2 <- data.frame(matrix(ncol = 9))


setwd(path.ano)
filelistano <- sort(dir(path.ano,pattern = ".txt"))

#This is a counter, set it equal to 1 outside of the for loop, within the for loop we increase it (k = k + 1) 
#through each pass through the loop to have a counter for each row of data, so first .txt file goes in k = 1 row, second is k = k + 1 row etc..

k = 1

#For loop, for every file ending in .txt in that path, we will run through this loop of calculations once.  
for(f in 1:length(filelist)){
  
  #Declare some tables for data
  Read.Data <- data.frame()
  a0bin.cells <- data.frame()
  a2.4bin.cells <- data.frame()
  a5.9bin.cells <- data.frame()
  a10bin.cells <- data.frame()
  
  setwd(path.ano)
  Read.Dataano <- read.table(filelistano[f], header = T, sep="\t", fill = TRUE, comment.char="")
  Read.Dataano <- subset(Read.Dataano, Read.Dataano$Name == "PathAnnotationObject" & Read.Dataano$Area.µm.2 > 0)
  
  #This line reads the .txt file and places it into a table we can look at
  setwd(path.det)
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE, comment.char="")
  
  #'Cells' is the positive class -- put anything in here that has ISH dots you want to count
  Cells <- subset(Read.Data, Read.Data$Name == "PathCellObject")
  
  # 'Negative' is the negative class -- put cells in here that you DONT want the ISH dots to count for
  Negative <- subset(Read.Data, Read.Data$Name == "Excluded")
  
  Cells[is.na(Cells)] <- 0
  #variable for ease
  #Cells <- CellObjects$updated.spot.count
  
  a0bin.cells <- subset(Cells, Cells$Subcellular..Channel.2..Num.spots.estimated == 0)
  a1bin.cells <- subset(Cells, Cells$Subcellular..Channel.2..Num.spots.estimated > 0 & Cells$Subcellular..Channel.2..Num.spots.estimated < 2)
  a2.4bin.cells <- subset(Cells, Cells$Subcellular..Channel.2..Num.spots.estimated >= 2 & Cells$Subcellular..Channel.2..Num.spots.estimated <= 4)
  a5.9bin.cells <- subset(Cells, Cells$Subcellular..Channel.2..Num.spots.estimated > 4 & Cells$Subcellular..Channel.2..Num.spots.estimated <= 9)
  a10bin.cells <- subset(Cells, Cells$Subcellular..Channel.2..Num.spots.estimated > 9)  #& Cells$updated.spot.count <= 50)
  
  totCellArea <- (sum(Cells$Cell..Area)) / 1000000
  totCellCount <- nrow(Cells)
  AnnotationArea <- sum(Read.Dataano$Area.µm.2)/1000000
  
  print(filelist[f])
  otherCellCount <- nrow(a0bin.cells) + nrow(Negative) + nrow(a1bin.cells) + nrow(a2.4bin.cells) + nrow(a5.9bin.cells) + nrow(a10bin.cells)
  
  
  #This DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
  #so k,1, if k = 1, would go in the first row, first column etc...
  filename <- gsub(".txt","", filelist[f])
  
  #Count Data
  DataDraft[k,1] <- filename
  
  DataDraft[k,2] <- totCellCount
  DataDraft[k,3] <- nrow(a0bin.cells)
  DataDraft[k,4] <- nrow(a1bin.cells)
  DataDraft[k,5] <- nrow(a2.4bin.cells)
  DataDraft[k,6] <- nrow(a5.9bin.cells)
  DataDraft[k,7] <- nrow(a10bin.cells)
  
  DataDraft[k,8] <- totCellArea
  DataDraft[k,9] <- AnnotationArea
  
  #Density Data
  DataDraft2[k,1] <- filename
  
  DataDraft2[k,2] <- (nrow(Cells))
  DataDraft2[k,3] <- (nrow(a0bin.cells)) / totCellArea
  DataDraft2[k,4] <- nrow(a1bin.cells) / totCellArea
  DataDraft2[k,5] <- nrow(a2.4bin.cells) / totCellArea
  DataDraft2[k,6] <- nrow(a5.9bin.cells) / totCellArea
  DataDraft2[k,7] <- nrow(a10bin.cells) / totCellArea
  
  DataDraft2[k,8] <- totCellArea
  DataDraft2[k,9] <- AnnotationArea
  
  #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
  k = k + 1
}
colnames(DataDraft) <- c("Sample", 
                         "Total Cell Count",
                         "Negative Cell Count",
                         "1 ISH Dot cell Count",
                         "2-4 ISH Dot Cell Count",
                         "5-9 ISH Dot Cell Count",
                         "10+ ISH Dot Cell Count",
                         "Total Cell Area (mm^2)",
                         "Total Annotation Area (mm^2)")

colnames(DataDraft2) <- c("Sample", 
                          
                          "Total Cell Count",
                          "Negative Cell Density (cells/mm^2)",
                          "1 ISH Dot cell Density (cells/mm^2)",
                          "2-4 ISH Dot Cell Density (cells/mm^2)",
                          "5-9 ISH Dot Cell Density (cells/mm^2)",
                          "10+ ISH Dot Cell Density (cells/mm^2)",
                          "Total Cell Area (mm^2)",
                          "Total Annotation Area (mm^2)")

#Writes a csv file with the data in the path
write.csv(DataDraft,paste("ISH DATA Counts",f,".csv"), row.names = F)
write.csv(DataDraft2,paste("ISH DATA Density",f,".csv"), row.names = F)
print("DONE!")
