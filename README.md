Welcome to the Bonsainut Thread To PDF repository

A tool for downloading bonsainut.com Thread, its Embeds and Images to your pc, all formated into a pdf (and a HTML file).
Images are supplied in their own subfolder => /images

## Getting started

1. Python 3.11 installed
2. Have a chromium based browser (preferably google chrome) installed.
3. Installing Chromedriver: This step is only required in some cases, you can check if its required for you by first running main.py and checking if everything works as expected, if not this is probably the reason:
   - Wou will need to install the correct chromedriver for your version of chrome, you can do this here: https://developer.chrome.com/docs/chromedriver/downloads?hl=en.
4. Have the following non standard modules installed in python [view required modules](requirements.txt)
5. Have the Repository downloaded to your pc
6. Setup the [config file](config.json):
    - input your credentials for bonsainut.com, into the fields username & password (these needed in order for the images & embeds in threads to be accessible, they wont be used anywhere but to login to the website and then be able to acess the images).
    - in the toSave section, input the Threads you want to download, seperate them by comma.
    - supply the path to your chrome browser in the configuration under chromeExecutable (ps: for most users (windows), this path will probably be: C:/Program Files/Google/Chrome/Application/chrome.exe)
    - supply wether you want to output a pdf (a html file will always be generated) in the printPdf section:
        - This option is either set to True or False, however setting it to False will improve performance of the programm DRASTICALLY also the layout and design of the pdf is worse than just viewing the thread as html. The default is set to False, meaning only a html file will get printed
            
            What benefits does it have leaving the printPdf Option to False?
                1. Much faster generation of the Threads
                2. Much smaller File size with HTML compared to the pdf
                3. optimized layout of the HTML file.
                4. On large Threads (with many images and more than 5 pages), the process of creating a pdf can take a couple of minutes
                5. On the html file you have the benefit of beeing able to click on images you want to view enlarged, they will load from the local /images file folder inside the Threads folder in full resolution.

7. run the main.py file, and let the magic happen.

In the output folder you can see a example for a Thread I've created with it, you can download it if you want and see the results for yourself!
