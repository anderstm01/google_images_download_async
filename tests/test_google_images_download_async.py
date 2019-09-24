
#Builtin imports:
import pytest
import os
import sys
import shutil
import json
from pathlib import Path

#Third party imports:
import pytest_asyncio
import asyncio

#Local imports:
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config_parser import parse_config
from google_images_download_async import GoogleImagesDownloader, expand_arguments, SilentMode



@pytest.mark.asyncio
async def test_image_download_task():
    """
    test async image download
    """
    with open(Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))).joinpath('url_parms.json')) as file:
        url_parm_json_file = json.load(file)
        
        
    prefix, suffix = '', ''
    
    gids = [[GoogleImagesDownloader(url_parm_json_file,{"prefix":'',"suffix":''}), ['','']],
            [GoogleImagesDownloader(url_parm_json_file,{"prefix":'pre',"suffix":''}), ['pre ','']],
            [GoogleImagesDownloader(url_parm_json_file,{"prefix":'',"suffix":'suf'}), ['',' suf']],
            [GoogleImagesDownloader(url_parm_json_file,{"prefix":'pre',"suffix":'suf'}), ['pre ',' suf']]]
    
    test_data =  [['https://www.python.org/static/opengraph-icon-200x200.png',f'downloads/{prefix}opengraph-icon-200x200{suffix}.png'],
                  ['https://www.python.org/static/opengraph-icon-200.png',f'downloads/{prefix}opengraph-icon-200{suffix}.png'],
                  ['http://www.ufnwefnewnioewiofwe.com/image.jpg',f'downloads/{prefix}image{suffix}.jpg'],
                  ['https%3A%2F%2Fspecials-images.forbesimg.com%2Fdam%2Fimageserve%2F1055486686%2F960x0.jpg%3Ffit%3Dscale',f'downloads/{prefix}960x0{suffix}.jpg'],
                  ['bad url','bad url']]
                


    test_expected_resp =  [[None,True],
                           [None,False],
                           [None,False],
                           [None,True],
                           [None,False]]
                          

    for gid, prefix_suffix in gids:
        for i in zip(test_data,test_expected_resp):
            res = await gid.image_download_task(i[0][0])
            assert None == i[1][0]
            prefix = prefix_suffix[0]
            suffix = prefix_suffix[1]
            assert os.path.exists(i[0][1]) == i[1][1]

    shutil.rmtree('downloads')

@pytest.mark.asyncio
async def test_silent_mode(capsys):
    """
    test SilentMode() 
    """
    test_data = [True,False]

    for tests in test_data:

        orginal_stdout = sys.stdout 

        async with SilentMode(tests):
            new_stdout =  sys.stdout
            if tests == True:
                assert sys.stdout != orginal_stdout
                assert orginal_stdout != new_stdout
                assert sys.stdout == new_stdout

            if tests == False:
                assert sys.stdout == orginal_stdout
                assert orginal_stdout == new_stdout
                assert sys.stdout == new_stdout

        assert sys.stdout == orginal_stdout
        
