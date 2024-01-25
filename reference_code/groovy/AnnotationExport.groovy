
def file_name = getProjectEntry().getImageName()[0..-6]+".txt" //removed the '.mrxs' extension which makes name matching with detection file easier
print(file_name)
def path = buildFilePath(PROJECT_BASE_DIR, 'annotations', file_name)
def annotations = getAnnotationObjects()
print(annotations)
new File(path).withObjectOutputStream {
    it.writeObject(annotations)
}
print 'Done!'
