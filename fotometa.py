#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Google, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Gets lots of Metadata from Photos"""

import argparse
import base64
import sys
import io
import codecs
import json

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from PIL import Image
from PIL import ImageDraw


# [START get_vision_service]
def get_vision_service():
    credentials = GoogleCredentials.get_application_default()
    return discovery.build('vision', 'v1', credentials=credentials)
# [END get_vision_service]

def get_base64(file_content):
    """returns file as base64 encoded string"""
    return base64.b64encode(file_content).decode('utf-8')

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def compress_to_base64(file_handle, max_size=5500000):
    """compresses a file as long its to big"""
    start_quality = 90
    quality_step = 5
    original_file = file_handle.read()
    tmp_file = original_file
    
    while len(get_base64(tmp_file)) > max_size:
        sys.stderr.write('Skipping Image: Too big for API ( '+str(len(get_base64(tmp_file))/1024)+' KB)\n')
        img = Image.open(file_handle)
        tmp = io.BytesIO()
        img.save(tmp, 'JPEG', quality=start_quality)
        tmp.seek(0)
        tmp_file = tmp.getvalue()
        start_quality = start_quality - quality_step

    img_size = len(get_base64(tmp_file))
    sys.stderr.write('Final Image Size: '+str(img_size/1024)+' KB\n')
    return get_base64(tmp_file)

def get_vision_api_data(file_handle, max_results=10):
    """Uses the Vision API to fetch metadata"""
    image_base64 = compress_to_base64(file_handle)
    
    batch_request = [{
        'image': {
            'content': image_base64
            },
        'features': [{
            'type': 'FACE_DETECTION',
            'maxResults': max_results,
            },{
            'type': 'LANDMARK_DETECTION',
            'maxResults': max_results,
            },{
            'type': 'LOGO_DETECTION',
            'maxResults': max_results,
            },{
            'type': 'LABEL_DETECTION',
            'maxResults': max_results,
            },{
            'type': 'TEXT_DETECTION',
            'maxResults': max_results,
            },{
            'type': 'IMAGE_PROPERTIES',
            'maxResults': max_results,
            },{
            'type': 'SAFE_SEARCH_DETECTION',
            'maxResults': max_results,
            }]
        }]
    
    sys.stderr.write('Requesting ...')
    service = get_vision_service()
    request = service.images().annotate(body={
        'requests': batch_request,
        })
    response = request.execute()
    """print(response)"""
    return response
    """['responses'][0]"""

def detect_face(face_file, max_results=4):
    """Uses the Vision API to detect faces in the given file.

    Args:
        face_file: A file-like object containing an image with faces.

    Returns:
        An array of dicts with information about the faces in the picture.
    """
    image_content = face_file.read()
    batch_request = [{
        'image': {
            'content': base64.b64encode(image_content).decode('utf-8')
            },
        'features': [{
            'type': 'FACE_DETECTION',
            'maxResults': max_results,
            }]
        }]

    service = get_vision_service()
    request = service.images().annotate(body={
        'requests': batch_request,
        })
    response = request.execute()

    return response['responses'][0]['faceAnnotations']


def highlight_faces(image, faces, output_filename):
    """Draws a polygon around the faces, then saves to output_filename.

    Args:
      image: a file containing the image with the faces.
      faces: a list of faces found in the file. This should be in the format
          returned by the Vision API.
      output_filename: the name of the image file to be created, where the
          faces have polygons drawn around them.
    """
    im = Image.open(image)
    draw = ImageDraw.Draw(im)

    for face in faces:
        box = [(v.get('x', 0.0), v.get('y', 0.0))
               for v in face['fdBoundingPoly']['vertices']]
        draw.line(box + [box[0]], width=5, fill='#00ff00')

    im.save(output_filename)


def main(input_filename, output_filename, max_results):
    """for filename in os.listdir(directory):
    if filename.endswith(".asm") or filename.endswith(".py"): 
        # print(os.path.join(directory, filename))
        continue
    else:
        continue"""
    with open(input_filename, 'rb') as image:
        output_data = get_vision_api_data(image, max_results)
        output_json = json.dumps(output_data, indent=2, ensure_ascii=True)
        if len(output_json)>0:
            fo = open(output_filename,'w')
            fo.write(output_json)
            fo.close()
            print("written file "+output_filename)
        else:
            print("NO Json file written. Zero length.");
        #faces = detect_face(image, max_results)
        #print('Found {} face{}'.format(
        #    len(faces), '' if len(faces) == 1 else 's'))

        #print('Writing to file {}'.format(output_filename))
        # Reset the file pointer, so we can read the file again
        #image.seek(0)
        #highlight_faces(image, faces, output_filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Detects faces in the given image.')
    parser.add_argument(
        'input_image', help='the image you\'d like to detect data in.')
    parser.add_argument(
        '--out', dest='output', default='out.json',
        help='the name of the output file.')
    parser.add_argument(
        '--max-results', dest='max_results', default=20,
        help='the max results of face detection.')
    args = parser.parse_args()

    main(args.input_image, args.output, args.max_results)
