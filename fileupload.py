import cloudinary
from cloudinary import CloudinaryImage
import cloudinary.uploader
import cloudinary.api
import os
from dotenv import load_dotenv

load_dotenv()
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


def upload_image(file_object, filename):
    if len(file_object)>5:
        return {"error": "You can only upload up to 5 images at a time."}
    
    image_urls=[]
    cloudinary.uploader.upload(file_object,
                               public_id=filename,
                               unique_filename=False,
                               overwrite=True)
    src_url = CloudinaryImage(filename).build_url()
    image_urls.append(src_url)
    return src_url


def delete_image(filename):
    cloudinary.uploader.destroy(filename)