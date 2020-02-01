"""
Google_images_download_async main module.
"""

# Builtin imports:
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, quote
import math

# Third party imports:
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import aiofiles
import aiohttp

# Local imports:
from config_parser import parse_config

class ArgumentExpander():
    """
    """
    def __init__(self, arguments: dict):
        self.arguments = arguments

    async def read_keywords_file(self, keywords_file: str) -> str:
        """
        """
        try:
            keywords_file_allowed_extensions = ('.csv','.txt')
            keywords = ''

            if any(extension in keywords_file for extension in keywords_file_allowed_extensions):
                with open(keywords_file) as file:
                    keyword_reader = file.read()
                    for row in keyword_reader:
                        keywords += str(row).strip()
            else:
                print(f'***Unable to import keywords file: {keywords_file}',
                f'file extension not valid use: {keywords_file_allowed_extensions}')
        except FileNotFoundError as error:
            print(f'***Unable to import keywords file: {keywords_file} {error}')

        return keywords

    async def init_new_argument(self, expanded_arguments: list) -> list:
        """
        This removes duplicate search terms by copying and initing them
        to their defaults before they are set in expand_arguments().
        """
        expanded_arguments.append(self.arguments.copy())
        expanded_arguments[-1]['url'] = ''
        expanded_arguments[-1]['similar_images'] = ''
        expanded_arguments[-1]['prefix_keywords'] = ''
        expanded_arguments[-1]['keywords'] = ''
        expanded_arguments[-1]['suffix_keywords'] = ''
        expanded_arguments[-1]['keywords_from_file'] = ''

        return expanded_arguments

    async def expand_search_words(self, expanded_arguments: list) -> list:
        """
        """

        prefixes = [str(prefix) for prefix in self.arguments['prefix_keywords'].split(',')]
        suffixes = [str(suffix) for suffix in self.arguments['suffix_keywords'].split(',')]
        keywords = [str(keyword) for keyword in self.arguments['keywords'].split(',')]

        for prefix in prefixes:
            for suffix in suffixes:
                for keyword in keywords:
                    expanded_arguments = await self.init_new_argument(expanded_arguments)
                    expanded_arguments[-1]['prefix_keywords'] = prefix
                    expanded_arguments[-1]['keywords'] = keyword
                    expanded_arguments[-1]['suffix_keywords'] = suffix

        return expanded_arguments

    async def expand_arguments(self) -> list:
        """
        Reads the arguments obtained from parse_config() and splits
        them into a list dict objects that can be processed concurrently.
        """

        expanded_arguments = []

        if self.arguments['url']:
            expanded_arguments = await self.init_new_argument(expanded_arguments)
            expanded_arguments[-1]['url'] = self.arguments['url']

        if self.arguments['similar_images']:
            expanded_arguments = await self.init_new_argument(expanded_arguments)
            expanded_arguments[-1]['similar_images'] = self.arguments['similar_images']

        if self.arguments['keywords_from_file']:
            self.arguments['keywords'] += ',' + await self.read_keywords_file(self.arguments['keywords_from_file'])

        if self.arguments['keywords'] or self.arguments['prefix_keywords'] or self.arguments['suffix_keywords']:
            expanded_arguments = await self.expand_search_words(expanded_arguments)

        return expanded_arguments


