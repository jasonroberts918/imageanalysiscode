path.det="C://Analysis_Studies//Steatosis QP//detection results"
path.ano = "C://Analysis_Studies//Steatosis QP//annotation results"

setwd(path.ano)
filelistano <- sort(dir(path.ano,pattern = ".txt"))

setwd(path.det)
filelist <- sort(dir(path.det,pattern = ".txt"))

DataDraft <- data.frame(matrix(ncol = 8))

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
  
  #cat("Length of Read.Data:", nrow(Read.Data), "\n")
  #cat("Unique Names in Read.Data:", unique(Read.Data$Name), "\n")
  
  
  #Read.Data[is.na(Read.Data)] <- 0
  #Read.Data.ano[is.na(Read.Data.ano)] <- 0
  
  for(regionName in unique(Read.Data$Name)){
    if(regionName == '3' | regionName == '2' | regionName == '1' ){
      
      Macro <- subset(Read.Data, Read.Data$Area > 65)
      Micro <- subset(Read.Data, Read.Data$Area < 65)
      
      #cat("Length of Macro:", nrow(Macro), "\n")
      #cat("Length of Micro:", nrow(Micro), "\n")
      
  
      MacroArea <- sum(Macro$Area)
      MicroArea <- sum(Micro$Area)
  
      realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == regionName)
      # realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "Annotation")
      # realAnnotations <- subset(Read.Data.ano, Read.Data.ano$Name == "Fat")
      anoArea <- sum(realAnnotations$Area.µm.2)/ 1000000 #division for conversion frum um^2 to mm^2
  
      DataDraft[k,1] <- filename
      DataDraft[k,2] <- regionName
      DataDraft[k,3] <- (MacroArea + MicroArea)/1000000
      DataDraft[k,4] <- ((MacroArea + MicroArea)/1000000)/anoArea*100
      DataDraft[k,5] <- MacroArea*100/(MacroArea+MicroArea)
      DataDraft[k,6] <- MicroArea*100/(MacroArea+MicroArea)
      DataDraft[k,7] <- mean(Read.Data$Area)
      DataDraft[k,8] <- anoArea
  
  
      k=k+1
    }
  }
}
colnames(DataDraft) <- c("Filename","Region", "Total Lipid Area (mm^2)", "% Lipid Area", "% Macrovesicular", "% Microvesicular", "Average Vesicle Size (um^2)", "Tissue Area Analyzed (mm^2)")
write.csv(DataDraft,paste("Steatosis Data",f,".csv"))