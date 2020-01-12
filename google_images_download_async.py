"""
Google_images_download_async main module.
"""

# Builtin imports:
import asyncio
import json
import os
import time
from pathlib import Path
from urllib.parse import unquote, quote
import csv

# Third party imports:
import aiofiles
import aiohttp

# Local imports:
from config_parser import parse_config


async def read_keywords_file(keywords_file: str) -> str:
    """
    """
    keywords_file_allowed_extensions = ('.csv','.txt')
    keywords = []

    if any(extension in keywords_file for extension in keywords_file_allowed_extensions):
        with open(keywords_file) as csv_file:
            keyword_reader = csv.reader(csv_file, delimiter=',')
            for row in keyword_reader:
                keywords += list(row)

    return ','.join(keywords).strip()

async def init_new_argument(expanded_arguments: list, arguments: dict) -> list:
    """
    This removes duplicate search terms by copying and initing them
    to their defaults before they are set in expand_arguments().
    """
    expanded_arguments.append(arguments.copy())
    expanded_arguments[-1]['url'] = ''
    expanded_arguments[-1]['similar_images'] = ''
    expanded_arguments[-1]['prefix_keywords'] = ''
    expanded_arguments[-1]['keywords'] = ''
    expanded_arguments[-1]['suffix_keywords'] = ''
    expanded_arguments[-1]['keywords_from_file'] = ''

    return expanded_arguments

async def expand_search_words(expanded_arguments: list, arguments: dict) -> list:
    """
    """

    prefixes = [str(prefix) for prefix in arguments['prefix_keywords'].split(',')]
    suffixes = [str(suffix) for suffix in arguments['suffix_keywords'].split(',')]
    keywords = [str(keyword) for keyword in arguments['keywords'].split(',')]

    for prefix in prefixes:
        for suffix in suffixes:
            for keyword in keywords:
                expanded_arguments = await init_new_argument(expanded_arguments, arguments)
                expanded_arguments[-1]['prefix_keywords'] = prefix
                expanded_arguments[-1]['keywords'] = keyword
                expanded_arguments[-1]['suffix_keywords'] = suffix

    return expanded_arguments

async def expand_arguments(arguments: dict) -> list:
    """
    Reads the arguments obtained from parse_config() and splits
    them into a list dict objects that can be processed concurrently.
    """

    expanded_arguments = []

    if arguments['url']:
        expanded_arguments = await init_new_argument(expanded_arguments, arguments)
        expanded_arguments[-1]['url'] = arguments['url']

    if arguments['similar_images']:
        expanded_arguments = await init_new_argument(expanded_arguments, arguments)
        expanded_arguments[-1]['similar_images'] = arguments['similar_images']

    if arguments['keywords_from_file']:
        arguments['keywords'] += ',' + await read_keywords_file(arguments['keywords_from_file'])

    if arguments['keywords'] or arguments['prefix_keywords'] or arguments['suffix_keywords']:
        expanded_arguments = await expand_search_words(expanded_arguments, arguments)

    return expanded_arguments


