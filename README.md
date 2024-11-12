Welcome to the Bonsainut Thread To PDF repository

A tool for downloading bonsainut.com Thread, its Embeds and Images to your pc, all formated into a pdf (and a HTML file).
Images are supplied in their own subfolder (/images)

## Getting started

1. Python 3.11 installed
2. Have the following non standard modules installed in python [view required modules](requirements.txt)
3. Have the Repository downloaded to your pc
4. Setup the [config file](config.json):
    - with your credentials for bonsainut.com (needed in order for the images to be accessible in good resolution, they wont be used anywhere but to login to the website and be able to access images)
    - in the toSave section, input the Threads you want to download, seperate them by comma.
5. run the main.py file, and let the magic happen.

The process can take a bite of time, however in your console output, reasonable breakpoints will be output, for you to track progress better.