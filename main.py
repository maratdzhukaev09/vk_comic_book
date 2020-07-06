import requests
import os
import random
from dotenv import load_dotenv

def download_picture(url, filename):
    response = requests.get(url)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)

def get_vk_api_response(api_method, params, requests_method):
    params["access_token"] = os.getenv("VK_ACCESS_TOKEN")
    params["v"] = "5.120"
    url = f"https://api.vk.com/method/{api_method}/"

    if requests_method == "GET":
        response = requests.get(url, params=params)
        response.raise_for_status()
    elif requests_method == "POST":
        response = requests.post(url, params=params)
        response.raise_for_status()
    
    return response.json()

def get_comic():
    url = f"http://xkcd.com/{random.randrange(0, 2328)}/info.0.json"
    response = requests.get(url)
    response.raise_for_status()

    picture_url = response.json()["img"]
    picture_comment = response.json()["alt"]
    picture_filename = picture_url.split("/")[-1]
    download_picture(picture_url, picture_filename)

    return picture_comment, picture_filename

def save_photo(picture_filename, server_url):
    with open(picture_filename, "rb") as file:
        url = server_url
        files = {"photo": file}
        response = requests.post(url, files=files)
        response.raise_for_status()

    hash = response.json()["hash"]
    server = response.json()["server"]
    photo = response.json()["photo"]
    
    params = {
        "server": server,
        "group_id": os.getenv('VK_GROUP_ID'),
        "hash": hash,
        "photo": photo
    }
    photos_info = get_vk_api_response("photos.saveWallPhoto", params, "POST")

    return photos_info

def publish_photo(photos_info, picture_comment):
    params = {
        "owner_id": f"-{os.getenv('VK_GROUP_ID')}",
        "from_group": 1,
        "message": picture_comment,
        "attachments": f"photo{photos_info['response'][0]['owner_id']}_{photos_info['response'][0]['id']}"
    }
    response_json = get_vk_api_response("wall.post", params, "POST")

    return response_json

def main():
    load_dotenv()
    picture_comment, picture_filename = get_comic()

    response_json = get_vk_api_response("photos.getWallUploadServer", {"group_id": os.getenv('VK_GROUP_ID')}, "GET")
    server_url = response_json["response"]["upload_url"]

    photos_info = save_photo(picture_filename, server_url)
    publish_photo(photos_info, picture_comment)

    os.remove(picture_filename)

if __name__ == "__main__":
    main()