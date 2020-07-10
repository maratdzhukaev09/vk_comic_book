import requests
import os
import random
from dotenv import load_dotenv


def download_picture(url, filename):
    response = requests.get(url)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)


def get_response(url, params={}):
    response = requests.get(url, params=params)
    response.raise_for_status()
    response_dict = response.json()

    if response.status_code != 200:
        raise requests.exceptions.HTTPError(response.status_code)
    elif 'error' in response_dict:
        raise requests.exceptions.HTTPError(response_dict['error'])
    else:
        return response


def get_vk_api_response(api_method, params, requests_method, vk_access_token):
    params["access_token"] = vk_access_token
    params["v"] = "5.120"
    url = f"https://api.vk.com/method/{api_method}/"

    if requests_method == "GET":
        response = get_response(url, params=params)
    elif requests_method == "POST":
        response = get_response(url, params=params)
    
    return response.json()


def get_last_comic_number():
    url = f"http://xkcd.com/info.0.json"
    response = get_response(url)
    last_comic_number = response.json()["num"]

    return last_comic_number


def get_comic():
    url = f"http://xkcd.com/{random.randrange(0, get_last_comic_number())}/info.0.json"
    response = get_response(url)
    response_dict = response.json()
    picture_url = response_dict["img"]
    picture_comment = response_dict["alt"]
    picture_filename = picture_url.split("/")[-1]
    download_picture(picture_url, picture_filename)

    return picture_comment, picture_filename


def save_photo(picture_filename, server_url, vk_access_token, vk_group_id):
    with open(picture_filename, "rb") as file:
        url = server_url
        files = {"photo": file}
        response = requests.post(url, files=files)
        response.raise_for_status()

    response_dict = response.json()
    vk_hash = response_dict["hash"]
    vk_server = response_dict["server"]
    vk_photo = response_dict["photo"]
    
    params = {
        "server": vk_server,
        "group_id": vk_group_id,
        "hash": vk_hash,
        "photo": vk_photo
    }
    photos_info = get_vk_api_response("photos.saveWallPhoto", params, "POST", vk_access_token)

    return photos_info


def publish_photo(photos_info, picture_comment, vk_access_token, vk_group_id):
    params = {
        "owner_id": f"-{vk_group_id}",
        "from_group": 1,
        "message": picture_comment,
        "attachments": f"photo{photos_info['response'][0]['owner_id']}_{photos_info['response'][0]['id']}"
    }
    response_dict = get_vk_api_response("wall.post", params, "POST", vk_access_token)

    return response_dict


def main():
    try:
        load_dotenv()
        vk_access_token = os.getenv("VK_ACCESS_TOKEN")
        vk_group_id = os.getenv("VK_GROUP_ID")

        picture_comment, picture_filename = get_comic()

        json_data = get_vk_api_response(
            "photos.getWallUploadServer",
            {"group_id": vk_group_id},
            "GET",
            vk_access_token
        )
        server_url = json_data["response"]["upload_url"]

        photos_info = save_photo(picture_filename, server_url,  vk_access_token, vk_group_id)
        publish_photo(photos_info, picture_comment, vk_access_token, vk_group_id)
    finally:
        directory = os.listdir(".")
        for file in directory:
            if ".png" in file:
                os.remove(file)


if __name__ == "__main__":
    main()