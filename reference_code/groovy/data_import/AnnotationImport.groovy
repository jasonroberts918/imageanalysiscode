
def file_name = getProjectEntry().getImageName()[0..-6]+".txt"
def path = buildFilePath(PROJECT_BASE_DIR, 'annotations', file_name)
def annotations = null
new File(path).withObjectInputStream {
    annotations = it.readObject()
}
addObjects(annotations)
print 'Added ' + annotations
