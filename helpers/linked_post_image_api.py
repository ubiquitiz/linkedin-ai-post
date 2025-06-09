import requests
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
ACCESS_TOKEN = os.getenv('LINKEDIN_ACCESS_TOKEN')
def upload_image_from_url_to_linkedin(image_url):
    """
    Upload an image from a URL to LinkedIn's media platform and return the asset ID.

    Parameters:
    - access_token: Your LinkedIn OAuth access token
    - image_url: URL of the image to upload
    - organization_id: Optional - if posting as an organization

    Returns:
    - asset_id: The ID of the uploaded image asset
    """
    # Step 1: Download the image from URL
    image_response = requests.get(image_url)
    if image_response.status_code != 200:
        raise Exception(f"Failed to download image: {image_response.status_code}")

    image_data = image_response.content

    # Step 2: Register Upload with LinkedIn
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }

    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"

    # Prepare registration request
    register_data = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"{os.getenv('PERSON_URN')}",
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }

    register_response = requests.post(register_url, headers=headers, json=register_data)

    if register_response.status_code != 200:
        raise Exception(f"Failed to register upload: {register_response.text}")

    register_data = register_response.json()
    print(f"Register Data: {register_data}")

    # Extract upload URL and asset ID from response
    upload_url = \
    register_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
    asset_id = register_data['value']['asset']

    # Step 3: Upload the image binary to the provided URL
    upload_response = requests.put(
        upload_url,
        data=image_data,
        headers={
            'Content-Type': 'image/jpeg'
        }
    )

    if upload_response.status_code not in [200, 201]:
        raise Exception(f"Failed to upload image: {upload_response.status_code}, {upload_response.text}")

    return {
        "asset_id": asset_id,
        "upload_status": upload_response.status_code,
        "register_response": register_data
    }


def prepare_image_upload(image_url):
    """
    Prepare the image data and metadata for uploading to LinkedIn.

    Parameters:
    - image_url: URL of the image to upload

    Returns:
    - A dictionary containing image data, content type, and registration payload
    """
    # Step 1: Download the image from URL
    print(f"Downloading image from URL: {image_url}")
    image_response = requests.get(image_url)
    if image_response.status_code != 200:
        raise Exception(f"Failed to download image: {image_response.status_code}")

    image_data = image_response.content

    # Get file name and type from URL
    url_path = urlparse(image_url).path
    file_name = os.path.basename(url_path)
    file_extension = os.path.splitext(file_name)[1].lower()

    # Map file extension to content type
    content_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif'
    }
    content_type = content_types.get(file_extension, 'image/jpeg')  # Default to JPEG

    # Prepare registration payload
    register_data = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"{os.getenv('LINKEDIN_PERSON_URN')}",
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }

    return {
        "image_data": image_data,
        "content_type": content_type,
        "register_data": register_data
    }

def create_linkedin_post_with_image(text, asset_id):
    """
    Create a LinkedIn post that includes the uploaded image

    Parameters:
    - access_token: Your LinkedIn OAuth access token
    - text: Text content of the post
    - asset_id: Asset ID returned from image upload
    - organization_id: Optional - if posting as an organization

    Returns:
    - Response from LinkedIn post-creation API
    """
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }

    # Define the author based on whether it's a person or org post
    author = f"urn:li:person:{os.getenv('LINKEDIN_PERSON_URN')}"

    post_data = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "media": asset_id
                    }
                ],
                "shareCommentary": {
                    "text": text
                },
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    post_url = "https://api.linkedin.com/v2/ugcPosts"
    post_response = requests.post(post_url, headers=headers, json=post_data)

    if post_response.status_code not in [200, 201]:
        raise Exception(f"Failed to create post: {post_response.status_code}, {post_response.text}")

    return post_response.json()
