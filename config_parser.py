# -*- coding: utf-8 -*-
"""
Google_images_download_async config parsing module.
"""

#Builtin imports:
import argparse
import json

async def parse_config():
    '''
    Scope: Reads user defined json config files or parses user provided arguments

    Paramiters: None

    Return: list of dicts that contain the search criteria
    '''
    config = argparse.ArgumentParser(description="google async image downloader")
    config.add_argument('-dflt',
                        '--default_file',
                        help='default file name',
                        default='default_config.json',
                        required=False)
    config.add_argument('-urlp',
                        '--url_parms',
                        help='url parameters',
                        default='url_parms.json',
                        required=False)
    config.add_argument('-cf',
                        '--config_file',
                        help='config file name',
                        required=False)

    args, unknown_args = config.parse_known_args()

    records = []

    if args.config_file:
        with open(args.default_file) as f:
            default_json_file = json.load(f)

        with open(args.config_file) as f:
            config_json_file = json.load(f)

        for i, record in enumerate(config_json_file['Records']):
            records.append(default_json_file.copy())
            records[i].update(record.items())

    else: # this is awful
        parser = argparse.ArgumentParser(description="google async image downloader")
        parser.add_argument('-k', '--keywords', help='delimited list input', type=str, required=False)
        parser.add_argument('-kf', '--keywords_from_file', help='extract list of keywords from a text file', type=str, required=False)
        parser.add_argument('-sk', '--suffix_keywords', help='comma separated additional words added after to main keyword', type=str, required=False)
        parser.add_argument('-pk', '--prefix_keywords', help='comma separated additional words added before main keyword', type=str, required=False)
        parser.add_argument('-l', '--limit', help='delimited list input', type=str, required=False)
        parser.add_argument('-f', '--format', help='download images with specific format', type=str, required=False,
                            choices=['jpg', 'gif', 'png', 'bmp', 'svg', 'webp', 'ico'])
        parser.add_argument('-u', '--url', help='search with google image URL', type=str, required=False)
        parser.add_argument('-x', '--single_image', help='downloading a single image from URL', type=str, required=False)
        parser.add_argument('-o', '--output_directory', help='download images in a specific main directory', type=str, required=False)
        parser.add_argument('-i', '--image_directory', help='download images in a specific sub-directory', type=str, required=False)
        parser.add_argument('-n', '--no_directory', default=False, help='download images in the main directory but no sub-directory', action="store_true")
        parser.add_argument('-d', '--delay', help='delay in seconds to wait between downloading two images', type=int, required=False)
        parser.add_argument('-co', '--color', help='filter on color', type=str, required=False,
                            choices=['red', 'orange', 'yellow', 'green', 'teal', 'blue', 'purple', 'pink', 'white', 'gray', 'black', 'brown'])
        parser.add_argument('-ct', '--color_type', help='filter on color', type=str, required=False,
                            choices=['full-color', 'black-and-white', 'transparent'])
        parser.add_argument('-r', '--usage_rights', help='usage rights', type=str, required=False,
                            choices=['labeled-for-reuse-with-modifications','labeled-for-reuse','labeled-for-noncommercial-reuse-with-modification','labeled-for-nocommercial-reuse'])
        parser.add_argument('-s', '--size', help='image size', type=str, required=False,
                            choices=['large','medium','icon','>400*300','>640*480','>800*600','>1024*768','>2MP','>4MP','>6MP','>8MP','>10MP','>12MP','>15MP','>20MP','>40MP','>70MP'])
        parser.add_argument('-es', '--exact_size', help='exact image resolution "WIDTH,HEIGHT"', type=str, required=False)
        parser.add_argument('-t', '--type', help='image type', type=str, required=False,
                            choices=['face','photo','clipart','line-drawing','animated'])
        parser.add_argument('-w', '--time', help='image age', type=str, required=False,
                            choices=['past-24-hours','past-7-days','past-month','past-year'])
        parser.add_argument('-wr', '--time_range', help='time range for the age of the image. should be in the format {"time_min":"MM/DD/YYYY","time_max":"MM/DD/YYYY"}', type=str, required=False)
        parser.add_argument('-a', '--aspect_ratio', help='comma separated additional words added to keywords', type=str, required=False,
                            choices=['tall', 'square', 'wide', 'panoramic'])
        parser.add_argument('-si', '--similar_images', help='downloads images very similar to the image URL you provide', type=str, required=False)
        parser.add_argument('-ss', '--specific_site', help='downloads images that are indexed from a specific website', type=str, required=False)
        parser.add_argument('-p', '--print_urls', default=False, help="Print the URLs of the images", action="store_true")
        parser.add_argument('-ps', '--print_size', default=False, help="Print the size of the images on disk", action="store_true")
        parser.add_argument('-pp', '--print_paths', default=False, help="Prints the list of absolute paths of the images",action="store_true")
        parser.add_argument('-m', '--metadata', default=False, help="Print the metadata of the image", action="store_true")
        parser.add_argument('-e', '--extract_metadata', default=False, help="Dumps all the logs into a text file", action="store_true")
        parser.add_argument('-st', '--socket_timeout', default=False, help="Connection timeout waiting for the image to download", type=float)
        parser.add_argument('-th', '--thumbnail', default=False, help="Downloads image thumbnail along with the actual image", action="store_true")
        parser.add_argument('-tho', '--thumbnail_only', default=False, help="Downloads only thumbnail without downloading actual images", action="store_true")
        parser.add_argument('-la', '--language', default=False, help="Defines the language filter. The search results are authomatically returned in that language", type=str, required=False,
                            choices=['Arabic','Chinese (Simplified)','Chinese (Traditional)','Czech','Danish','Dutch','English','Estonian','Finnish','French','German','Greek','Hebrew','Hungarian','Icelandic','Italian','Japanese','Korean','Latvian','Lithuanian','Norwegian','Portuguese','Polish','Romanian','Russian','Spanish','Swedish','Turkish'])
        parser.add_argument('-pr', '--prefix', default=False, help="A word that you would want to prefix in front of each image name", type=str, required=False)
        parser.add_argument('-px', '--proxy', help='specify a proxy address and port', type=str, required=False)
        parser.add_argument('-cd', '--chromedriver', help='specify the path to chromedriver executable in your local machine', type=str, required=False)
        parser.add_argument('-ri', '--related_images', default=False, help="Downloads images that are similar to the keyword provided", action="store_true")
        parser.add_argument('-sa', '--safe_search', default=False, help="Turns on the safe search filter while searching for images", action="store_true")
        parser.add_argument('-nn', '--no_numbering', default=False, help="Allows you to exclude the default numbering of images", action="store_true")
        parser.add_argument('-of', '--offset', help="Where to start in the fetched links", type=str, required=False)
        parser.add_argument('-nd', '--no_download', default=False, help="Prints the URLs of the images and/or thumbnails without downloading them", action="store_true")
        parser.add_argument('-iu', '--ignore_urls', default=False, help="delimited list input of image urls/keywords to ignore", type=str)
        parser.add_argument('-sil', '--silent_mode', default=False, help="Remains silent. Does not print notification messages on the terminal", action="store_true")
        parser.add_argument('-is', '--save_source', help="creates a text file containing a list of downloaded images along with source page url", type=str, required=False)

        parser.add_argument('-urlp', '--url_parms', help='url parameters', default='url_parms.json', type=str, required=False)

        args, unknown_args = parser.parse_known_args()
        if unknown_args:
            print(f'The following argument(s) {", ".join(str(unknown_arg) for unknown_arg in unknown_args)} is/are not a recognised and have been bypassed.')

        records.append(vars(args))

    with open(args.url_parms) as file:
        url_parm_json_file = json.load(file)

    return records, url_parm_json_file
