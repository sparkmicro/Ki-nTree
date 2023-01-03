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
    new_kicad_sym_file = os.path.join(library_path, symbol + '.kicad_sym')
    if not os.path.exists(new_kicad_sym_file):
        copyfile(template_lib, new_kicad_sym_file)


def download(url, filetype='API data', fileoutput='', timeout=3, enable_headers=False, requests_lib=False, silent=False):
    ''' Standard method to download URL content, with option to save to local file (eg. images) '''

    import socket
    import urllib.request

    # Set default timeout for download socket
    socket.setdefaulttimeout(timeout)
    if enable_headers:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
    try:
        if filetype == 'Image':
            # Enable use of requests library for downloading images (Element14 URLs do NOT work with urllib)
            if requests_lib:
                import requests
                headers = {'User-agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=timeout)
                with open(fileoutput, 'wb') as image:
                    image.write(response.content)
            else:
                (image, headers) = urllib.request.urlretrieve(url, filename=fileoutput)
            return image
        else:
            url_data = urllib.request.urlopen(url)
            data = url_data.read()
            data_json = json.loads(data.decode('utf-8'))
            return data_json
    except socket.timeout:
        cprint(f'[INFO]\tWarning: {filetype} download socket timed out ({timeout}s)', silent=silent)
    except urllib.error.HTTPError:
        cprint(f'[INFO]\tWarning: {filetype} download failed (HTTP Error)', silent=silent)
    except (urllib.error.URLError, ValueError):
        cprint(f'[INFO]\tWarning: {filetype} download failed (URL Error)', silent=silent)
    return None


def download_image(image_url: str, image_full_path: str, silent=False) -> str:
    ''' Standard method to download image URL to local file '''

    if not image_url:
        cprint('[INFO]\tError: Missing image URL', silent=silent)
        return False
    
    # Try without headers
    image = download(image_url, filetype='Image', fileoutput=image_full_path, silent=silent)

    if not image:
        # Try with headers
        image = download(image_url, filetype='Image', fileoutput=image_full_path, enable_headers=True, silent=silent)

    if not image:
        # Try with requests library
        image = download(image_url, filetype='Image', fileoutput=image_full_path, enable_headers=True, requests_lib=True, silent=silent)

    # Still nothing
    if not image:
        return False

    return True
