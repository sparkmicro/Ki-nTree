# Ki-nTree
#### Fast part creation in [KiCad](https://kicad-pcb.org/) and [InvenTree](https://github.com/inventree/inventree)

<img src="images/doc/kintree_example.png"  width="auto" height="auto">

## Introduction
Ki-nTree (pronounce "Key Entry" or "Ki And Tree") aims to:
* automate part creation of KiCad library parts
* automate part creation of InvenTree parts
* synchronize parts data between KiCad and InvenTree

Ki-nTree works with:
- Digi-Key's **enormous** part database and [free API](https://developer.digikey.com/)
- the awesome open-source [Digi-Key API python library](https://github.com/peeter123/digikey-api) built and maintained by @peeter123
- the awesome open-source [InvenTree Inventory Management System](https://github.com/inventree/inventree) built and maintained by @SchrodingersGat
- [KiCad](https://kicad-pcb.org/) (of course!) and their open-source [library utils](https://github.com/KiCad/kicad-library-utils)

Ki-nTree was developped by @eeintech for [SPARK Microsystems](https://www.sparkmicro.com/), who generously accepted to make it open-source!

## Get Started
### Installation
#### From release package
1. Download the latest release package: [releases](https://github.com/sparkmicro/Ki-nTree/releases)
2. Extract the TGZ file
3. Run `./kintree_gui` in terminal console to run and show output
4. Alternatively, double-click on `kintree_gui` to run it in graphical mode only

#### From source
1. Create and activate a new python environment
2. Clone this repository with the following command:
```
$ git clone --recurse-submodules https://github.com/sparkmicro/Ki-nTree
```
3. Run `pip install -r requirements.txt` to install dependencies
4. Run `python kintree_gui.py` to start using the tool

### Usage Instructions
#### Requirements
* This tool was developped and tested only on a Linux system with Python 3.8.x (should be compatible with Python 3.6+)
* This tool requires a Digi-Key **production** API instance. To create one, go to https://developer.digikey.com/. Create an account, an organization and add a **production** API to your organization. Save both Client ID and Secret keys.

#### Settings
1. With the tool open, click on "Settings > Digi-Key" and fill in both Digi-Key API Client ID and Secret keys
2. Click on "Settings > KiCad", browse to the location where KiCad symbol and footprint libraries are stored on your computer then click "Save"
3. If you intend to use InvenTree with this tool, click on "Settings > InvenTree" and fill in your InvenTree credentials and click "Save"

#### Part Number Search
1. In the main window, enter the part number and click "OK", it will start by fetching part data using the Digi-Key API
2. In the case the Digi-Key API token is not found or expired, a browser window will pop-up. Enter yoiur Digi-Key developper account credentials then login. The following page will appear (`user@email.com` will show your email address):

<img src="images/doc/digikey_api_approval_request.png"  width="800" height="auto">

Click on "Allow", another page will open.  
Click on the "Advanced" button, then click on "Proceed to localhost (unsafe)" at the bottom of the page:

<img src="images/doc/digikey_api_approval_request2.png"  width="800" height="auto">

Lastly, you will get a new page with the "You may now close this window." message, do so to proceed with the search.

3. Once the part data has been successfully fetched from Digi-Key, you will be prompted to confirm/edit the Category and Subcategory in which this part should be saved in (the tool tries to match them automatically but can sometimes fail to do so)  
4. Then, you will be prompted with selecting the symbol library, template and footprint library to use for this part  
5. It will take some time to complete the part creation in InvenTree and KiCad, once done you'll be notified of the result  
6. Finally, if the part was created or found in InvenTree, your browser will be automatically open with the part information

## Roadmap
#### Version 0.2
- [ ] Get more users to try it and release stable version with bug fixes

#### Version 0.3
Main goals: Improve GUI/user input and part synchronization between KiCad and InvenTree

##### Global
- [ ] Inform user of part creation progress in UI and terminal
- [ ] Combine all KiCad templates in a single library file (lib+dcm)

##### GUI
- [ ] Improve cosmetics (!)
- [ ] Show form prefilled with part API search results and allow user edits
- [ ] Add icon to GUI and executable (not successful in 0.2, try with PySimpleGUIQt?)
