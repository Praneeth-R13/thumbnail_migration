import boto3
from io import BytesIO
from PIL import Image
from urllib.parse import urlparse
import blurhash
import gc
# import warnings

# warnings.simplefilter('error', Image.DecompressionBombWarning)

WEBP_COMPRESSION_QUALITY = 85

sizes = {
    "96w": (96, 96),
    "240w": (240, 240),
    "480w": (480, 480),
    "1080w": (1080, 1080),
}

IMAGE_TYPE = "extracted"

def upload_to_s3(file_obj, original_path, filename, bucket_name, type="extracted"):
    if type == "extracted":
        prefix = original_path.replace("images/", "image-thumbnail/")
        key = f"{prefix}/{filename}"
    else:
        prefix = original_path.replace("inputs/", "thumbnail/")
        key = f"{prefix}/{filename}"

    s3_client = boto3.client("s3")
    s3_client.upload_fileobj(
        file_obj, bucket_name, key, ExtraArgs={"ContentType": "image/webp"}
    )
    return f"https://{bucket_name}.s3.amazonaws.com/{key}"

def compress_and_save_as_webp(img):
    webp_image = BytesIO()
    img.save(webp_image, format="WEBP", quality=WEBP_COMPRESSION_QUALITY)
    webp_image.seek(0)
    return webp_image

def download_image_from_s3(s3_url):
    # try:
    parsed_url = urlparse(s3_url)
    bucket_name = parsed_url.netloc.split(".")[0]
    key = parsed_url.path.lstrip("/")

    s3_client = boto3.client("s3")
    image_obj = BytesIO()
    s3_client.download_fileobj(bucket_name, key, image_obj)
    image_obj.seek(0)
    filename = key.rsplit("/", 1)[-1].split(".")[
        0
    ]  # Extract filename without extension
    base_path = key.rsplit("/", 1)[0]  # Extract base path
    img = Image.open(image_obj)
    # except Image.DecompressionBombWarning as e:
    #     img = None
    #     del image_obj
    #     gc.collect()
    #     raise Image.DecompressionBombError(f"Decompression bomb warning: {e}")    
    return img, bucket_name, base_path, filename

def generate_blurhash(img):
    img_resized = img.resize((32, 32))
    return blurhash.encode(img_resized,x_components=4, y_components=4)
