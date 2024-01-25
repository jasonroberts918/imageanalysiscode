path.det="D://23-690 UNCCH_Steatosis_qp//detection results"
path.ano = "D://23-690 UNCCH_Steatosis_qp//annotation results"
setwd(path.det)

#Tells it to look for all .txt files in the path given above
filelist <- dir(path.det,pattern = ".txt")

DataDraft <- data.frame(matrix(ncol = 12))

k = 1

for(f in 1:length(filelist)) {
  
  #Declare some tables for data
  Read.Data <- data.frame()
  Micro <- data.frame()
  Macro <- data.frame()
  
  setwd(path.ano)
  filename <- gsub(" Detections", "", filelist[f])
  Read.Data.ano <- read.table(filename, header=T, sep="\t", fill = TRUE)
  setwd(path.det)
  
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  Read.Data <- subset(Read.Data, Read.Data$Class == 'Positive')
  
  
  Macro <- subset(Read.Data, Read.Data$Area > 65)
  Micro <- subset(Read.Data, Read.Data$Area < 65)
  
  MacroArea <- sum(Macro$Area)
  MicroArea <- sum(Micro$Area)
  
  realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "PathAnnotationObject")
  #realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "Annotation")
  # realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "Fat")
  anoArea <- sum(realAnnotations$Area.Âµm.2)/ 1000000 #division for conversion frum um^2 to mm^2
  
  filename <- gsub(".txt", "", filelist[f])
  filename <- gsub(".mrxs", "", filelist[f])
  
  DataDraft[k,1] <- filename
  DataDraft[k,2] <- (MacroArea + MicroArea)/1000000
  DataDraft[k,3] <- ((MacroArea + MicroArea)/1000000)/(anoArea)
  DataDraft[k,4] <- MacroArea*100/(MacroArea+MicroArea)
  DataDraft[k,5] <- MicroArea*100/(MacroArea+MicroArea)
  DataDraft[k,6] <- mean(Read.Data$Area)
  DataDraft[k,7] <- anoArea
  
  
  k=k+1
  
}

# Assign column names after the loop
colnames(DataDraft) <- c(
  "Sample", "Total Lipid Area (mm^2)", "% Lipid Area",
  "% Macrovesicular", "% Microvesicular",
  "Average Vesicle Size (um^2)", "Tissue Area Analyzed (mm^2)"
)

# Write the CSV file
write.csv(DataDraft, paste("Data", f, ".csv"))
