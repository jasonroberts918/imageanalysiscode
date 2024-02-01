library("openxlsx")
library("stringr")

path = "C:\\Analysis_Studies\\Study\\detection results"
setwd(path)

filelist <- dir(path,pattern = ".txt")

#for creating the final xlsx
wb <- createWorkbook()

#get list of all the intensity values of positive cells so you can make a distribution and threshold
study_int_values <- list()
for (d in 1:length(filelist)){
  print(filelist[d])
  filename <- gsub(".mrxs Detections.txt", "", filelist[d])
  
  #Don't care about cores/specific annotations so no regional subsetting needed
  slidedata <- read.table(filelist[d], header=T, sep="\t", fill = TRUE)
  Positive <- subset(slidedata, slidedata$Class == "Positive")
  #append to master list
  study_int_values <- c(study_int_values, Positive$Cell..DAB.OD.mean)
  
}
#Now get threshold values from the global list of int values

study_int_values <- lapply(study_int_values, function(x) x[!is.na(x)]) #remove NA
study_int_values <- unlist(study_int_values) #now its a vector

#optional z-score anlaysis
z_scores <- (study_int_values-mean(study_int_values))/sd(study_int_values) #Calculate z-score for outlier removal
df <- do.call(rbind, Map(data.frame, vals=study_int_values, zscore=z_scores))
final_set <- subset(df, df$zscore < 3)$vals

#get thresholds
thresholds_raw <- quantile(study_int_values, probs = c(0.33,0.67))
thesholds_z <- quantile(final_set, probs = c(0.33,0.67))

thresh_33 <- thresholds_raw[[1]]
thresh_66 <- thresholds_raw[[2]]


#Build the structure of the data table
DataDraft <- data.frame(matrix(ncol=10))
colnames(DataDraft) <- c("Sample",
                         
                         "Total Cells",
                         "Thresholds",
                         "1 class count",
                         "1 class %",
                         "2 class count",
                         "2 class %",
                         "3 class count", 
                         "3 class %",
                         "H-score")
k=1
for(f in 1:length(filelist)){
  print(filelist[f])
  filename <- gsub(".mrxs Detections.txt", "", filelist[f])
  
  initialdata <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  initialdata[is.na(initialdata)] <- 0 #if any "NA" entries, make them "0"

  Positive <- subset(initialdata, initialdata$Class == "Positive")
  Negative <- subset(initialdata, initialdata$Class == "Negative")
  
  class_1 <- subset(Positive, Positive$Cell..DAB.OD.mean <= thresh_33)
  class_2 <- subset(Positive, Positive$Cell..DAB.OD.mean > thresh_33 & Positive$Cell..DAB.OD.mean <= thresh_66)
  class_3 <- subset(Positive, Positive$Cell..DAB.OD.mean > thresh_66)
  
  totCellArea <- (sum(Positive$Cell..Area) + sum(Negative$Cell..Area))/ 1000000
  totCellCount <- (nrow(Positive) + nrow(Negative))
  
  class_1pc <- nrow(class_1) / totCellCount
  class_2pc <- nrow(class_2) / totCellCount
  class_3pc <- nrow(class_3) / totCellCount
  
  DataDraft[k,1] <- filename
  DataDraft[k,2] <- totCellCount
  
  DataDraft[k,3] <- paste(thresh_33, ", ", thresh_66, sep="")
  DataDraft[k,4] <- nrow(class_1)
  DataDraft[k,5] <- class_1pc
  DataDraft[k,6] <- nrow(class_2)
  DataDraft[k,7] <- class_2pc
  DataDraft[k,8] <- nrow(class_3)
  DataDraft[k,9] <- class_2pc
  
  DataDraft[k,10] <- ((1*class_1pc) + (2*class_2pc) + (3*class_3pc))*100
  
  k = k + 1

  print(filelist[f])
}
#write.csv(DataDraft,paste("DataTestingTesting123", k ," ", ".csv"))
write.xlsx(DataDraft, paste("Hscore Data.xlsx"), row.names=FALSE)
