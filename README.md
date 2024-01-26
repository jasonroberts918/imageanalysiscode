# ImageAnalysisCode

-----------------------------------------------------------------------------------------------------------------------------------
Introduction and Usage
-----------------------------------------------------------------------------------------------------------------------------------
The current project is both a repo of code to be used for reference in various softwares and a custom python package designed to handle annotation, detection, and/or shape data exported from QuPath.

**Project structure:**

**/reference_code:** most of this code is not intended to run in your IDE; it is a repo of workflows and snippets that should be used in other software, e.g.:
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
$ git clone git@github.com:jasonroberts918/imageanalysiscode.git
~~~
