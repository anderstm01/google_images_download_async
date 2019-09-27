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

# Third party imports:
import aiofiles
import aiohttp

# Local imports:
from config_parser import parse_config


async def expand_arguments(arguments: dict) -> list:
    """
    Reads the arguments obtained from parse_config() and splits
    them into a list dict objects that can be processed concurrently.
    """
    async def expand_arguments_helper(expanded_arguments: list, arguments: dict) -> list:
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
        return expanded_arguments

    expanded_arguments = []

    prefixes = [str(prefix) for prefix in arguments['prefix_keywords'].split(',')]
    suffixes = [str(suffix) for suffix in arguments['suffix_keywords'].split(',')]
    keywords = [str(keyword) for keyword in arguments['keywords'].split(',')]

    if arguments['url']:
        expanded_arguments = await expand_arguments_helper(expanded_arguments, arguments)
        expanded_arguments[-1]['url'] = arguments['url']

    if arguments['similar_images']:
        expanded_arguments = await expand_arguments_helper(expanded_arguments, arguments)
        expanded_arguments[-1]['similar_images'] = arguments['similar_images']

    for prefix in prefixes:
        for suffix in suffixes:
            for keyword in keywords:
                expanded_arguments = await expand_arguments_helper(expanded_arguments, arguments)
                expanded_arguments[-1]['prefix_keywords'] = prefix
                expanded_arguments[-1]['keywords'] = keyword
                expanded_arguments[-1]['suffix_keywords'] = suffix

    return expanded_arguments


