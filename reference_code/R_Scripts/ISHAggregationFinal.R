path.det = "C://Analysis_Studies//Study//detection results"
path.ano = "C://Analysis_Studies//Study//annotation results"

#set working directory
setwd(path.det)

#Tells it to look for all .txt files in the path given above
filelist <- dir(path.det,pattern = ".txt")

#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 9))


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
  a2.3bin.cells <- data.frame()
  a4.9bin.cells <- data.frame()
  a10bin.cells <- data.frame()
  
  setwd(path.ano)
  Read.Dataano <- read.table(filelistano[f], header = T, sep="\t", fill = TRUE, comment.char="")
  Read.Dataano <- subset(Read.Dataano, Read.Dataano$Name == "PathAnnotationObject" & Read.Dataano$Area.µm.2 > 0)
  
  #This line reads the .txt file and places it into a table we can look at
  setwd(path.det)
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE, comment.char="")
  
  #'Cells' is the positive class -- put anything in here that has ISH dots you want to count
  Cells <- subset(Read.Data, Read.Data$Name == "Positive")
  
  # 'Negative' is the negative class -- put cells in here that you DONT want the ISH dots to count for
  Negative <- subset(Read.Data, Read.Data$Name == "Negative")
  
  Cells[is.na(Cells)] <- 0
  #variable for ease
  #Cells <- CellObjects$updated.spot.count
  
  a0bin.cells <- subset(Negative, Negative$FinalDotCount == 0)
  a1bin.cells <- subset(Cells, Cells$FinalDotCount > 0 & Cells$FinalDotCount <= 1)
  a2.3bin.cells <- subset(Cells, Cells$FinalDotCount >= 2 & Cells$FinalDotCount <= 3)
  a4.9bin.cells <- subset(Cells, Cells$FinalDotCount >= 4 & Cells$FinalDotCount <= 9)
  a10bin.cells <- subset(Cells, Cells$FinalDotCount >= 10)  #& Cells$updated.spot.count <= 50)
  
  totalCellCount <- nrow(Cells) + nrow(Negative)
  
  print(filelist[f])
  positiveCellCount <- nrow(a1bin.cells) + nrow(a2.3bin.cells) + nrow(a4.9bin.cells) + nrow(a10bin.cells)
  HScore <- nrow(a1bin.cells)/totalCellCount*100 + 2*nrow(a2.3bin.cells)/totalCellCount*100 + 3*nrow(a4.9bin.cells)/totalCellCount*100 + 4*nrow(a10bin.cells)/totalCellCount*100
  percentofCellsAnalyzed <- 100
  
  #This DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
  #so k,1, if k = 1, would go in the first row, first column etc...
  filename <- gsub(".txt","", filelist[f])
  
  #Count Data
  DataDraft[k,1] <- filename
  
  DataDraft[k,2] <- nrow(a0bin.cells)/totalCellCount*100
  DataDraft[k,3] <- nrow(a1bin.cells)/totalCellCount*100
  DataDraft[k,4] <- nrow(a2.3bin.cells)/totalCellCount*100
  DataDraft[k,5] <- nrow(a4.9bin.cells)/totalCellCount*100
  DataDraft[k,6] <- nrow(a10bin.cells)/totalCellCount*100
  
  DataDraft[k,7] <- HScore
  DataDraft[k,8] <- percentofCellsAnalyzed
  DataDraft[k,9] <- positiveCellCount/totalCellCount*100
  
  
  #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
  k = k + 1
}
colnames(DataDraft) <- c("Filename",
                         "Bin 0 (%Cells)",
                         "Bin 1 (%Cells)",
                         "Bin 2 (%Cells)",
                         "Bin 3 (%Cells)",
                         "Bin 4 (%Cells)",
                         "H-Score",
                         "% of Cells Analyzed",
                         "% of Positive Cells")


#Writes a csv file with the data in the path
write.csv(DataDraft,paste("22-1137 MMP1 ISH Data",f,".csv"), row.names = F)
print("DONE!")
