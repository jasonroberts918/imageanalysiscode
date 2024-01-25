# ImageAnalysisCode

-----------------------------------------------------------------------------------------------------------------------------------
Introduction and Usage
-----------------------------------------------------------------------------------------------------------------------------------
The current project is both a repo of code to be used for reference in various softwares and a custom python package designed to handle annotation, detection, and/or shape data exported from QuPath.

**Project structure:**

**/my_studies:** tracked files in this directory serve as usage examples for different modules within the qupath_io package. 
             analysts should use this dir to assemble custom analysis scripts based on the qupath_io package. these will not be published to github
             
**/python_experiments:** this code is in development and is not guaranteed to work

**/qupath_io:** a custom package for handling data output by qupath. subpackages include:
- **/data_aggregation:** modules to aggregate per annotation/detection data into a deliverable CSV
- **/data_visualization:** modules to chart study features of interest for exploratory data analysis, QC, or client delivery
- **/shape_utilities:** modules to convert QP shapes (GeoJSON) to format accepted by imageDx (WKT)
- **study.py:** base class to instatiate all studies. takes in annotation and/or detection paths and outputs dict {"image_name": "/path/to/image_name/data"}

**/reference_code:** this code is not intended to run in your IDE; it is a repo of workflows and snippets that should be used in other software, e.g.:
- groovy scripts for use in QP
- command line code for terminal/powershell/cmd

-----------------------------------------------------------------------------------------------------------------------------------
# Installation
-----------------------------------------------------------------------------------------------------------------------------------
## **Before install**
<br /> Ensure github account contains an ssh key to the machine you're working from. Relevant documentation [here](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/checking-for-existing-ssh-keys)
<br /> Ensure python3.8 installed. Check current version from terminal/powershell/cmd:
~~~
$ python --version
~~~
If needed, python downloads can be found [here](https://www.python.org/downloads/)

## **Cloning the repo**
<br /> From terminal/powershell/cmd, navigate to dir where repo should be cloned
<br /> Execute the following:
~~~
$ git clone git@github.com:RevealBio/ImageAnalysisCode.git
~~~

## **Google Authentication**
<br /> In downloading the repo, you should have a credentials file at /ImageAnalysisCode/python-package-reader.json
<br /> This file is needed to download packages private to Reveal from Google's artifact registry.
<br /> Take note of the absolute path of the credentials file, and set an environment variable as follows. 

### <br /> Linux:
~~~
$ nano ~/.bashrc
~~~

<br /> In the file that opens in terminal, scroll to the bottom and add the following:

~~~
$ export GOOGLE_APPLICATION_CREDENTIALS="/insert/path/to/python-package-reader.json"
~~~

<br /> Save the file and exit to return to terminal.
<br /> Update your terminal with the new settings:

~~~
$ source ~/.bashrc
~~~

<br /> You can verify that setting the variable worked by running the following in terminal:

~~~
$ echo $GOOGLE_APPLICATION_CREDENTIALS
~~~
<br /> This should output the path to your credentials file if the environment variable was set up properly.

### <br /> Windows (cmd): <br />
~~~
$ setx GOOGLE_APPLICATION_CREDENTIALS "C:\\insert\path\to\python-package-reader.json"
~~~

### <br /> Windows (powershell):<br />
~~~
$ [Environment]::SetEnvironmentVariable("GOOGLE_APPLICATION_CREDENTIALS", "C:\\insert\path\to\python-package-reader.json", "User")
~~~


## <br /> Two additional python packages are needed before installing qupath_io:

~~~
$ pip install keyring keyrings.google-artifactregistry-auth
~~~


## **Installing the package for development and use**
<br /> Open project root (ImageAnalysisCode) in VSCode (or other IDE) with administrator privileges
<br /> Start an integrated terminal and run all of the following <mark>from project root</mark>:
<br /> Create a virtual environment:
~~~
$ python -m venv qpio_venv
~~~

### <br /> Activate qpio_venv:
#### <br /> Windows:
~~~
$ qpio_venv\Scripts\activate
~~~
#### <br /> Unix:
~~~
$ source qpio_venv/bin/activate
~~~

### <br /> Upgrade pip:
~~~
$ pip install --upgrade pip
~~~

### <br /> Install the package:
~~~
$ pip install -e .
~~~

<br /> Note that this command will likely fail on the first run.
<br /> Run the above a second time, and it should succeed. 
<br /> If not, there is another installation issue that needs to be resolved.



