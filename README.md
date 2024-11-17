# Bonsainut Thread To PDF Repository

A tool for downloading **bonsainut.com** threads, including their embeds and images, to your PC. The content is formatted into a **PDF** (and a **HTML** file). Images are supplied in their own subfolder: `/images`.

In the output folder you can see a example for a Thread I've created with it, you can download it if you want and see the results for yourself!

## Getting Started

Follow these steps to set up and run the tool:

### 1. Install Python 3.11
Make sure Python 3.11 is installed on your system.

### 2. Install a Chromium-based Browser
Install a **Chromium-based** browser (preferably **Google Chrome**) on your system.

### 3. Install ChromeDriver (if needed)
This step is only required in some cases. First, try running `main.py` to see if everything works as expected. If it doesn't, you'll need to install **ChromeDriver** for your version of Chrome:

- Visit the official ChromeDriver download page: [ChromeDriver Downloads](https://developer.chrome.com/docs/chromedriver/downloads?hl=en)
- Download the correct version based on your Chrome version.

### 4. Install Required Python Modules
Ensure that the following non-standard Python modules are installed. You can install them using `pip` by running:

```bash
pip install -r requirements.txt
```

### 5. Setup the [config file](config.json):
   -   input your credentials for bonsainut.com, into the fields username & password (these needed in order for the images & embeds in threads to be accessible, they wont be used anywhere but to login to the website and then be able to acess the images).
   -   in the toSave section, input the Threads you want to download, seperate them by comma.
   -   supply the path to your chrome browser in the configuration under chromeExecutable (ps: for most users (windows), this path will probably be: C:/Program Files/Google/Chrome/Application/chrome.exe).
   -   supply wether you want to output a pdf (a html file will always be generated) in the printPdf section:
         -   This option is either set to True or False, however setting it to False will improve performance of the programm DRASTICALLY also the layout and design of the pdf is worse than just viewing the thread as html. The default is set to False, meaning only a html file will get printed

What benefits does it have leaving the printPdf Option to False?
                1. Much faster generation of the Threads
                2. Much smaller File size with HTML compared to the pdf
                3. optimized layout of the HTML file.
                4. On large Threads (with many images and more than 5 pages), the process of creating a pdf can take a couple of minutes
                5. On the html file you have the benefit of beeing able to click on images you want to view enlarged, they will load from the local /images file folder inside the Threads folder in full resolution.

### 6. Run the main.py file, and watch the magic happen...
