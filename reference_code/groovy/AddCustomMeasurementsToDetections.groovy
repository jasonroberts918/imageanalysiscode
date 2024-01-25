//Generating measurements in detections from other measurements created in QuPath
//0.1.2 and 0.2.0
detections = getDetectionObjects()

detections.each{
    nucMaxCytoplasmMaxRatioCh1 = measurement(it, "Nucleus: Channel 1 max")/measurement(it, "Cytoplasm: Channel 1 max")
    it.getMeasurementList().putMeasurement("nucMaxCytoplasmMaxRatioCh1", nucMaxCytoplasmMaxRatioCh1)
}

detections.each{
    nucMinCytoplasmMinRatioCh1 = measurement(it, "Nucleus: Channel 1 min")/measurement(it, "Cytoplasm: Channel 1 min")
    it.getMeasurementList().putMeasurement("nucMinCytoplasmMinRatioCh1", nucMinCytoplasmMinRatioCh1)
}
println("done")