class GoogleImagesDownloader():
    """
    Main class of downloader.
    """
    def __init__(self, url_parm_json_file, argument):
        self.main_directory = Path(argument['output_directory'] or "Downloads")
        self.image_file_allowed_extensions = (".jpg", ".jpeg", ".gif", ".png", ".bmp", ".svg", ".webp", ".ico")
        self.url_parm_json_file = url_parm_json_file
        self.argument = argument

    async def download_url_data(self, google_url: str, request_type: str) -> bytes or str:
        """
        Downloads data from provided url.
        """
        await asyncio.sleep(0.1)

        if not self.argument['silent_mode']:
            print(f'Begin downloading {google_url}')

        headers = {}
        headers['User-Agent'] = ('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 ' +
                                    '(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')

        if self.argument['socket_timeout'] < 2:
            timeout = aiohttp.ClientTimeout(total=2)
        else:
            timeout = aiohttp.ClientTimeout(total=self.argument['socket_timeout'])

        try:
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(google_url) as resp:
                    if resp.status == 200:
                        if request_type == 'bytes':
                            content = await resp.read()

                        else:
                            content = await resp.text()

                        if not self.argument['silent_mode']:
                            print(f'Finished downloading {google_url}')

                        return content

                    raise DownloadError(google_url, resp.status)

        except DownloadError as error:
            if not self.argument['silent_mode']:
                print(error)

        except aiohttp.client_exceptions.ClientConnectorError as error:
            if not self.argument['silent_mode']:
                print(f'***Unable to Connect to Client {error} URL: {google_url}')

        except aiohttp.client_exceptions.InvalidURL as error:
            if not self.argument['silent_mode']:
                print(f'***Invalid URL: {error}')

        except asyncio.TimeoutError:
            if not self.argument['silent_mode']:
                print(f'Timeout downloading: {google_url}')

    async def make_directory(self, sub_dir: str) -> None:
        """
        """
        try:
            if sub_dir:
                file_path = self.main_directory.joinpath(sub_dir)
                os.makedirs(self.main_directory.joinpath(sub_dir))
            else:
                file_path = self.main_directory
                os.makedirs(self.main_directory)
        except OSError as error:
            if error.errno == 17:
                pass

        return file_path

    async def generate_file_name(self, filename: str) -> str:
        """
        """
        if '?' in filename:
            filename = filename[:filename.find('?')]

        if not any(extension in filename for extension in self.image_file_allowed_extensions):
            filename = f'{filename}.jpg'

        if self.argument["prefix"]:
            filename = f'{self.argument["prefix"]} {filename}'

        if self.argument["suffix"]:
            filename, ext = filename.rsplit('.', 1)
            filename = f'{filename} {self.argument["suffix"]}.{ext}'

        return filename

    async def write_download_log(self, image_url: str, file_path: str) -> None:
        """
        """
        save_source = self.main_directory.joinpath(self.argument["save_source"])

        async with aiofiles.open(save_source, 'a') as file:
            await file.write(f'{file_path}\t{image_url}\n')

    async def write_to_file(self, image_url: str, content: bytes, sub_dir: str) -> None:
        """
        Writes data to file.
        """
        filename = await self.generate_file_name(str(image_url[(image_url.rfind('/')) + 1:]))

        directory = await self.make_directory(sub_dir)

        file_path = directory.joinpath(filename)

        async with aiofiles.open(file_path, 'wb') as file:
            if not self.argument['silent_mode']:
                print(f'Begin writing to {filename}')

            await file.write(content)

            if not self.argument['silent_mode']:
                print(f'Finished writing to {filename}')

        if self.argument['save_source']:
            await self.write_download_log(image_url, file_path)

    async def build_url_parameters(self) -> str:
        """
        Returns string of url parameters.
        """
        lang_url = ''
        time_range = ''
        exact_size = ''
        built_url = "&tbs="
        counter = 0

        params = self.url_parm_json_file.copy()
        for parm in params:
            params[parm][0] = self.argument[parm]


        for value in params.values():

            if value[0]:
                ext_param = value[1][value[0]]

                if counter == 0:
                    # add it to the built url
                    built_url = built_url + ext_param
                    counter += 1

                else:
                    built_url = built_url + ',' + ext_param
                    counter += 1


        params = lang_url+built_url+exact_size+time_range

        return params

    async def build_keywords_term(self) -> str:
        search_term = self.argument["keywords"]

        if self.argument["prefix_keywords"]:
            search_term = f'{self.argument["prefix_keywords"]} {search_term}'

        if self.argument["suffix_keywords"]:
            search_term = f'{search_term} {self.argument["suffix_keywords"]}'

        return search_term

    async def build_search_term(self) -> str:
        """
        """
        search_term = ''

        if self.argument['similar_images']:
            search_term = await self.build_similar_images_search_term()

        if self.argument['keywords']:
            search_term = await self.build_keywords_term()

        return search_term

    async def build_search_url(self, params: str) -> str:
        """
        Creates search url from provided params.
        """
        # check safe_search
        safe_search_string = "&safe=active"

        if self.argument['url']:
            google_url = self.argument['url']
        else:
            search_term =  await self.build_search_term()

            google_url = (f'https://www.google.com/search?q={quote(search_term)}' +
                   f'&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch{params}' +
                   '&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg')

        # safe search check
        if self.argument['safe_search']:
            google_url = google_url + safe_search_string

        return google_url

    async def build_similar_images_search_term(self):
        """

        """
        google_similar_image_url = (f'https://www.google.com/searchbyimage?' +
               f'site=search&sa=X&image_url={self.argument["similar_images"]}')

        if not self.argument['silent_mode']:
            print(f'Begin downloading images similar to {google_similar_image_url}')

        try:
            content = await self.download_url_data(google_similar_image_url, 'text')
        # if content != None:
            start_content = content.find('AMhZZ')
            end_content = content.find('&', start_content)
            google_url = f'https://www.google.com/search?tbs=sbi:{content[start_content:end_content]}&site=search&sa=X'
        # else:
            # print('***Unable to complete similar image search')
            # search_term = ''

            content = await self.download_url_data(google_url, 'text')

        # if content != None:
            start_content = content.find('/search?sa=X&amp;q=')
            end_content = content.find(';', start_content + 19)
            search_term = content[start_content + 19:end_content]
        # else:
        except Exception as error:
            print(f'***Unable to complete similar image search: {error}')
            search_term = ''
            pass

        return search_term

    async def format_image_meta_data(self, obj: dict) -> dict:
        """
        Formats image meta dates.
        """
        formatted_object = {}
        formatted_object['image_format'] = obj['ity']
        formatted_object['image_height'] = obj['oh']
        formatted_object['image_width'] = obj['ow']
        formatted_object['image_link'] = obj['ou']
        formatted_object['image_description'] = obj['pt']
        formatted_object['image_host'] = obj['rh']
        formatted_object['image_source'] = obj['ru']
        formatted_object['image_thumbnail_url'] = obj['tu']

        return formatted_object

    async def get_next_item(self, page: str) -> tuple:
        """
        Gets next image from page.
        """
        start_line = page.find('rg_meta notranslate')
        if start_line == -1:  # If no links are found then give an error!
            final_object = "no_links"
            end_object = 0

        else:
            start_line = page.find('class="rg_meta notranslate">')
            start_object = page.find('{', start_line + 1)
            end_object = page.find('</div>', start_object + 1)
            object_raw = str(page[start_object:end_object])

            try:
                object_decode = bytes(object_raw, "utf-8").decode("unicode_escape")
                final_object = json.loads(object_decode)

            except (UnicodeError, json.JSONDecodeError):
                final_object = ""

        return final_object, end_object

    async def set_directory(self) -> str:
        '''
        '''
        color  = f' - {self.argument["color"]}' if self.argument['color'] else ''
        prefix = f'{self.argument["prefix_keywords"]} ' if self.argument['prefix_keywords'] else ''
        suffix = f' {self.argument["suffix_keywords"]}' if self.argument['suffix_keywords'] else ''
        sub_dir = f'{prefix}{self.argument["keywords"]}{suffix}{color}' if not self.argument['no_directory'] else ''

        return sub_dir

    async def get_all_items(self, page: str) -> asyncio.coroutine:
        """
        Gets all images from page.
        """
        tasks = []
        count = 1

        while count <= int(self.argument['limit']):

            image_meta_data, end_content = await self.get_next_item(page)

            if image_meta_data == "no_links":
                break

            if image_meta_data == '':
                page = page[end_content:]

            elif self.argument['offset'] and count < int(self.argument['offset']):
                count += 1
                page = page[end_content:]

            else:
                formated_image_meta_data = await self.format_image_meta_data(image_meta_data)
                image_url = formated_image_meta_data['image_link']
                sub_dir = await self.set_directory()

                tasks.append(self.download_images(image_url, sub_dir))
                count += 1

                page = page[end_content:]

        return tasks

    async def download_images(self, image_url: str, sub_dir: str = '') -> None:
        """
        Downloads image from provided url to provided sub directory.
        """
        unquoted_image_url = unquote(image_url)
        content = await self.download_url_data(unquoted_image_url, 'bytes')

        if content:
            await self.write_to_file(unquoted_image_url, content, sub_dir)
        else:
            if not self.argument['silent_mode']:
                print(f'***File not write: {unquoted_image_url}')

    async def gather_images(self) -> None:
        """
        Downloads all scraped images.
        """
        if self.argument['single_image']:
            await self.download_images(self.argument['single_image'])

        else:
            url_params = await self.build_url_parameters()

            google_url = await self.build_search_url(url_params)

            raw_html = await self.download_url_data(google_url, 'text')

            if raw_html != None:
                tasks = await self.get_all_items(raw_html)
                await asyncio.gather(*tasks)


class DownloadError(Exception):
    """
    Raised when error occurs during download.
    """
    def __init__(self, url, status):
        self.url = url
        self.status = status

    def __str__(self):
        return f'***Unable to download {self.url}, HTTP Status Code was {self.status}'


async def main() -> None:
    """
    Main function of google_image_downloader_async.
    """
    url_parm_json_file, records = await parse_config()

    tasks = []

    print('Starting image download')

    for record in records:
        if record['single_image']:
            gid = GoogleImagesDownloader(url_parm_json_file, record)
            tasks.append(gid.gather_images())
        else:
            expanded_arguments = await expand_arguments(record)
            for argument in expanded_arguments:
                gid = GoogleImagesDownloader(url_parm_json_file, argument)
                tasks.append(gid.gather_images())

    await asyncio.gather(*tasks)

    print('Finished image download')

if __name__ == "__main__":
    START = time.perf_counter()
    asyncio.run(main())
    ELAPSED = time.perf_counter() - START
    print(f'Execution time: {ELAPSED:0.3f} seconds.')