class GoogleImagesDownloader():
    """
    Main class of downloader.
    """
    def __init__(self, url_parm_json_file, argument):
        self.main_directory = Path(argument['output_directory'] or "Downloads")
        self.extensions = (".jpg", ".jpeg", ".gif", ".png", ".bmp", ".svg", ".webp", ".ico")
        self.url_parm_json_file = url_parm_json_file
        self.argument = argument

    async def download_url_data(self, url: str, request_type: str) -> bytes or str:
        """
        Downloads data from provided url.
        """
        await asyncio.sleep(0.1)

        try:
            if not self.argument['silent_mode']:
                print(f'Begin downloading {url}')

            headers = {}
            headers['User-Agent'] = ('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 ' +
                                     '(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')

            timeout = aiohttp.ClientTimeout(total=5.0)

            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        if request_type == 'bytes':
                            content = await resp.read()

                        else:
                            content = await resp.text()

                        if not self.argument['silent_mode']:
                            print(f'Finished downloading {url}')

                        return content

                    raise DownloadError(url, resp.status)

        except DownloadError as error:
            if not self.argument['silent_mode']:
                print(error)

        except aiohttp.client_exceptions.ClientConnectorError as error:
            if not self.argument['silent_mode']:
                print(f'***Unable to Connect to Client {error} URL: {url}')

        except aiohttp.client_exceptions.InvalidURL as error:
            if not self.argument['silent_mode']:
                print(f'***Invalid URL: {error}')

        except asyncio.TimeoutError:
            if not self.argument['silent_mode']:
                print(f'Timeout downloading: {url}')

    async def write_to_file(self, url: str, content: bytes, sub_dir: str) -> None:
        """
        Writes data to file.
        """
        try:
            if sub_dir:
                os.makedirs(self.main_directory.joinpath(sub_dir))
            else:
                os.makedirs(self.main_directory)
        except OSError as error:
            if error.errno == 17:
                pass

        filename = str(url[(url.rfind('/')) + 1:])

        if '?' in filename:
            filename = filename[:filename.find('?')]

        if not any(extension in filename for extension in self.extensions):
            filename = f'{filename}.jpg'

        if self.argument["prefix"]:
            filename = f'{self.argument["prefix"]} {filename}'

        if self.argument["suffix"]:
            filename, ext = filename.rsplit('.', 1)
            filename = f'{filename} {self.argument["suffix"]}.{ext}'

        if sub_dir:
            file_path = self.main_directory.joinpath(sub_dir).joinpath(filename)

        else:
            file_path = self.main_directory.joinpath(filename)

        if self.argument['save_source']:
            save_source = self.main_directory.joinpath(self.argument["save_source"])

            async with aiofiles.open(save_source, 'a') as file:
                await file.write(f'{file_path}\t{url}\n')

        async with aiofiles.open(file_path, 'wb') as file:
            if not self.argument['silent_mode']:
                print(f'Begin writing to {filename}')

            await file.write(content)

            if not self.argument['silent_mode']:
                print(f'Finished writing to {filename}')

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

    async def build_search_url(self, params: str) -> str:
        """
        Creates search url from provided params.
        """
        # check safe_search
        safe_search_string = "&safe=active"

        if self.argument['similar_images']:
            search_term = await self.similar_images()
        else:
            search_term = self.argument["keywords"]

        if self.argument["prefix_keywords"]:
            search_term = f'{self.argument["prefix_keywords"]} {search_term}'

        if self.argument["suffix_keywords"]:
            search_term = f'{search_term} {self.argument["suffix_keywords"]}'

        if self.argument['url']:
            url = self.argument['url']

        else:
            url = (f'https://www.google.com/search?q={quote(search_term)}' +
                   f'&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch{params}' +
                   '&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg')

        # safe search check
        if self.argument['safe_search']:
            url = url + safe_search_string

        return url

    async def similar_images(self):
        """

        """
        url = (f'https://www.google.com/searchbyimage?' +
               f'site=search&sa=X&image_url={self.argument["similar_images"]}')

        content = await self.download_url_data(url, 'text')

        start_content = content.find('AMhZZ')
        end_content = content.find('&', start_content)
        url = f'https://www.google.com/search?tbs=sbi:{content[start_content:end_content]}&site=search&sa=X'

        content = await self.download_url_data(url, 'text')

        start_content = content.find('/search?sa=X&amp;q=')
        end_content = content.find(';', start_content + 19)
        search_term = content[start_content + 19:end_content]

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
                url = formated_image_meta_data['image_link']

                color = f' - {self.argument["color"]}' if self.argument['color'] else ''
                prefix = f'{self.argument["prefix_keywords"]} ' if self.argument['prefix_keywords'] else ''
                suffix = f' {self.argument["suffix_keywords"]}' if self.argument['suffix_keywords'] else ''
                if not self.argument['no_directory']:
                    sub_dir = f'{prefix}{self.argument["keywords"]}{suffix}{color}'
                else:
                    sub_dir = ''

                tasks.append(self.image_download_task(url, sub_dir))
                count += 1

                page = page[end_content:]

        return tasks

    async def image_download_task(self, url: str, sub_dir: str = '') -> None:
        """
        Downloads image from provided url to provided sub directory.
        """
        url = unquote(url)
        content = await self.download_url_data(url, 'bytes')
        if content:
            await self.write_to_file(url, content, sub_dir)
        else:
            if not self.argument['silent_mode']:
                print(f'***File not write: {url}')

    async def gather_image_task(self) -> None:
        """
        Downloads all scraped images.
        """
        if self.argument['single_image']:
            await self.image_download_task(self.argument['single_image'])

        else:
            url_params = await self.build_url_parameters()

            url = await self.build_search_url(url_params)

            raw_html = await self.download_url_data(url, 'text')

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
            tasks.append(gid.gather_image_task())
        else:
            expanded_arguments = await expand_arguments(record)
            for argument in expanded_arguments:
                gid = GoogleImagesDownloader(url_parm_json_file, argument)
                tasks.append(gid.gather_image_task())

    await asyncio.gather(*tasks)

    print('Finished image download')

if __name__ == "__main__":
    START = time.perf_counter()
    asyncio.run(main())
    ELAPSED = time.perf_counter() - START
    print(f'Execution time: {ELAPSED:0.3f} seconds.')
