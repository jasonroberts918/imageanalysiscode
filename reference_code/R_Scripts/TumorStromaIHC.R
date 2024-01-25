
#Change path here, this is where your data is
path.det = "C:\\Analysis_Studies\\21-216 Tango qp2\\detection results2\\"
path.ano = "C:\\Analysis_Studies\\21-216 Tango qp2\\annotation results2\\"
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
  filename <- gsub(" Detections", "", filelist[f])
  print(filename)
  #Declare some tables for data
  Read.Data <- data.frame()
  Positive <- data.frame()  
  
  #This line reads the .txt file and places it into a table we can look at
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  
  setwd(path.ano)
  Read.Data.ano <- read.table(filename, header=T, sep="\t", fill = TRUE)
  setwd(path.det)
  #Basic calculations from the data, Negatives are all the things that are given the class Negative in the data etc, can be changed to be whatever
  
  Negative <- subset(Read.Data, Read.Data$Class == "Negative")
  Positive <- subset(Read.Data, Read.Data$Class == "Positive")
  
  tum_pos <- subset(Positive, Positive$Parent == "Tumor")
  tum_neg <- subset(Negative, Negative$Parent == "Tumor")
  str_pos <- subset(Positive, Positive$Parent == "Stroma")
  str_neg <- subset(Negative, Negative$Parent == "Stroma")
  oth_pos <- subset(Positive, Positive$Parent == "Other" | Positive$Parent == "Necrosis")
  oth_neg <- subset(Negative, Negative$Parent == "Other" | Negative$Parent == "Necrosis")
  
  NegativeArea <- sum(Negative$Cell..Area) / 1000000
  PositiveArea <- sum(Positive$Cell..Area) / 1000000
  
  Intensity <- mean(Positive$Cell..DAB.OD.mean)
  tumor_intensity <- mean(tum_pos$Cell..DAB.OD.mean)
  tum_nuc_intensity <- mean(tum_pos$Nucleus..DAB.OD.mean)
  tum_cy_intensity <- mean(tum_pos$Cytoplasm..DAB.OD.mean)
  st_intensity <- mean(str_pos$Cell..DAB.OD.mean)
  st_nuc_intensity <- mean(str_pos$Nucleus..DAB.OD.mean)
  st_cy_intensity <- mean(str_pos$Cytoplasm..DAB.OD.mean)
  totCells <- nrow(tum_pos) + nrow(tum_neg) + nrow(str_pos) + nrow(str_neg) + nrow(oth_pos) + nrow(oth_neg)
  
  subregions <- subset(Read.Data.ano, Read.Data.ano$ROI == "Area")
  tum_region <- subset(subregions, subregions$Class == "Tumor")
  str_region <- subset(subregions, subregions$Class == "Stroma")
  oth_region <- subset(subregions, subregions$Class == "Other" | subregions$Class == "Necrosis")
  wspc_region <- subset(subregions, subregions$Class == "Whitespace")
  anoArea <- sum(subregions$Area.µm.2) / 1000000
  #This DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
  #so k,1, if k = 1, would go in the first row, first column etc...
  
  DataDraft[k,1] <- gsub(".mrxs.txt", "", filename) #clean filename
  DataDraft[k,2] <- anoArea
  DataDraft[k,3] <- totCells
  DataDraft[k,4] <- nrow(tum_pos) + nrow(str_pos) + nrow(oth_pos)
  DataDraft[k,5] <- Intensity
  DataDraft[k,6] <- sum(tum_region$Area.µm.2) / 1000000
  DataDraft[k,7] <- nrow(tum_pos) + nrow(tum_neg)
  DataDraft[k,8] <- nrow(tum_pos)
  DataDraft[k,9] <- nrow(tum_pos) / totCells
  DataDraft[k,10] <- tumor_intensity
  DataDraft[k,11] <- tum_nuc_intensity
  DataDraft[k,12] <- tum_cy_intensity
  DataDraft[k,13] <- sum(str_region$Area.µm.2) / 1000000
  DataDraft[k,14] <- nrow(str_pos) + nrow(str_neg)
  DataDraft[k,15] <- nrow(str_pos)
  DataDraft[k,16] <- nrow(str_pos) / totCells
  DataDraft[k,17] <- st_intensity
  DataDraft[k,18] <- st_nuc_intensity
  DataDraft[k,19] <- st_cy_intensity
  DataDraft[k,22] <- mean(str_pos$Cell..DAB.OD.std.dev) #Stroma cell intensity std dev
  DataDraft[k,20] <- sum(oth_region$Area.µm.2) / 1000000
  DataDraft[k,21] <- nrow(oth_pos) + nrow(oth_neg)
  DataDraft[k,22] <- nrow(oth_pos)
  DataDraft[k,23] <- nrow(oth_pos) / totCells
  
  print(filelist[f])
  
  #The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
  k = k + 1
}


colnames(DataDraft) <- c("Sample",
                         "Area Analyzed (mm^2)",
                         "Total Cell Count",
                         "Total Positive Cell Count",
                         "Positive Cell Intensity",
                         "Tumor Area (mm^2)",
                         "Total Tumor Cell Count",
                         "Tumor Positive Cell Count",
                         "Tumor Positive % (of total)",
                         "Tumor Positive Whole Cell Mean DAB Intensity",
                         "Tumor Positive Nuclear Mean DAB Intensity",
                         "Tumor Positive Cytoplasmic Mean DAB Intensity",
                         "Stroma Area (mm^2)",
                         "Total Stroma Cell Count",
                         "Stroma Positive Cell Count",
                         "Stroma Positive % (of total)",
                         "Stroma Positive Whole Cell Mean DAB Intensity",
                         "Stroma Positive Nuclear Mean DAB Intensity",
                         "Stroma Positive Cytoplasmic Mean DAB Intensity",
                         "Other Area (mm^2)",
                         "Other Total Cell Count",
                         "Other Positive Cell Count",
                         "Other Positive % (of total)"
                         )

#Writes a csv file with the data in the path
write.csv(DataDraft,paste("Data - additional intensity measurements - ",f,".csv"), row.names = F)
