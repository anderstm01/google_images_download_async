# google_images_download_async
Google Image downloader written in Python 3 using asyncio framework.

This is a rewrite of hardikvasa's [google-images-download ](https://github.com/hardikvasa/google-images-download) using the asyncio framework.

**Not all features have been implemented from the original project.**

## Requirements:
- `Python`==3.7.4
- `aiofiles`==0.4.0
- `aiohttp`==3.6.0

## Usage examples:
Using Config File:
`python google_images_download_async.py -cf user_config.json`

Using Single File:
`python google_images_download_async.py -x 'https://www.python.org/static/opengraph-icon-200x200.png'`

## Options:

|Short form|Long form|Description|
:-: | :-: | :-
| -cf \<path\> | --config_file \<path\> | config file path, if provided indicates to download according to config instead provided arguments |
| -k KEYWORDS | --keywords KEYWORDS | delimited list input |
| -kf \<path\> | --keywords_from_file \<path\> | extract list of keywords from a text file |
| -sk \<k1,k2...\> | --suffix_keywords \<k1,k2...\> | comma separated additional words added after to main keyword|
| -pk \<k1,k2...\> | --prefix_keywords \<k1,k2...\> | comma separated additional words added before main keyword |
| -l LIMIT | --limit LIMIT | delimited list input |
| -f \<format\> | --format \<format\> | download images with specific format |
| -u \<url\> | --url \<url\> | search with google image URL |
| -x \<url\> | --single_image \<url\> | downloading a single image from URL |
| -o \<path\> | --output_directory \<path\> | download images in a specific main directory |
| -i \<path\> | --image_directory \<path\> | download images in a specific sub-directory |
| -n | --no_directory | download images in the main directory but no sub-directory |
| -d \<n\> | --delay \<n\> | delay in seconds to wait between downloading two images |
| -co \<color\> | --color \<color\> | filter on color |
| -ct \<type\> | --color_type \<type\> | filter on color |
| -r \<choice\> | --usage_rights \<choice\> | usage rights |
| -s \<size\> | --size \<size\> | image size |
| -es \<width,height\> | --exact_size \<width,height\> | exact image resolution "WIDTH,HEIGHT" |
| -t \<type\> | --type \<type\> | image type | 
| -w \<age\> | --time \<age\> | image age |
| -wr \<time range\> | --time_range \<time range\> | time range for the age of the image. should be in the format:  {"time_min":"MM/DD/YYYY","time_max":"MM/DD/YYYY"} |
| -a \<aspect\> | --aspect_ratio \<aspect\> | comma separated additional words added to keywords |
| -si \<url\> | --similar_images \<url\> | downloads images very similar to the image URL you provide |
| -ss \<url\> | --specific_site \<url\> | downloads images that are indexed from a specific website |
| -p | --print_urls | Print the URLs of the images |
| -ps | --print_size | Print the size of the images on disk |
| -pp | --print_paths | Prints the list of absolute paths of the images |
| -m | --metadata | Print the metadata of the image |
| -e | --extract_metadata | Dumps all the logs into a text file |
| -st \<n\> | --socket_timeout \<n\> | Connection timeout waiting for the image to download |
| -th | --thumbnail | Downloads image thumbnail along with the actual image |
| -tho | --thumbnail_only | Downloads only thumbnail without downloading actual images |
| -la \<choice\> | --language \<choice\> | Defines the language filter. The search results are authomatically returned in that language |
| -pr \<prefix\> | --prefix \<prefix\> | A word that you would want to prefix in front of each image name |
| -px \<address:port\> | --proxy \<address:port\> | specify a proxy address and port |
| -cd \<path\> | --chromedriver \<path\> | specify the path to chromedriver executable in your local machine |
| -ri | --related_images | Downloads images that are similar to the keyword provided
| -sa | --safe_search | Turns on the safe search filter while searching for images |
| -nn | --no_numbering |Allows you to exclude the default numbering of images | 
| -of \<n\> | --offset \<n\> | Where to start in the fetched links |
| -nd | --no_download | Prints the URLs of the images and/or thumbnails without downloading them |
| -iu \<k1,k2...\> | --ignore_urls \<k1,k2...\> | delimited list input of image urls/keywords to ignore |
| -sil | --silent_mode | Remains silent. Does not print notification messages on the terminal |
| -is \<path\> | --save_source \<path\> | creates a text file containing a list of downloaded images along with source page url |