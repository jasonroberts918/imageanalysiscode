library(plyr)
library(openxlsx)
library(ggplot2)
path = "C://Analysis_Studies//Study//detection results"
path.ano = "C://Analysis_Studies//Study//annotation results"
stainName = "WGA"
setwd(path.ano)
filelistAno <- sort(dir(path.ano,pattern = ".txt"))
setwd(path)
filelist <- dir(path,pattern = ".txt")
#Channel 1 is Red
#Channel 2 is Green
DataDraft <- data.frame(matrix(ncol = 7))
k = 1
for(f in 1:length(filelist)) {
  Read.Data <- data.frame()
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  setwd(path.ano)
  Read.Data.ano <- read.table(filelistAno[f], header=T, sep="\t", fill = TRUE)
  Read.Data.ano[is.na(Read.Data.ano)] = 0
  setwd(path)
  Lipids <- Read.Data
  Lipids <- subset(Lipids, Lipids$Class == "Positive")
  Lipids[is.na(Lipids)] = 0
  #Lipids <- perfectdatatable
  plotfun <- ggplot(Lipids, aes(x =Area)) + theme(text = element_text(size = 6))
  plotfun <- plotfun + geom_density(stat = "density",position=position_dodge(),
                                    alpha = .3, fill = "#4271AE") + xlab("Area of Muscle Fiber (um^2)") + ylab("Frequency") + ylim(0, .0005) + xlim(0,3500)
  plotfun <- plotfun + theme_bw()
  plotfun
  final_name <- strsplit(filelist[f], ".txt")
  ggsave(paste(final_name,".png"))
  #BigLipids <- subset(Lipids, Lipids$ROI.Shape..Area.µm.2 > 10)
  # Layer123 <- subset(Read.Data, Read.Data$Name == list1[i])
  perilipin_Area <- sum(Lipids$Area)/1000000
  det_Area <-sum(Read.Data$Area)/1000000
  anno_Area <- sum(Read.Data.ano$Area.µm.2)/1000000
  filename <- gsub(".txt", "", filelist[f])
  DataDraft[k,1] <- filename
  DataDraft[k,2] <- mean(Lipids$Area)
  DataDraft[k,3] <- quantile(Lipids$Area, 0.75) - quantile(Lipids$Area, 0.25)
  DataDraft[k,4] <- quantile(Lipids$Area, 0.25)
  DataDraft[k,5] <- median(Lipids$Area)
  DataDraft[k,6] <- quantile(Lipids$Area, 0.75)
  DataDraft[k,7] <- quantile(Lipids$Area, 0.9)
  #DataDraft[k,3] <- nrow(Negative)
  #DataDraft[k,4] <- sum(Lipids$Area.µm.2)/1000000
  # try(DataDraft[k,5] <- list1[i])
  k = k + 1
}
colnames(DataDraft) <- c("Sample",
                         paste("Mean Cross Sectional Area (um)"),
                         paste("Myocyte Area: Interquartile Range"),
                         paste("Myocyte Area: 25th Percentile"),
                         paste("Myocyte Area: Median"),
                         paste("Myocyte Area: 75th Percentile"),
                         paste("Myocyte Area: 90th Percentile"))
write.csv(DataDraft,paste(stainName, "Data",f,".csv"), row.names = F)
write.xlsx(DataDraft,paste(stainName, "Data",f,".xlsx"))
