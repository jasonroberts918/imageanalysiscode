#Change path here, this is where your data is
#Writes a csv file with the data in the path

#The data was acquired by running the export script on "Live" Images
#So have the positive pixel class you are happy with running Live and viewable
#Give it a second to load
#Then run the export
#Repeat for each slide 

path.ano = "C://Analysis_Studies//24-106 Ventoux Bio//24-106 Ventoux QP//annotation results_fibrosis"

setwd(path.ano)
#Tells it to look for all .txt files in the path given above
filelist <- dir(path.ano,pattern = ".txt")


#Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft <- data.frame(matrix(ncol = 6))

k = 1

#For loop, for every file ending in .txt in that path, we will run through this loop of calculations once.  
for(f in 1:length(filelist)){
  filename = gsub(".mrxs.txt", "", filelist[f])
  
  #Declare some tables for data
  Read.Data <- data.frame()
  
  #This line reads the .txt file and places it into a table we can look at
  Read.Data <- read.table(filelist[f], header=T, sep="\t", fill = TRUE)
  
  # find unique region/section names in detections Name column
  regionNames <- unique(Read.Data$Name)
  print("Region names found: ")
  print(regionNames)
  
  
  # iterate over each region, aggregating data for each individually
  for(regionName in regionNames){
    if(regionName == 'Dermis' | regionName == 'Epidermis' ){
  
      Read.Data.region <- subset(Read.Data, Read.Data$Name == regionName)
      positive_area_mm <- sum(Read.Data.region$X24.106.MTC.Classifier..Positive.area.Âµm.2) / 1000000
    
      annotation_area <- sum(Read.Data.region$Area.Âµm.2) / 1000000
      negative_area_mm <- annotation_area - positive_area_mm
      
      DataDraft[k,1] <- filename
      DataDraft[k,2] <- regionName
      DataDraft[k,3] <- positive_area_mm 
      DataDraft[k,4] <- (positive_area_mm / annotation_area) * 100
      DataDraft[k,5] <- negative_area_mm 
      DataDraft[k,6] <- (negative_area_mm / annotation_area) * 100
      DataDraft[k,7] <- annotation_area
      print(filelist[f])
      
      k = k + 1
    }
  }
}

colnames(DataDraft) <- c("Filename",
                         "Region",
                         "Positive Area (mm^2)",
                         "Positive Area Percentage (%)", #cell counts per total cell area
                         "Negative Area (mm^2)",
                         "Negative Area Percentage (%)",
                         "Total Area Analyzed (mm^2)")

write.csv(DataDraft,paste("Fibrosis Data",f,".csv"), row.names = FALSE)

