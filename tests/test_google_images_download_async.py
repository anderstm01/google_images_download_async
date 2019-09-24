
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
        
    GID = GoogleImagesDownloader(url_parm_json_file,{})

    test_data = [['https://www.python.org/static/opengraph-icon-200x200.png','downloads/opengraph-icon-200x200.png'],
                 ['https://www.python.org/static/opengraph-icon-200.png','downloads/opengraph-icon-200.png'],
                 ['http://www.ufnwefnewnioewiofwe.com/image.jpg','downloads/image.jpg'],
                 ['https%3A%2F%2Fspecials-images.forbesimg.com%2Fdam%2Fimageserve%2F1055486686%2F960x0.jpg%3Ffit%3Dscale','downloads/960x0.jpg'],
                 ['bad url','bad url']]

    test_expected_resp = [[None,True],
                          [None,False],
                          [None,False],
                          [None,True],
                          [None,False]]

    for i in zip(test_data,test_expected_resp):
        res = await GID.image_download_task(i[0][0])
        assert None == i[1][0]
        assert os.path.exists(i[0][1]) == i[1][1]

    shutil.rmtree('downloads')

