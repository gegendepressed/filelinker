import cloudinary
from cloudinary import CloudinaryImage
import cloudinary.uploader
import cloudinary.api
import os,uuid
from dotenv import load_dotenv

load_dotenv()
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


def upload_image(file_objects, filenames):
    if not file_objects: 
        return []
    
    if len(file_objects) > 5:
        raise ValueError("You can only upload up to 5 images.")
    
    uploaded_urls = []

    for file_object in file_objects:
        unique_filename = str(uuid.uuid4())
        
        response = cloudinary.uploader.upload(file_object,
                                              public_id=unique_filename,
                                              unique_filename=False,
                                              overwrite=False)
        src_url = CloudinaryImage(unique_filename).build_url()
        uploaded_urls.append(src_url)

    return uploaded_urls

def delete_image(filenames):
    for filename in filenames:
     cloudinary.uploader.destroy(filename, invalidate=True)
