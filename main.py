### bonsainut.com thread to pdf, @raffaelbaer ###

import os
import io
import re
import json
import shutil
import hashlib
import asyncio
import requests
from PIL import Image
from pyppeteer import launch
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC

def validateConfigurationFile(config):    
    username = config['configuration']['username'].strip()
    password = config['configuration']['password'].strip()
    chromeExecutable = config['chromeExecutable']['value'].strip()
    printPdf = config['printPdf']['value']
    
    toSave = config['toSave']
    
    if username is None or not isinstance(username, str):
        raise Exception('Username specified in configuration file not valid, please correct.')
    
    if password is None or not isinstance(password, str):
        raise Exception('Password specified in configuration file not valid, please correct.')
    
    if chromeExecutable is None or not isinstance(chromeExecutable, str):
        raise Exception('Chrome Executable in configuration file not valid, please correct.')
    else:
        if not os.path.exists(chromeExecutable):
            raise Exception('Path to Chrome Executable in configuration file doesnt exist, please correct.')
        
    if printPdf is None or not isinstance(printPdf, bool):
        raise Exception('printPdf option in configuration file not valid, please correct.')
    
    if len(toSave) == 0:
        raise Exception('No urls to save where specified in the configuration file.')
    else:
        for url in toSave:
            if not isinstance(url, str) or not 'www.bonsainut.com' in url:
                raise Exception(f'Invalid thread url ({url}) specified in configuration file.')
            
            toSaveUrls.append(url.strip())
        
    return (username, password, chromeExecutable, printPdf)

def initializeChromeDriver():
    chromeOptions = Options()
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--disable-in-process-stack-traces")
    chromeOptions.add_argument("--disable-logging")
    chromeOptions.add_argument("window-size=1920,1280")
    chromeOptions.add_argument("--ignore-certificate-errors")
    chromeOptions.add_argument("--incognito")
    chromeOptions.add_argument("--no-sandbox")
    chromeOptions.add_argument("--disable-dev-shm-usage")
    chromeOptions.add_argument('--headless')
    chromeOptions.add_argument("--log-level=3")
    
    chromeOptions.set_capability('goog:loggingPrefs', {
        'driver': 'OFF',
        'browser': 'OFF',
        'performance': 'OFF'
    })
    
    return webdriver.Chrome(options=chromeOptions)

def consentCookies(driver):
    try:
        cookieBannerConsentButton = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.fc-cta-consent')))
        cookieBannerConsentButton.click()
    except (TimeoutException, NoSuchElementException) as e:
        pass

