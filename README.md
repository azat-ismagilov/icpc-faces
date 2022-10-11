# ICPC faces
Automated face recognition system with badge detection

## Contents
1. [Requirements](#requirements)
2. [Installation](#installation)
2. [How to use](#how-to-use)
3. [ICPC Photo Tagging process](#icpc-photo-tagging-process)
4. [Known issues](#known-issues)

## Requirements
- python (3.4+)
- pip
- cmake
- exiftool (12.15+) (for utils) 
- CUDA (if you want to use GPU)

## Installation
```bash
pip3 install -r requirenments.txt
```

### For utils:
```bash
pip3 install -r utils/requirenments.txt
```

## How to use: 
```bash
python3 recognize_teams.py [-h] [--delimiter D] teams_csv input_dir [output_dir] [tags_file]
```

TODO: write instruction with the whole process


## ICPC Photo Tagging process

Goal is to identify as many people on the photos as possible, and for each person mark the corresponsing `Badge name` for further use in the ICPC Gallery [news.icpc.global/gallery](https://news.icpc.global/gallery).

Sources of information are:
* list of all ICPC attendees with their role, institution (for teams ++) and `Badge Name`. Notice, that `Badge Name` may be different from passport first namd and last name. Within ICPC we try to address people as their `Badge Name`.
* [`digikam`](https://www.digikam.org) software that identifies faces on images, finds similar faces and helps organize the photos, add tags and so on
* multiple command line tools for different tagging formats interoperability
* `Azat` badge-to-face detection system for Team Photos.

### `digikam`

The software we suggest to use for photo management is `digikam`. 
When setting up `digikam` it is important to 
* select a folder, where the all photos will be stored
* enable option `store tags in photos`

### Pre-select training data

Core organizer team doesn't change much between years. Prepare a separate folder with core org group photos tagged from last years to help the `digikam` identify people.

### Team Photos -- `Azat`

Another main source of information about specific WF attendees are `Team Photos`. Every team member on the team photo is expected to have a visible badge with `Badge name` and university name printed on them. If you provide `Azat` software with the list of all team members and their correct `badge name`s, the tool will identify almost all faces and corresponding people. It will write the result in a human-readable file for manual check.

Confirmed informationa from file can be then be burned into tags of these photos. Tags will work on both `digiKam` and `Picasa` face detection formats. 

### Adding new events

Photos from every event should be placed in a separate folder. It is also possible to put photos from different photographers into different folders for easier author tagging.

Every time you add a folder to the root `digikam` photo folder, you will need to refresh the list of files in `digikam`. Then run the `people -> detect faces` (skip already scanned photos) and `people - recognize faces` (skip already scanned photos). You will see a list of unknown or unconfirmed recognized faces that need to be confirmed or rejected manually.

When all face tagging for an event is ready, create a new tag with `event$` prefix, for example `event$Opening Ceremony`. Select all new photos in the folder, right-click, select `Assign tag` and select the appropriate tag. Then it will be applied to all selected photos.

Each photo needs to be tagged with a year tag: `album$2021`. 

Then you will need to run a tool `convert_digiKam_to_picasa.py` to embed photo tags from `digikam` into appropriate for icpc `picasa` tagging format.

### Editing tags on Flickr

If a wrong tag was already uploaded to the flickr, they can still be easily edited through flickr interface. Make sure to include quotation marks.

## Known issues
* how to edit photo description to include photographer name?
* university names with special symbols `& ,` can be processed incorrectly
