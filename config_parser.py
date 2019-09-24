# -*- coding: utf-8 -*-
"""
Google_images_download_async config parsing module.
"""

# Builtin imports:
import argparse
import json
import os
from pathlib import Path


async def parse_config():
    """
    Reads user defined json config files or parses user provided arguments.

    Return: list of dicts that contain the search criteria
    """
    parser = argparse.ArgumentParser(prog='google_async_image_downloader.py',
                                     description='Downloads images from google images.',
                                     epilog='NOTE: Not all above options has been implemented.')

    parser.add_argument('-cf',
                        '--config_file',
                        help='''config file path, if provided indicates to
                            download according to config instead provided arguments''',
                        metavar='<path>')

    parser.add_argument('-k', '--keywords',
                        help='delimited list input')
    parser.add_argument('-kf', '--keywords_from_file',
                        help='extract list of keywords from a text file',
                        metavar='<path>')
    parser.add_argument('-sk', '--suffix_keywords',
                        help='comma separated additional words added after to main keyword',
                        metavar='<k1,k2...>')
    parser.add_argument('-pk', '--prefix_keywords',
                        help='comma separated additional words added before main keyword',
                        metavar='<k1,k2...>')
    parser.add_argument('-l', '--limit',
                        default=1,
                        help='delimited list input')
    parser.add_argument('-f', '--format',
                        help='download images with specific format',
                        choices=['jpg', 'gif', 'png', 'bmp', 'svg', 'webp', 'ico'],
                        metavar='<format>')
    parser.add_argument('-u', '--url',
                        help='search with google image URL',
                        metavar='<url>')
    parser.add_argument('-x', '--single_image',
                        help='downloading a single image from URL',
                        metavar='<url>')
    parser.add_argument('-o', '--output_directory',
                        help='download images in a specific main directory',
                        metavar='<path>')
    parser.add_argument('-i', '--image_directory',
                        help='download images in a specific sub-directory',
                        metavar='<path>')
    parser.add_argument('-n', '--no_directory',
                        help='download images in the main directory but no sub-directory',
                        action="store_true")
    parser.add_argument('-d', '--delay',
                        type=int,
                        help='delay in seconds to wait between downloading two images',
                        metavar='<n>')
    parser.add_argument('-co', '--color',
                        choices=['red', 'orange', 'yellow', 'green', 'teal', 'blue',
                                 'purple', 'pink', 'white', 'gray', 'black', 'brown'],
                        help='filter on color',
                        metavar='<color>')
    parser.add_argument('-ct', '--color_type',
                        choices=['full-color', 'black-and-white', 'transparent'],
                        help='filter on color',
                        metavar='<type>')
    parser.add_argument('-r', '--usage_rights',
                        choices=['labeled-for-reuse-with-modifications',
                                 'labeled-for-reuse',
                                 'labeled-for-noncommercial-reuse-with-modification',
                                 'labeled-for-nocommercial-reuse'],
                        help='usage rights',
                        metavar='<choice>')
    parser.add_argument('-s', '--size',
                        choices=['large', 'medium', 'icon', '>400*300', '>640*480', '>800*600',
                                 '>1024*768', '>2MP', '>4MP', '>6MP', '>8MP', '>10MP', '>12MP',
                                 '>15MP', '>20MP', '>40MP', '>70MP'],
                        help='image size',
                        metavar='<size>')
    parser.add_argument('-es', '--exact_size',
                        help='exact image resolution "WIDTH,HEIGHT"',
                        metavar='<width,height>')
    parser.add_argument('-t', '--type',
                        choices=['face', 'photo', 'clipart', 'line-drawing', 'animated'],
                        help='image type',
                        metavar='<type>')
    parser.add_argument('-w', '--time',
                        choices=['past-24-hours', 'past-7-days', 'past-month', 'past-year'],
                        help='image age',
                        metavar='<age>')
    parser.add_argument('-wr', '--time_range',
                        help='''time range for the age of the image. should be in the format
                            {"time_min":"MM/DD/YYYY","time_max":"MM/DD/YYYY"}''',
                        metavar='<time range>')
    parser.add_argument('-a', '--aspect_ratio',
                        choices=['tall', 'square', 'wide', 'panoramic'],
                        help='comma separated additional words added to keywords',
                        metavar='<aspect>')
    parser.add_argument('-si', '--similar_images',
                        help='downloads images very similar to the image URL you provide',
                        metavar='<url>')
    parser.add_argument('-ss', '--specific_site',
                        help='downloads images that are indexed from a specific website',
                        metavar='<url>')
    parser.add_argument('-p', '--print_urls',
                        action="store_true",
                        help="Print the URLs of the images")
    parser.add_argument('-ps', '--print_size',
                        action="store_true",
                        help="Print the size of the images on disk")
    parser.add_argument('-pp', '--print_paths',
                        action="store_true",
                        help="Prints the list of absolute paths of the images")
    parser.add_argument('-m', '--metadata',
                        action="store_true",
                        help="Print the metadata of the image")
    parser.add_argument('-e', '--extract_metadata',
                        action="store_true",
                        help="Dumps all the logs into a text file")
    parser.add_argument('-st', '--socket_timeout',
                        type=float,
                        help="Connection timeout waiting for the image to download",
                        metavar='<n>')
    parser.add_argument('-th', '--thumbnail',
                        action="store_true",
                        help="Downloads image thumbnail along with the actual image")
    parser.add_argument('-tho', '--thumbnail_only',
                        action="store_true",
                        help="Downloads only thumbnail without downloading actual images")
    parser.add_argument('-la', '--language',
                        default=False,
                        choices=['Arabic', 'Chinese (Simplified)', 'Chinese (Traditional)',
                                 'Czech', 'Danish', 'Dutch', 'English', 'Estonian', 'Finnish',
                                 'French', 'German', 'Greek', 'Hebrew', 'Hungarian', 'Icelandic',
                                 'Italian', 'Japanese', 'Korean', 'Latvian', 'Lithuanian',
                                 'Norwegian', 'Portuguese', 'Polish', 'Romanian', 'Russian',
                                 'Spanish', 'Swedish', 'Turkish'],
                        help='''Defines the language filter. The search results
                            are authomatically returned in that language''',
                        metavar='<choice>')
    parser.add_argument('-pr', '--prefix',
                        default=False,
                        help="A word that you would want to prefix in front of each image name",
                        metavar='<prefix>')
    parser.add_argument('-su', '--suffix',
                        default=False,
                        help="A word that you would want to add to the end of each image name",
                        metavar='<suffix>')
    parser.add_argument('-px', '--proxy',
                        help='specify a proxy address and port',
                        metavar='<address:port>')
    parser.add_argument('-cd', '--chromedriver',
                        help='specify the path to chromedriver executable in your local machine',
                        metavar='<path>')
    parser.add_argument('-ri', '--related_images',
                        action="store_true",
                        help="Downloads images that are similar to the keyword provided")
    parser.add_argument('-sa', '--safe_search',
                        action="store_true",
                        help="Turns on the safe search filter while searching for images")
    parser.add_argument('-nn', '--no_numbering',
                        action="store_true",
                        help="Allows you to exclude the default numbering of images")
    parser.add_argument('-of', '--offset',
                        help="Where to start in the fetched links",
                        metavar='<n>')
    parser.add_argument('-nd', '--no_download',
                        action="store_true",
                        help='''Prints the URLs of the images and/or thumbnails without
                            downloading them''')
    parser.add_argument('-iu', '--ignore_urls',
                        default=False,
                        help="delimited list input of image urls/keywords to ignore",
                        metavar='<k1,k2...>')
    parser.add_argument('-sil', '--silent_mode',
                        action="store_true",
                        help="Remains silent. Does not print notification messages on the terminal")
    parser.add_argument('-is', '--save_source',
                        help='''creates a text file containing a list of downloaded images
                            along with source page url''',
                        metavar='<path>')

    args, unknown_args = parser.parse_known_args()

    if unknown_args:
        print('The following argument(s):',
              f'{", ".join(str(unknown_arg) for unknown_arg in unknown_args)} ',
              'is/are not a recognised and have been bypassed.')

    records = []

    if args.config_file:
        default_args = ["keywords", "keywords_from_file", "prefix_keywords", "suffix_keywords",
                        "limit", "format", "color", "color_type", "usage_rights", "size",
                        "exact_size", "aspect_ratio", "type", "time", "time_range", "delay", "url",
                        "single_image", "output_directory", "image_directory", "no_directory",
                        "proxy", "similar_images", "specific_site", "print_urls", "print_size",
                        "print_paths", "metadata", "extract_metadata", "socket_timeout",
                        "thumbnail", "thumbnail_only", "language", "prefix", "suffix", "chromedriver",
                        "related_images", "safe_search", "no_numbering", "offset", "no_download",
                        "save_source", "silent_mode", "ignore_urls"]

        record_template = dict.fromkeys(default_args)
        record_template.update(vars(args))

        with open(Path(args.config_file)) as config_file:
            records_json = json.load(config_file)['Records']

            for record in records_json:
                template = record_template.copy()
                template.update(record)
                records.append(template)
    else:
        records.append(vars(args))

    with open(Path(os.getcwd()).joinpath('url_parms.json')) as file:
        url_parm_json_file = json.load(file)

    return records, url_parm_json_file
