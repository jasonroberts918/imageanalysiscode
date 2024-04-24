##find and replace string for all text files in a directory
##ensure your script is in the same root directory as your files directory

import fnmatch
import os

#root directory where subdirectories/files are located
root_directory = r"study/results"

#find and replace string in each text file in root directory
for root, dirnames, filenames in os.walk(root_directory):
  for filename in fnmatch.filter(filenames, '*.txt'):
    with open(os.path.join(root_directory, filename), "r+") as text_file:
        texts = text_file.read()
        texts = texts.replace("resolution #1", "")
    with open(os.path.join(root_directory, filename), "w") as text_file:
        text_file.write(texts)
