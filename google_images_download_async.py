import json
import argparse
import aiohttp
import aiofiles
# from aiofile import AIOFile, Reader, Writer
from collections import defaultdict
import asyncio
import time
import os
import ssl
import random


async def parse_config():
    '''
    Scope: Reads user defined json config files or parses user provided arguments
    
    Paramiters: None
    
    Return: list of dicts that contain the search criteria
    '''    
    config = argparse.ArgumentParser(description="google async image downloader")
    config.add_argument('-dflt', '--default_file', help='default file name', default='default_config.json', type=str, required=False)
    config.add_argument('-urlp', '--url_parms', help='url parameters', default='url_parms.json', type=str, required=False)
    config.add_argument('-cf', '--config_file', help='config file name', default=None, type=str, required=False)
    args, unknown_args = config.parse_known_args()

    records = []
    
    if args.config_file is not None:
        with open(args.default_file,'r') as f:
            default_json_file = json.load(f)

        with open(args.config_file,'r') as f:
            config_json_file = json.load(f)

        for i, record in enumerate(config_json_file['Records']):
            records.append(default_json_file.copy())
            records[i].update(record.items())
            
    else:
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
        if unknown_args != []:
            print(f'The following argument(s) {", ".join(str(unknown_arg) for unknown_arg in unknown_args)} is/are not a recognised and have been bypassed.')
            
        records.append(vars(args))
        
    with open(args.url_parms,'r') as f:
        url_parm_json_file = json.load(f)
    
    return records, url_parm_json_file

async def expand_arguments(arguments: dict) -> list:
    expanded_arguments = []
    
    keywords = [str(keyword) for keyword in arguments['keywords'].split(',')]
    for i, keyword in enumerate(keywords):
        expanded_arguments.append(arguments.copy())
        expanded_arguments[i]['keywords'] = keyword
    
    return expanded_arguments

class GoogleImagesDownloader(object):
    def __init__(self, url_parm_json_file):
        self.main_directory = "downloads"
        self.extensions = (".jpg", ".gif", ".png", ".bmp", ".svg", ".webp", ".ico")
        self.url_parm_json_file = url_parm_json_file
            
    async def download_url_data(self, url: str, request_type: str) -> bytes or str:
        await asyncio.sleep(0.1)
        
        try:
            print(f'Begin downloading {url}')
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(headers = headers, timeout=timeout) as session:
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
        try:
            if sub_dir != '':
                os.makedirs(f'{self.main_directory}/{sub_dir}')
            else:
                os.makedirs(self.main_directory)
        except OSError as e:
            if e.errno == 17:
                pass

        filename = str(url[(url.rfind('/')) + 1:])
        
        if '?' in filename:
            filename = filename[:filename.find('?')]
            
        if not any(extension in filename for extension in self.extensions):
            filename = f'{filename}.jpg'

        async with aiofiles.open(f'{self.main_directory}/{sub_dir}/{filename}', 'wb') as f:
            print(f'Begin writing to {filename}')
            await f.write(content)
            print(f'Finished writing to {filename}')
        
    async def build_url_parameters(self, argument):
        lang_url = ''
        time_range = ''
        exact_size = ''
        built_url = "&tbs="
        counter = 0

        params = self.url_parm_json_file.copy()
        for i, parm in enumerate(params):
            params[parm][0] = argument[parm]
        
        for key, value in params.items():
            if value[0] is not None:
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

        return argument['keywords'], params, argument['url'], argument['similar_images'], argument['specific_site'], argument['safe_search']
    
    async def build_search_url(self, search_term, params, url, similar_images, specific_site, safe_search):
        #check safe_search
        safe_search_string = "&safe=active"
        # check the args and choose the URL
        if url:
            url = url
            
        else:
            url = f'https://www.google.com/search?q={search_term}&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch{params}&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'

        #safe search check
        if safe_search:
            url = url + safe_search_string
        
        return url
    
    async def format_image_meta_data(self, object):
        formatted_object = {}
        formatted_object['image_format'] = object['ity']
        formatted_object['image_height'] = object['oh']
        formatted_object['image_width'] = object['ow']
        formatted_object['image_link'] = object['ou']
        formatted_object['image_description'] = object['pt']
        formatted_object['image_host'] = object['rh']
        formatted_object['image_source'] = object['ru']
        formatted_object['image_thumbnail_url'] = object['tu']
        return formatted_object
    
    async def get_next_item(self, page):
        start_line = page.find('rg_meta notranslate')
        if start_line == -1:  # If no links are found then give an error!
            end_quote = 0
            link = "no_links"
            return link, end_quote
        
        else:
            start_line = page.find('class="rg_meta notranslate">')
            start_object = page.find('{', start_line + 1)
            end_object = page.find('</div>', start_object + 1)
            object_raw = str(page[start_object:end_object])
        
            try:
                object_decode = bytes(object_raw, "utf-8").decode("unicode_escape")
                final_object = json.loads(object_decode)
            except:
                final_object = ""
            return final_object, end_object
    
    async def get_all_items(self, page, argument):
        tasks = []
        count = 1
        
        while count <= int(argument['limit']):
        
            image_meta_data, end_content = await self.get_next_item(page)
            
            if image_meta_data == "no_links":
                break
            
            elif image_meta_data == "":
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
        content = await self.download_url_data(url, 'bytes')
        if content != None:
            await self.write_to_file(url, content, sub_dir)
        else:
            print(f'***File not write: {url}')
        
        
    async def multi_image_download_task(self, argument: list) -> None:
        search_term, params, url, similar_images, specific_site, safe_search = await self.build_url_parameters(argument)
        url = await self.build_search_url(search_term, params, url, similar_images, specific_site, safe_search)
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
    s = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - s
    print(f"Execution time: {elapsed:0.3f} seconds.")