class GoogleImagesDownloader():
    """
    Main class of downloader.
    """
    def __init__(self, url_parm_json_file, argument):
        self.main_directory = Path(argument['output_directory'] or "Downloads")
        self.image_file_allowed_extensions = (".jpg", ".jpeg", ".gif", ".png", ".bmp", ".svg", ".webp", ".ico")
        self.file_size_units = ('bytes', 'KB', 'MB', 'GB', 'TB')
        self.url_parm_json_file = url_parm_json_file
        self.argument = argument
        self.sub_dir = ''

    async def gather_and_download_images(self) -> None:
        """
        Downloads all scraped images.
        """
        await self.make_directory(self.main_directory)

        if self.argument['single_image']:
            await self.download_images(self.argument['single_image'])

        else:

            url_params = await self.build_url_parameters()

            google_url = await self.build_search_url(url_params)

            raw_html = await self.get_raw_html_data(google_url)

            if raw_html != None:
                tasks = await self.generate_image_download_tasks(raw_html)
                await asyncio.gather(*tasks)

    async def make_directory(self, directory: str) -> None:
        """
        """
        try:
            os.makedirs(directory)
        except OSError as error:
            if error.errno == 17:
                pass

    async def build_url_parameters(self) -> str:
        """
        Returns string of url parameters.
        """
        lang_url = ''
        time_range = ''
        exact_size = ''
        built_url = "&tbs="

        params = self.url_parm_json_file.copy()

        for parm in params:
            params[parm][0] = self.argument[parm]

        for count, parm_value in enumerate(params.values()):
            if parm_value[0]:
                ext_param = parm_value[1][parm_value[0]]
                built_url += ext_param if count == 0 else f',{ext_param}'

        params = lang_url+built_url+exact_size+time_range

        return params

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

    async def build_search_term(self) -> str:
        """
        """
        search_term = ''
        specific_site = f'+site:{self.argument["specific_site"]}' if self.argument['specific_site'] else ''

        if self.argument['keywords']:
            search_term = f'{await self.build_keywords_search_term()}{specific_site}'

        if self.argument['similar_images']:
            search_term = f'{await self.build_similar_images_search_term()}{specific_site}'

        return search_term

    async def build_keywords_search_term(self) -> str:
        """
        """
        keyword = self.argument['keywords'] if self.argument['keywords'] else ''
        prefix = self.argument['prefix_keywords'] if self.argument['prefix_keywords'] else ''
        suffix = self.argument['suffix_keywords'] if self.argument['suffix_keywords'] else ''

        search_term = f'{prefix} {keyword} {suffix}'

        return search_term

    async def build_similar_images_search_term(self) -> str:
        """
        """
        try:
            google_similar_image_url = (f'https://www.google.com/searchbyimage?' +
                f'site=search&sa=X&image_url={self.argument["similar_images"]}')

            await self.write_to_sysout(f'Begin downloading images similar to {google_similar_image_url}')

            content = await self.download_url_data(google_similar_image_url, 'text')
            start_content = content.find('AMhZZ')
            end_content = content.find('&', start_content)
            google_url = f'https://www.google.com/search?tbs=sbi:{content[start_content:end_content]}&site=search&sa=X'

            content = await self.download_url_data(google_url, 'text')

            start_content = content.find('/search?sa=X&amp;q=')
            end_content = content.find(';', start_content + 19)
            search_term = content[start_content + 19:end_content]

        except TypeError as error:
            await self.write_error_log(f'***Unable to complete similar image search: {error}')
            search_term = ''
            pass

        return search_term

    async def download_url_data(self, google_url: str, request_type: str, attempts: int = 0) -> bytes or str:
        """
        Downloads data from provided url.
        """
        try:
            await asyncio.sleep(0.1)

            attempts += 1

            # await self.write_to_sysout(f'Begin downloading {google_url}')

            headers = {}
            headers['User-Agent'] = ('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 ' +
                                        '(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')

            if self.argument['socket_timeout'] < 2:
                timeout = aiohttp.ClientTimeout(total=2)
            else:
                timeout = aiohttp.ClientTimeout(total=self.argument['socket_timeout'])

            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(google_url) as resp:
                    if resp.status == 200:
                        if request_type == 'bytes':
                            content = await resp.read()
                        else:
                            content = await resp.text()

                        # await self.write_to_sysout(f'Finished downloading {google_url}')

                        return content

                    raise DownloadError(google_url, resp.status)

        except DownloadError as error:
            await self.write_error_log(error)

        except aiohttp.client_exceptions.ClientConnectorError as error:
            await self.write_error_log(f'***Unable to Connect to Client {error} URL: {google_url}')

        except aiohttp.client_exceptions.InvalidURL as error:
            await self.write_error_log(f'***Invalid URL: {error}')

        except asyncio.TimeoutError:
            if attempts < self.argument['repeat_failure']:
                await self.download_url_data(google_url, request_type, attempts)
            else:
                await self.write_error_log(f'Timeout downloading: {google_url}')

    async def get_raw_html_data(self, google_url: str) -> str:
        """
        """
        if self.argument['limit'] > 100:
            raw_html = await self.multi_page_image_download(google_url)
        else:
            raw_html = await self.download_url_data(google_url, 'text')

        return raw_html

    async def generate_image_download_tasks(self, page: str) -> asyncio.coroutine:
        """
        Gets all images from page.
        """
        tasks = []
        limit = 1
        ignore_url = False

        while limit <= int(self.argument['limit']):

            image_meta_data, end_content = await self.get_next_item(page)

            if image_meta_data == "no_links":
                break
            if image_meta_data == '':
                page = page[end_content:]
            elif self.argument['offset'] and limit < int(self.argument['offset']):
                limit += 1
                page = page[end_content:]
            else:
                formated_image_meta_data = await self.format_image_meta_data(image_meta_data)
                image_url = formated_image_meta_data['image_link']
                image_thumbnail_url = formated_image_meta_data['image_thumbnail_url']

                await self.set_sub_directory()

                if self.argument['proxy']:
                    os.environ["http_proxy"] = self.argument['proxy']
                    os.environ["https_proxy"] = self.argument['proxy']

                if self.argument['ignore_urls']:
                    if any(ignored_url in image_url for ignored_url in self.argument['ignore_urls'].split(',')):
                        tasks.append(self.write_to_sysout(f'URL Ignored: {image_url}'))
                        ignore_url = True

                if not ignore_url:
                    if self.argument['print_urls'] or self.argument['no_download']:
                        tasks.append(self.print_image_url(image_url))

                    if not self.argument['no_download']:
                        if not self.argument['thumbnail_only']:
                            tasks.append(self.download_images(image_url))

                        if self.argument['thumbnail'] or self.argument['thumbnail_only']:
                            tasks.append(self.download_image_thumbnails(image_url, image_thumbnail_url))

                limit += 1

                page = page[end_content:]

        return tasks

    async def get_next_item(self, page: str) -> tuple:
        """
        Gets next image from page.
        """
        try:
            start_line = page.find('rg_meta notranslate')
            if start_line == -1:  # If no links are found then give an error!
                image_meta_data = "no_links"
                end_content = 0
            else:
                start_line = page.find('class="rg_meta notranslate">')
                start_content = page.find('{', start_line + 1)
                end_content = page.find('</div>', start_content + 1)
                content_raw = str(page[start_content:end_content])
                content_decode = bytes(content_raw, "utf-8").decode("unicode_escape")
                image_meta_data = json.loads(content_decode)
        except (UnicodeError, json.JSONDecodeError):
            image_meta_data = ""

        return image_meta_data, end_content

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

    async def set_sub_directory(self) -> None:
        '''
        '''
        image  = f'{self.argument["image_directory"]}/' if self.argument['image_directory'] else ''
        prefix = f'{self.argument["prefix_keywords"]} ' if self.argument['prefix_keywords'] else ''
        suffix = f' {self.argument["suffix_keywords"]}' if self.argument['suffix_keywords'] else ''
        color  = f' - {self.argument["color"]}' if self.argument['color'] else ''

        self.sub_dir = f'{image}{prefix}{self.argument["keywords"]}{suffix}{color}' if not self.argument['no_directory'] else ''

    async def print_image_url(self, image_url: str) -> None:
        """
        """
        await self.write_to_sysout(f'Image URL: {image_url}')

    async def multi_page_image_download(self, google_url: str) -> str:
        """
        """
        page_source = ''
        stale_element = True

        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')

        try:
            with webdriver.Chrome(self.argument['chromedriver'], options=options) as wd:
                wd.get(google_url)
                html_body_element = wd.find_element_by_tag_name("body")

                number_of_pages = math.ceil(self.argument['limit']/100)
                for i in range(number_of_pages):
                    while stale_element:
                        try:
                            html_body_element.send_keys(Keys.END)
                            stale_element = False
                        except StaleElementReferenceException:
                            pass

                    try:
                        html_body_element.find_element_by_xpath("//input[@id='smb']").click()
                    except ElementNotInteractableException:
                        pass
                    except NoSuchElementException:
                        pass

                    await asyncio.sleep(0.5)

                page_source = wd.page_source
        except WebDriverException as error:
             await self.write_error_log(f'Exception: {error}' +
                'Cannot locate chromedriver please insure the chrome browser is installed' +
                'and the argument "--chromedriver" has the correct path to the executable.')

        return page_source

    async def download_images(self, image_url: str, attempts: int = 0) -> None:
        """
        Downloads image from provided url to provided sub directory.
        """
        try:
            attempts += 1
            unquoted_image_url = unquote(image_url)

            content = await self.download_url_data(unquoted_image_url, 'bytes')

            await self.write_image_to_file(unquoted_image_url, content)
        except TypeError as error:
            if attempts <= self.argument['repeat_failure']:
                await self.download_images(image_url, attempts)
            else:
                await self.write_error_log(f'***File not writen: {unquoted_image_url} {error}')

    async def write_image_to_file(self, image_url: str, content: bytes) -> None:
        """
        Writes data to file.
        """
        filename = await self.generate_file_name(str(image_url[(image_url.rfind('/')) + 1:]))
        image_directory = await self.generate_image_directory()
        image_file_path = image_directory.joinpath(filename)

        await self.write_to_file(image_file_path, content)
        file_size = await self.get_file_size(image_file_path) if self.argument['print_size'] else ''

        await self.write_to_sysout(f'Finished downloading: {image_file_path} {file_size}')

        if self.argument['save_source']:
            await self.write_download_log(image_url, image_file_path)

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

    async def generate_image_directory(self) -> str:
        """
        """
        image_directory = self.main_directory.joinpath(self.sub_dir) if self.sub_dir else self.main_directory
        await self.make_directory(image_directory)

        return image_directory

    async def download_image_thumbnails(self, image_url: str, image_thumbnail_url: str, attempts: int = 0) -> None:
        """
        Downloads image from provided url to provided sub directory.
        """
        try:
            attempts += 1
            unquoted_image_thumbnail_url = unquote(image_thumbnail_url)

            content = await self.download_url_data(unquoted_image_thumbnail_url, 'bytes')

            await self.write_image_thumbnail_to_file(image_url, unquoted_image_thumbnail_url, content)
        except TypeError as error:
            if attempts <= self.argument['repeat_failure']:
                await self.download_images(unquoted_image_thumbnail_url, attempts)
            else:
                await self.write_error_log(f'***File not writen: {unquoted_image_thumbnail_url} {error}')

    async def write_image_thumbnail_to_file(self, image_url: str, image_thumbnail_url: str, content: bytes) -> None:
        """
        Writes data to file.
        """
        filename = await self.generate_file_name(str(image_url[(image_url.rfind('/')) + 1:]))
        image_thumbnail_directory = await self.generate_image_thumbnail_directory()
        image_thumbnail_file_path = image_thumbnail_directory.joinpath(filename)

        await self.write_to_file(image_thumbnail_file_path, content)
        file_size = await self.get_file_size(image_thumbnail_file_path) if self.argument['print_size'] else ''

        await self.write_to_sysout(f'Finished downloading: {image_thumbnail_file_path} {file_size}')

        if self.argument['save_source']:
            await self.write_download_log(image_thumbnail_url, image_thumbnail_file_path)

    async def generate_image_thumbnail_directory(self) -> str:
        """
        """
        image_thumbnail_directory = self.main_directory.joinpath(self.sub_dir, 'thumbnail') if self.sub_dir else self.main_directory.joinpath('thumbnail')
        await self.make_directory(image_thumbnail_directory)

        return image_thumbnail_directory

    async def write_to_file(self, image_file_path: str, content: bytes) -> None:
        """
        """
        try:
            async with aiofiles.open(image_file_path, 'wb') as file:
                await file.write(content)
        except IOError as error:
            await self.write_error_log(f'***{error}: {image_file_path}')

    async def get_file_size(self, file_path: str) -> str:
        """
        """
        try:
            count = 0
            units = ''
            file_size = os.path.getsize(file_path)

            while int(file_size) / 1024 >= 1:
                file_size /= 1024.0
                count += 1

            units = self.file_size_units[count]
            file_size_with_units = f'{file_size:.1f} {units}'

        except OSError as error:
            file_size_with_units = ''

        return file_size_with_units

    async def write_to_sysout(self, message: str) -> None:
        """
        """
        if not self.argument['silent_mode']:
            print(message)

    async def write_download_log(self, image_url: str, file_path: str) -> None:
        """
        """
        save_source = self.main_directory.joinpath(self.argument["save_source"])

        abs_path = os.path.abspath(file_path)

        download_log_record = f'{await self.get_time_stamp()}: {abs_path}\t{image_url}\n'

        async with aiofiles.open(save_source, 'a') as file:
            await file.write(download_log_record)

    async def write_error_log(self, message: str) -> None:
        """
        """
        error_log_source = self.main_directory.joinpath(self.argument["error_log"])

        error_log_record = f'{await self.get_time_stamp()}: {message}\n'

        async with aiofiles.open(error_log_source, 'a') as file:
            await file.write(error_log_record)

        await self.write_to_sysout(message)

    async def get_time_stamp(self) -> None:
        """
        """
        datetime_now = datetime.now()
        time_stamp = datetime.timestamp(datetime_now)
        form_time_stamp = datetime.fromtimestamp(time_stamp)

        return form_time_stamp


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
            google_image_downloader = GoogleImagesDownloader(url_parm_json_file, record)
            tasks.append(google_image_downloader.gather_and_download_images())
        else:
            argument_expander = ArgumentExpander(record)
            expanded_arguments = await argument_expander.expand_arguments()
            for argument in expanded_arguments:
                google_image_downloader = GoogleImagesDownloader(url_parm_json_file, argument)
                tasks.append(google_image_downloader.gather_and_download_images())

    await asyncio.gather(*tasks)

    print('Finished image download')

if __name__ == "__main__":
    START = time.perf_counter()
    asyncio.run(main())
    ELAPSED = time.perf_counter() - START
    print(f'Execution time: {ELAPSED:0.3f} seconds.')