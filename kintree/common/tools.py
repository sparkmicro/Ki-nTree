import builtins
import json
import os
from shutil import copyfile


# CUSTOM PRINT METHOD
class pcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Overload print function with custom pretty-print


def cprint(*args, **kwargs):
    # Check if silent is set
    try:
        silent = kwargs.pop('silent')
    except:
        silent = False
    if not silent:
        if type(args[0]) is dict:
            return builtins.print(json.dumps(*args, **kwargs, indent=4, sort_keys=True))
        else:
            try:
                args = list(args)
                if 'warning' in args[0].lower():
                    args[0] = f'{pcolors.WARNING}{args[0]}{pcolors.ENDC}'
                elif 'error' in args[0].lower():
                    args[0] = f'{pcolors.ERROR}{args[0]}{pcolors.ENDC}'
                elif 'fail' in args[0].lower():
                    args[0] = f'{pcolors.ERROR}{args[0]}{pcolors.ENDC}'
                elif 'success' in args[0].lower():
                    args[0] = f'{pcolors.OKGREEN}{args[0]}{pcolors.ENDC}'
                elif 'pass' in args[0].lower():
                    args[0] = f'{pcolors.OKGREEN}{args[0]}{pcolors.ENDC}'
                elif 'main' in args[0].lower():
                    args[0] = f'{pcolors.HEADER}{args[0]}{pcolors.ENDC}'
                elif 'skipping' in args[0].lower():
                    args[0] = f'{pcolors.BOLD}{args[0]}{pcolors.ENDC}'
                args = tuple(args)
            except:
                pass
            return builtins.print(*args, **kwargs, flush=True)
###


def create_library(library_path: str, symbol: str, template_lib: str):
    ''' Create library files if they don\'t exist '''
    if not os.path.exists(library_path):
        os.mkdir(library_path)
    new_kicad_sym_file = os.path.join(library_path, f'{symbol}.kicad_sym')
    if not os.path.exists(new_kicad_sym_file):
        copyfile(template_lib, new_kicad_sym_file)


def get_image_with_retries(url, headers, retries=3, wait=5, silent=False):
    """ Method to download image with cloudscraper library and retry attempts"""
    import cloudscraper
    import time
    scraper = cloudscraper.create_scraper()
    for attempt in range(retries):
        try:
            response = scraper.get(url, headers=headers)
            if response.status_code == 200:
                return response
            else:
                cprint(f'[INFO]\tWarning: Image download Attempt {attempt + 1} failed with status code {response.status_code}. Retrying in {wait} seconds...', silent=silent)
        except Exception as e:
            cprint(f'[INFO]\tWarning: Image download Attempt {attempt + 1} encountered an error: {e}. Retrying in {wait} seconds...', silent=silent)
        time.sleep(wait)
    cprint('[INFO]\tWarning: All Image download attempts failed. Could not retrieve the image.', silent=silent)
    return None


def download(url, filetype='API data', fileoutput='', timeout=3, enable_headers=False, requests_lib=False, try_cloudscraper=False, silent=False):
    ''' Standard method to download URL content, with option to save to local file (eg. images) '''

    import socket
    import urllib.request
    import requests

    # A more detailed headers was needed for request to Jameco
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36',
        'Accept': 'applicaiton/json,image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Encoding': 'Accept-Encoding: gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
    }

    # Set default timeout for download socket
    socket.setdefaulttimeout(timeout)
    if enable_headers and not requests_lib:
        opener = urllib.request.build_opener()
        opener.addheaders = list(headers.items())
        urllib.request.install_opener(opener)
    try:
        if filetype == 'PDF':
            # some distributors/manufacturers implement
            # redirects which don't allow direct downloads
            if 'gotoUrl' in url and 'www.ti.com' in url:
                mpn = url.split('%2F')[-1]
                url = f'https://www.ti.com/lit/ds/symlink/{mpn}.pdf'
        if filetype == 'Image' or filetype == 'PDF':
            # Enable use of requests library for downloading files (some URLs do NOT work with urllib)
            if requests_lib:
                response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                if filetype.lower() not in response.headers['Content-Type'].lower():
                    cprint(f'[INFO]\tWarning: {filetype} download returned the wrong file type', silent=silent)
                    return None
                with open(fileoutput, 'wb') as file:
                    file.write(response.content)
            elif try_cloudscraper:
                response = get_image_with_retries(url, headers=headers)
                if filetype.lower() not in response.headers['Content-Type'].lower():
                    cprint(f'[INFO]\tWarning: {filetype} download returned the wrong file type', silent=silent)
                    return None
                with open(fileoutput, 'wb') as file:
                    file.write(response.content)
            else:
                (file, headers) = urllib.request.urlretrieve(url, filename=fileoutput)
                if filetype.lower() not in headers['Content-Type'].lower():
                    cprint(f'[INFO]\tWarning: {filetype} download returned the wrong file type', silent=silent)
                    return None
            return file
        else:
            # some suppliers work with requests.get(), others need urllib.request.urlopen()
            try:
                response = requests.get(url)
                data_json = response.json()
                return data_json
            except requests.exceptions.JSONDecodeError:
                try:
                    url_data = urllib.request.urlopen(url)
                    data = url_data.read()
                    data_json = json.loads(data.decode('utf-8'))
                    return data_json
                finally:
                    pass
    except (socket.timeout, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
        cprint(f'[INFO]\tWarning: {filetype} download socket timed out ({timeout}s)', silent=silent)
    except (urllib.error.HTTPError, requests.exceptions.ConnectionError):
        cprint(f'[INFO]\tWarning: {filetype} download failed (HTTP Error)', silent=silent)
    except (urllib.error.URLError, ValueError, AttributeError):
        cprint(f'[INFO]\tWarning: {filetype} download failed (URL Error)', silent=silent)
    except requests.exceptions.SSLError:
        cprint(f'[INFO]\tWarning: {filetype} download failed (SSL Error)', silent=silent)
    except FileNotFoundError:
        cprint(f'[INFO]\tWarning: {os.path.dirname(fileoutput)} folder does not exist', silent=silent)
    return None


def download_with_retry(url: str, full_path: str, silent=False, **kwargs) -> str:
    ''' Standard method to download image URL to local file '''

    if not url:
        cprint('[INFO]\tError: Missing image URL', silent=silent)
        return False
    
    # Try without headers
    file = download(url, fileoutput=full_path, silent=silent, **kwargs)

    if not file:
        # Try with headers
        file = download(url, fileoutput=full_path, enable_headers=True, silent=silent, **kwargs)

    if not file:
        # Try with requests library
        file = download(url, fileoutput=full_path, enable_headers=True, requests_lib=True, silent=silent, **kwargs)
    
    if not file:
        # Try with cloudscraper
        file = download(url, fileoutput=full_path, enable_headers=True, requests_lib=False, try_cloudscraper=True, silent=silent, **kwargs)

    # Still nothing
    if not file:
        return False

    cprint(f'[INFO]\tDownload success ({url=})', silent=silent)
    return True
