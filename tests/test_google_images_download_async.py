
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

with open(Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))).joinpath('url_parms.json')) as file:
    url_parm_json_file = json.load(file)


@pytest.mark.asyncio
async def test_image_download_task():
    """
    test async image download
    """        
        
    prefix, suffix = '', ''
    
    gids = [[GoogleImagesDownloader(url_parm_json_file,{"prefix":'',"suffix":''}), ['','']],
            [GoogleImagesDownloader(url_parm_json_file,{"prefix":'pre',"suffix":''}), ['pre ','']],
            [GoogleImagesDownloader(url_parm_json_file,{"prefix":'',"suffix":'suf'}), ['',' suf']],
            [GoogleImagesDownloader(url_parm_json_file,{"prefix":'pre',"suffix":'suf'}), ['pre ',' suf']]]
    
    test_data =  [['https://www.python.org/static/opengraph-icon-200x200.png',f'Downloads/{prefix}opengraph-icon-200x200{suffix}.png'],
                  ['https://www.python.org/static/opengraph-icon-200.png',f'Downloads/{prefix}opengraph-icon-200{suffix}.png'],
                  ['http://www.ufnwefnewnioewiofwe.com/image.jpg',f'Downloads/{prefix}image{suffix}.jpg'],
                  ['https%3A%2F%2Fspecials-images.forbesimg.com%2Fdam%2Fimageserve%2F1055486686%2F960x0.jpg%3Ffit%3Dscale',f'Downloads/{prefix}960x0{suffix}.jpg'],
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

    shutil.rmtree('Downloads')

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

@pytest.mark.asyncio
async def test_download_url_data(capsys):
    """
    test image download method
    """
    
    test_resp_place_holder = ''

    test_data = [['https://www.python.org/static/opengraph-icon-200x200.png','bytes'],

                 ['https://www.google.com/search?rlz=1CACBUY_enUS865&tbm=isch&sxsrf=' +
                  'ACYBGNSOFkjkRV_jlxY7_04l8lVUkA3yXw:1569373001538&q=python&chips=q' +
                  ':python,g_1:logo:ctsVDjMBDgY%3D&usg=AI4_-kTQt5Yjgzs6XSoeHlcjjpues' +
                  'pKMKw&sa=X&ved=0ahUKEwil6JqC4urkAhVpc98KHSqMAQoQ4lYINigF&biw=1920' +
                  '&bih=977&dpr=1','text'],

                 ['https://www.python.org/static/opengraph-icon-200.png','bytes']]

    gid = GoogleImagesDownloader(url_parm_json_file,{})
    for i, tests in enumerate(test_data):

        test_expected_resp = [[type(b''), f'Begin downloading {tests[0]}\nFinished downloading {tests[0]}\n'],
                              [type(''), f'Begin downloading {tests[0]}\nFinished downloading {tests[0]}\n'],
                              [type(None), (f'Begin downloading {tests[0]}\n***Unable to download {tests[0]},' +
                                            ' HTTP Status Code was 404\n')]]

        res = await gid.download_url_data(tests[0], tests[1])
        assert type(res) == test_expected_resp[i][0]

        captured = capsys.readouterr()
        assert captured.out == test_expected_resp[i][1]


try:        
    shutil.rmtree('Downloads')
except:
    pass
