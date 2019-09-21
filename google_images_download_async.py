"""
Google_images_download_async main module.
"""

#Builtin imports:
import asyncio
import time
import os
import json

#Local imports:
from config_parser import parse_config

#Third party imports:
import aiofiles
import aiohttp

async def expand_arguments(arguments: dict) -> list:
    """

    """
    expanded_arguments = []

    keywords = [str(keyword) for keyword in arguments['keywords'].split(',')]
    for i, keyword in enumerate(keywords):
        expanded_arguments.append(arguments.copy())
        expanded_arguments[i]['keywords'] = keyword

    return expanded_arguments

class GoogleImagesDownloader():
    """

    """
    def __init__(self, url_parm_json_file):
        self.main_directory = "downloads"
        self.extensions = (".jpg", ".gif", ".png", ".bmp", ".svg", ".webp", ".ico")
        self.url_parm_json_file = url_parm_json_file

    async def download_url_data(self, url: str, request_type: str) -> bytes or str:
        """

        """
        await asyncio.sleep(0.1)

        try:
            print(f'Begin downloading {url}')
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(url) as resp:
                    if request_type == 'bytes':
                        content = await resp.read()
                    else:
                        content = await resp.text()
                    print(f'Finished downloading {url}')
                    return content

        except asyncio.TimeoutError:
            print(f'Timeout downloading: {url}')

    async def write_to_file(self, url: str, content: bytes, sub_dir: str) -> None:
        """

        """
        try:
            if sub_dir:
                os.makedirs(f'{self.main_directory}/{sub_dir}')
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

        async with aiofiles.open(f'{self.main_directory}/{sub_dir}/{filename}', 'wb') as file:
            print(f'Begin writing to {filename}')
            await file.write(content)
            print(f'Finished writing to {filename}')

    async def build_url_parameters(self, argument):
        """

        """
        lang_url = ''
        time_range = ''
        exact_size = ''
        built_url = "&tbs="
        counter = 0

        params = self.url_parm_json_file.copy()
        for parm in params:
            params[parm][0] = argument[parm]

        for value in params.values():
            if value[0]:
                ext_param = value[1][value[0]]
                # counter will tell if it is first param added or not
                if counter == 0:
                    # add it to the built url
                    built_url = built_url + ext_param
                    counter += 1
                else:
                    built_url = built_url + ',' + ext_param
                    counter += 1
        params = lang_url+built_url+exact_size+time_range

        return (argument['keywords'],
                params,
                argument['url'],
                argument['similar_images'],
                argument['specific_site'],
                argument['safe_search'])

    async def build_search_url(self,
                               search_term,
                               params, url,
                               similar_images,#unused
                               specific_site,#unused
                               safe_search):
        """

        """
        #check safe_search
        safe_search_string = "&safe=active"
        # check the args and choose the URL
        if not url:
            url = f'https://www.google.com/search?q={search_term}&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch{params}&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'

        #safe search check
        if safe_search:
            url = url + safe_search_string

        return url

    async def format_image_meta_data(self, obj):
        """

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

    async def get_next_item(self, page):
        """

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
            except Exception:
                final_object = ""

        return final_object, end_object

    async def get_all_items(self, page, argument):
        """

        """
        tasks = []
        count = 1

        while count <= int(argument['limit']):

            image_meta_data, end_content = await self.get_next_item(page)

            if image_meta_data == "no_links":
                break

            elif image_meta_data == '':
                page = page[end_content:]

            elif argument['offset'] and count < int(argument['offset']):
                count += 1
                page = page[end_content:]

            else:
                formated_image_meta_data = await self.format_image_meta_data(image_meta_data)
                url = formated_image_meta_data['image_link']

                color = f'- {argument["color"]}' if argument['color'] else ''
                sub_dir = f'{argument["keywords"]} {color}'

                tasks.append(self.image_download_task(url, sub_dir))
                count += 1

                page = page[end_content:]
        return tasks

    async def image_download_task(self, url: str, sub_dir: str = '') -> None:
        """

        """
        content = await self.download_url_data(url, 'bytes')
        if content:
            await self.write_to_file(url, content, sub_dir)
        else:
            print(f'***File not write: {url}')


    async def multi_image_download_task(self, argument: list) -> None:
        """

        """
        search_term, params, url, similar_images, specific_site, safe_search = await self.build_url_parameters(argument)

        url = await self.build_search_url(search_term,
                                          params,
                                          url,
                                          similar_images,
                                          specific_site,
                                          safe_search)

        raw_html = await self.download_url_data(url, 'text')

        tasks = await self.get_all_items(raw_html, argument)

        await asyncio.gather(*tasks)


async def main() -> None:
    records, url_parm_json_file = await parse_config()

    tasks = []
    GID = GoogleImagesDownloader(url_parm_json_file)

    for arguments in records:
        if arguments['single_image']:
            tasks.append(GID.image_download_task(arguments['single_image']))

        else:
            expanded_arguments = await expand_arguments(arguments)
            for argument in expanded_arguments:
                tasks.append(GID.multi_image_download_task(argument))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - start
    print(f"Execution time: {elapsed:0.3f} seconds.")
