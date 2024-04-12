path.det = "C://Analysis_Studies//23-509_TMA_TA4398_QP//detection results"
path.ano = "C://Analysis_Studies//23-509_TMA_TA4398_QP//annotation results"

#set working directory
setwd(path.det)

#Tells it to look for all .txt files in the path given above
filelist <- dir(path.det,pattern = ".txt")

#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 10))


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
  
  for(regionName in unique(Read.Data$Parent)){
    if(regionName == '1' | regionName == '2' | regionName == '3' | regionName == '4' | regionName == '5' | regionName == '6' | regionName == '7' | regionName == '8' | regionName == '9' | regionName == '10' | regionName == '11' | regionName == '12' | regionName == '13' | regionName == '14' | regionName == '15' | regionName == '16' | regionName == '17' | regionName == '18' | regionName == '19' | regionName == '20' | regionName == '21' | regionName == '22' | regionName == '23' | regionName == '24' | regionName == '25' | regionName == '26' | regionName == '27' | regionName == '28' | regionName == '29' | regionName == '30' | regionName == '31' | regionName == '32' | regionName == '33' | regionName == '34' | regionName == '35' | regionName == '36' | regionName == '37' | regionName == '38' | regionName == '39' | regionName == '40' | regionName == '41' | regionName == '42' | regionName == '43' | regionName == '44' | regionName == '45' | regionName == '46' | regionName == '47' | regionName == '48' | regionName == '49' | regionName == '50' | regionName == '51' | regionName == '52' | regionName == '53' | regionName == '54' | regionName == '55' | regionName == '56' | regionName == '57' | regionName == '58' ){
      
      a0bin.cells <- subset(Negative, Parent == regionName & FinalDotCount == 0)
      a1bin.cells <- subset(Cells, Parent == regionName & FinalDotCount > 0 & FinalDotCount <= 1)
      a2.3bin.cells <- subset(Cells, Parent == regionName & FinalDotCount >= 2 & FinalDotCount <= 3)
      a4.9bin.cells <- subset(Cells, Parent == regionName & FinalDotCount >= 4 & FinalDotCount <= 9)
      a10bin.cells <- subset(Cells, Parent == regionName & FinalDotCount >= 10)
      
      totalCellCount <- nrow(a0bin.cells) + nrow(a1bin.cells) + nrow(a2.3bin.cells) + nrow(a4.9bin.cells) + nrow(a10bin.cells)
      
      print(filelist[f])
      positiveCellCount <- nrow(a1bin.cells) + nrow(a2.3bin.cells) + nrow(a4.9bin.cells) + nrow(a10bin.cells)
      HScore <- nrow(a1bin.cells)/totalCellCount*100 + 2*nrow(a2.3bin.cells)/totalCellCount*100 + 3*nrow(a4.9bin.cells)/totalCellCount*100 + 4*nrow(a10bin.cells)/totalCellCount*100
      percentofCellsAnalyzed <- 100
      
      #This DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
      #so k,1, if k = 1, would go in the first row, first column etc...
      filename <- gsub(".txt","", filelist[f])
      
      #Count Data
      DataDraft[k,1] <- filename
      DataDraft[k,2] <- regionName
      
      DataDraft[k,3] <- nrow(a0bin.cells)/totalCellCount*100
      DataDraft[k,4] <- nrow(a1bin.cells)/totalCellCount*100
      DataDraft[k,5] <- nrow(a2.3bin.cells)/totalCellCount*100
      DataDraft[k,6] <- nrow(a4.9bin.cells)/totalCellCount*100
      DataDraft[k,7] <- nrow(a10bin.cells)/totalCellCount*100
      
      DataDraft[k,8] <- HScore
      DataDraft[k,9] <- percentofCellsAnalyzed
      DataDraft[k,10] <- positiveCellCount/totalCellCount*100
      
      
      #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
      k = k + 1
    } #else {
    # print(paste('skipped', filelist[f], regionName))
    
  }    
}
colnames(DataDraft) <- c("Filename",
                         "Core",
                         "Bin 0 (%Cells)",
                         "Bin 1 (%Cells)",
                         "Bin 2 (%Cells)",
                         "Bin 3 (%Cells)",
                         "Bin 4 (%Cells)",
                         "H-Score",
                         "% of Cells Analyzed",
                         "% of Positive Cells")


#Writes a csv file with the data in the path
write.csv(DataDraft,paste("23-509 TMA TA4398 Data",f,".csv"), row.names = F)
print("DONE!")