def generatePostElementHtml(username, datetime, postId, content, attachmentsList, xf_sessionCookie, savePath, compressedImagesPath): 
    def generateIdentifier(input):        
        hash_object = hashlib.sha256(input.encode())
        hex_digest = hash_object.hexdigest()
        return hex_digest[:6]
    
    def download_image(attachment, operationFor):
        name, link = attachment
        
        #handling images with same name...

        filePathName = f'{savePath}/{postId.strip("#")}-{name}'
        randomIdentifier = generateIdentifier(link)
            
        localLink = f'images/compressed/{postId.strip("#")}-{randomIdentifier}-{name}'
        localLink_uncompressed = f'images/{postId.strip("#")}-{randomIdentifier}-{name}'
        filePathName = f'{savePath}/{postId.strip("#")}-{randomIdentifier}-{name}'
        name = f'{randomIdentifier}-{name}'  
        
        try:
            cookies = {
                "xf_session": xf_sessionCookie,
            }

            response = requests.get(link, cookies=cookies, stream=True)

            if response.status_code == 403:
                raise Exception(f"Could not load image {name} from {link}, status code 403.")
            elif response.status_code == 200:
                os.makedirs(os.path.dirname(filePathName), exist_ok=True)
                
                imageData = io.BytesIO()
                
                with open(filePathName, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                        imageData.write(chunk)  
                
                def downloadAndOptimizeImages(quality):
                    compressedImagesFilePath = f'{compressedImagesPath}/{postId.strip("#")}-{name}'
                    os.makedirs(os.path.dirname(compressedImagesFilePath), exist_ok=True)
                    imageData.seek(0)
                    
                    with Image.open(imageData) as img:
                        if (operationFor == 'attachment'):
                            original_width, original_height = img.size
                            target_width = 400

                            if original_width > target_width:
                                aspect_ratio = original_height / original_width
                                target_height = int(target_width * aspect_ratio)

                                img = img.resize((target_width, target_height), Image.LANCZOS)
                        
                        with open(compressedImagesFilePath, 'wb') as optimized_file:
                            img.save(optimized_file, quality=quality, optimize=True)
                                
                downloadAndOptimizeImages(30)
                
                if operationFor == 'attachment':
                    return f'''
                        <a class="attachment" style="background-image: url('{localLink}')" href="{localLink_uncompressed}">
                            <h3>{name}</h3>
                        </a>
                    '''
                    
        except Exception as e:
            raise Exception(f"Couldnt download Image {name}: {e}")

    def download_attachments(attachmentsList, operationFor):
        attachmentsHtml = ''
        
        with ThreadPoolExecutor() as executor:
            results = executor.map(lambda attachment: download_image(attachment, operationFor), attachmentsList)
        
        for result in results:
            if result:
                attachmentsHtml += result
    
        return attachmentsHtml 
    
    attachmentsHtml = download_attachments(attachmentsList, 'attachment')
    
    if len(attachmentsList) > 0:
        attachmentsHtml = f'''
        <h3 style="margin-top: 1.75rem">Attachments</h3>
        <div class="attachments">
        {attachmentsHtml}
        </div>
        '''
    else:
        attachmentsHtml = ''
        
    #getting embeded images, and also saving them in images folder
    
    def download_embeds(embeddedImagesList, operationFor):
        with ThreadPoolExecutor() as executor:
            executor.map(lambda embed: download_image(embed, operationFor), embeddedImagesList)
    
    soup = BeautifulSoup(content, 'lxml')
    embeddedImages = soup.select('.js-lbImage > img')
    externalImageEmbeds = soup.select('.link.link--external > img')
    
    embeddedImagesList = []
    
    def downloadAllEmbedsFor(embeddedImagesList, embedsElement, imageWrapperClass):
        if len(embedsElement) > 0:
            for img in embedsElement:
                src = img.get('src')
                
                if '/proxy' in src:
                    src = f'https://www.bonsainut.com/{img.get("src")}'

                if img['width'] and int(img['width']) < 350:
                    img['width'] = 'auto'

                imageWrapper = img.find_parent(class_=imageWrapperClass)

                if imageWrapper:
                    #replacing downscaled attachments with their full resolution counterparts, by modifying uri

                    if '/data/attachments/' in src:
                        src = imageWrapper.get('href')

                    randomIdentifier = generateIdentifier(src)
                    
                    name = img.get('title') or img.get('alt')
                    
                    if not name:
                            name = f'{randomIdentifier}.jpeg'
                            
                    name = generateFileAndFolderSaveName(re.sub(r'\s+', '', name))
                    base_name, ext = os.path.splitext(name)
                    
                    if bool(re.search(r'\d', ext)) or not ext:
                        ext = '.jpeg'
                        name = base_name + ext
                    
                    img['src'] = f'images/compressed/{postId.strip("#")}-{randomIdentifier}-{name}'
                    imageWrapper['href'] = f'images/{postId.strip("#")}-{randomIdentifier}-{name}'

                    h3 = soup.new_tag('h3')
                    h3.string = f'{name}'

                    imageWrapper.append(h3)

                    linkElement = soup.new_tag('a')
                    linkElement.attrs = imageWrapper.attrs
                    linkElement.extend(imageWrapper.contents)
                    imageWrapper.replace_with(linkElement)

                embeddedImagesList.append((name, src))
            
            download_embeds(embeddedImagesList, 'embed')

    downloadAllEmbedsFor(embeddedImagesList, embeddedImages, 'js-lbImage')
    downloadAllEmbedsFor(embeddedImagesList, externalImageEmbeds, 'link--external')
        
    
    if len(attachmentsList) > 0 or len(embeddedImages) > 0 or len(externalImageEmbeds) > 0:
        postClassname = 'post'
    elif len(attachmentsList) == 0 and len(embeddedImages) == 0 and len(externalImageEmbeds) == 0:
        postClassname = 'post noAttachments'
    
    content = str(soup)
    
    return f'''
    <section class="{postClassname}">
        <div class="postinfo">
            <h3 class="postid">{postId}</h3>
            <h3 class="username">@{username}</h3>
            <h4 class="datetime">{datetime}</h3>
        </div>
        <div class="postcontent">
            <div>{content}</div>
            {attachmentsHtml}
        </div>
    </section>
    '''

def clearThenLogConsole(msg):
    if os.name == 'nt':
        os.system('cls')
        print(msg)
    else:
        os.system('clear')
        print(msg)
        
def generateFileAndFolderSaveName(string):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F#]', '_', string)[:255].strip()

try:
    with open('config.json', 'r') as file:
        try:
            config = json.load(file)
        except json.JSONDecodeError:
            raise

    toSaveUrls = []
    username, password, chromeExecutable, printPdf = validateConfigurationFile(config)
    
    driver = initializeChromeDriver()
    
    driver.get('https://www.bonsainut.com/login')
    
    clearThenLogConsole('validated configuration file, starting process')
        
    consentCookies(driver)
    
    usernameInput = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="login"][autocomplete="username"]')))
    usernameInput.send_keys(username)
    
    passwordInput = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="password"]')))
    passwordInput.send_keys(password)
    
    submitButton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"].button--icon--login')))
    submitButton.click()
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.blockMessage.blockMessage--error')))
        raise Exception("Login failed due to probably incorrect credentials")
    except (TimeoutException, NoSuchElementException):
        pass
    
    #extracting session cookie, in order to make downloading images possible, @raffaelbaer
    
    try:
        xf_sessionCookie = driver.get_cookie('xf_session')
        
        xf_sessionCookieComplete = xf_sessionCookie
        xf_sessionCookie = xf_sessionCookie.get('value')
        
        if not xf_sessionCookie:
            raise Exception('No xf_sessionCookie found, needed for downloading images and embeds properly!')
    except Exception as e:
        raise
    
    for index, threadUrl in enumerate(toSaveUrls):
        defaultPrintStatement = f'Thread {index+1}/{len(toSaveUrls)}:'
        clearThenLogConsole(f'{defaultPrintStatement} starting download process')
        
        postsHtml = []
                
        driver.get(threadUrl)
        
        consentCookies(driver)
        
        pagesLength = 0
        
        try:
            navigation = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.pageNav')))
            navigation = navigation[0]
            
            pagesLength = WebDriverWait(navigation, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li:last-child')))
            pagesLength = int(pagesLength.text.strip())
        except Exception as e:
            pagesLength = 1
            
        threadName = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.p-body-header .p-title-value')))
        threadName = threadName.text.strip()
        
        threadCreator = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.p-description .username')))
        threadCreator = threadCreator.text.strip()
        
        threadTime = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.p-description time.u-dt')))
        threadTime = threadTime.get_attribute('title').strip()
        
        threadId = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'html')))
        threadId = threadId.get_attribute('data-content-key').strip().lstrip('thread-')
        
        outputFilename = generateFileAndFolderSaveName(threadName)
        pdfOutputPathName = f'Thread-{threadId}-{outputFilename}'
        pdfOutputPath = f'output/{pdfOutputPathName}'
        os.makedirs(pdfOutputPath, exist_ok=True)
        
        imagesOutputPath = f'output/{pdfOutputPathName}/images'
        compressedImagesPath = f'output/{pdfOutputPathName}/images/compressed'
        
        for index, page in enumerate(range(pagesLength)):
            clearThenLogConsole(f'{defaultPrintStatement} getting Page {index+1}/{pagesLength}')
            posts = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.message--post .message-inner')))
            
            for post in posts:
                try:
                    attachmentsList = [] #placement ensures the correct clearing of the array, @raffaelbaer
                    
                    username = WebDriverWait(post, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.message-userDetails h4.message-name')))
                    username = username.text.strip()
                    
                    datetime = WebDriverWait(post, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'time.u-dt')))
                    datetime = datetime.get_attribute("title").strip()
                    
                    postId = WebDriverWait(post, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.message-attribution-opposite--list > li:last-child > a')))
                    postId = postId.text.strip()
                    
                    content = WebDriverWait(post, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.message-body .bbWrapper')))
                    content = content.get_attribute('outerHTML')
                    
                    attachments = WebDriverWait(post, 0.5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'section.message-attachments .attachmentList > li')))
                    
                    for attachment in attachments:
                        attachmentLink = WebDriverWait(attachment, 0).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'section.message-attachments .attachmentList > li > a.file-preview')))
                        attachmentLink = attachmentLink.get_attribute("href").strip()
                        
                        attachmentName = WebDriverWait(attachment, 0).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'section.message-attachments .attachmentList > li > div.file-content .file-info > .file-name')))
                        attachmentName = attachmentName.text.strip()
                        
                        attachmentsList.append((attachmentName, attachmentLink))
                    
                    postsHtml.append(generatePostElementHtml(username, datetime, postId, content, attachmentsList, xf_sessionCookie, imagesOutputPath, compressedImagesPath))
                except (TimeoutException, NoSuchElementException) as e:
                    postsHtml.append(generatePostElementHtml(username, datetime, postId, content, attachmentsList, xf_sessionCookie, imagesOutputPath, compressedImagesPath))
            
            if (pagesLength > 1 and page != pagesLength-1):
                navigationNext = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.pageNav .pageNav-jump.pageNav-jump--next')))
                navigationNext.click()
        
        clearThenLogConsole(f'{defaultPrintStatement} finished scraping, now writing to pdf, finishing download of thread soon')
        
        postsHtml = '\n'.join([f'{post}' for post in postsHtml])
        
        threadHtml = f'''
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
            </head>
            <style>
                    * {{
                        box-sizing: border-box;
                        padding: 0;
                        margin: 0;
                        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                        scroll-behavior: smooth;
                        text-rendering: optimizeLegibility;
                        -webkit-font-smoothing: subpixel-antialiased;
                    }}
                    
                    html {{
                        margin: 15px;
                    }}
                    
                    img.smilie.smilie--emoji {{
                        width: 20px;
                        height: 20px;
                        vertical-align: text-bottom;
                    }}
                    
                    .post {{
                        display: flex;
                        flex-direction: column;
                        gap: 0.75rem;
                        border: 1px solid #d9d9d9;
                        box-shadow: 2px 2px 10px 3px #fdfdfd;
                        border-radius: 10px;
                        margin-top: 1rem;
                        padding: 1rem;
                    }}
                    
                    .post.noAttachments {{
                        page-break-inside: avoid;
                    }}
                    
                    .postinfo {{
                        display: flex;
                        gap: 1rem;
                        align-items: center;
                    }}
                    
                    h1, h2, h3, h4, h5, h6 {{
                        color: #1f2124;
                    }}
                    
                    p, a, div, span {{
                        color: #3c3c3c;
                    }}
                    
                    .postcontent {{
                        flex: 1;
                    }}
                    
                    header .subheading {{
                        color: #3c3c3c;
                    }}
                    
                    header {{
                        padding: 1rem;
                        border: 3px solid #13c564;
                        background: #f9f9f9;
                        border-radius: 10px;
                        box-shadow: 2px 2px 10px 3px #fdfdfd;
                    }}
                    
                    .post .datetime {{
                        font-weight: 400;
                        color: #3c3c3c;
                    }}
                    
                    header .mainheading {{
                        margin-bottom: 0.5rem;
                    }}
                
                    .attachments {{
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                        gap: 0.5rem;
                        margin-top: 0.75rem;
                    }}
                
                    .attachment {{
                        border-radius: 10px;
                        height: 250px;
                        background-size: cover;
                        background-position: center center;
                        background-repeat: no-repeat;
                        display: flex;
                        align-items: flex-end;
                        
                    }}
                    
                    .attachment > h3 {{
                        background: #10101094;
                        width: 100%;
                        border: none;
                        border-radius: 0px 0px 10px 10px;
                        padding: 0.75rem;
                        color: white;
                        word-break: break-all;
                    }}
                    
                    blockquote.bbCodeBlock {{
                        padding: 0.5rem;
                        border: 2px solid #13c564;
                        border-radius: 5px;
                        background: #f9f9f9;
                        margin-block: 0.75rem;
                    }}
                    
                    blockquote.bbCodeBlock .bbCodeBlock-title {{
                        font-size: 1.1em;
                        font-weight: 600;
                        margin-bottom: 0.5rem;
                    }}
                    
                    blockquote.bbCodeBlock .bbCodeBlock-expandLink {{
                        display: none;
                    }}
                    
                    .postcontent .bbWrapper .js-lbImage > img,
                    .postcontent .link.link--external > img {{
                        max-width: 500px;
                        height: auto;
                        border-radius: 10px;
                    }}
                    
                    .postcontent .bbWrapper .js-lbImage,
                    .postcontent .link.link--external {{
                        margin-bottom: 0.5rem;
                        position: relative;
                        width: fit-content;
                        display: flex;
                    }}
                    
                    .postcontent .bbWrapper .js-lbImage > h3,
                    .postcontent .link.link--external > h3 {{
                        background: #10101094;
                        width: 100%;
                        border: none;
                        border-radius: 0px 0px 10px 10px;
                        padding: 0.75rem;
                        color: white;
                        position: absolute;
                        bottom: 0;
                        word-break: break-all;
                    }}
            </style>
            <body>
            <header>
                <h1 class="mainheading">{threadName}</h1>
                <h3 class="subheading">By user: @{threadCreator}</h2>
                <h3 class="subheading">Created at: {threadTime}</h2>
                <h3 class="subheading">ThreadId: {threadId}</h2>
            </header>
            {postsHtml}
            </body>
        </html>
        '''
        
        pdfOutputFileName = pdfOutputPathName
            
        async def generateThreadPdf(htmlPath, pdfOutputPathFile, pdfOutputFileName):
            browser = await launch(
                headless=True,
                executablePath=chromeExecutable
                )
            page = await browser.newPage()
            await page.goto(f'file://{os.path.abspath(htmlPath)}', {'timeout': 0})
            await page.evaluate(f'document.title = "{pdfOutputFileName}"')
            await page.evaluate('''
                document.querySelectorAll('img[loading="lazy"]').forEach(function(img) {
                    img.removeAttribute('loading');
                });
            ''')
            await page.waitForFunction('document.querySelector("img").complete === true')
            await page.pdf({
                'path': f'{pdfOutputPathFile}.pdf',
                'format': 'A4',
                'margin': {
                    'top': '5mm',
                    'right': '5mm',
                    'bottom': '5mm',
                    'left': '5mm'
                },
                'printBackground': True,
            })
            await browser.close()
         
        htmlFilePath = f'{pdfOutputPath}/{pdfOutputFileName}.html'
            
        with open (htmlFilePath, 'w', encoding='utf-8') as file:
            file.write(threadHtml)
        
        if printPdf == True:
            asyncio.get_event_loop().run_until_complete(generateThreadPdf(f'{htmlFilePath}', f'{pdfOutputPath}/{pdfOutputFileName}', pdfOutputFileName))
        
        clearThenLogConsole(f'{defaultPrintStatement} finished download of thread!')

except Exception as e:
    print(e)
    
finally:
    try:
        if driver:
            driver.quit()
    except NameError as e:
        pass