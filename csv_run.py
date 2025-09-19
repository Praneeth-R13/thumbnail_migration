import pandas as pd
from PIL import Image
from tqdm import tqdm
from sqlalchemy.sql import Select
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session
from elasticsearch import Elasticsearch, exceptions
from utils import download_image_from_s3, compress_and_save_as_webp, upload_to_s3, generate_blurhash, sizes, IMAGE_TYPE
from sqlalchemy.orm import sessionmaker
from db import Base, Content
import logging
import csv
import gc

ES_HOSTNAME="https://search.joist.ai"
ES_PORT="443" 
ES_USERNAME="fds_user"
ES_PASSWORD="QGzHpFm&Cosr#Y39j5ye"
APP_STAGE="prod"

Image.MAX_IMAGE_PIXELS = None

logging.basicConfig(
    filename='prod_error.log', 
    level=logging.ERROR, 
    format='%(message)s'
)

def get_db_session():
    SQLALCHEMY_DATABASE_URL_READER = (
        "postgresql://fds_prod:x7k*EdBw%3S9VYLakp$djha8j@fds-instance.cyqstyz3e64b.us-east-1.rds.amazonaws.com:5432/fds_prod"
    )
    SQLALCHEMY_DATABASE_URL_WRITER = (
        "postgresql://fds_prod:x7k*EdBw%3S9VYLakp$djha8j@fds-instance.cyqstyz3e64b.us-east-1.rds.amazonaws.com:5432/fds_prod"
    )
    # SQLALCHEMY_DATABASE_URL_READER = (
    #     "postgresql://fds_prod:x7k*EdBw%3S9VYLakp$djha8j@localhost:5434/fds_prod"
    # )
    # SQLALCHEMY_DATABASE_URL_WRITER = (
    #     "postgresql://fds_prod:x7k*EdBw%3S9VYLakp$djha8j@localhost:5432/fds_prod"
    # )

    engine_writer = create_engine(
        SQLALCHEMY_DATABASE_URL_WRITER, echo=False, future=True, pool_recycle=300
    )
    engine_reader = create_engine(
        SQLALCHEMY_DATABASE_URL_READER, echo=False, future=True, pool_recycle=300
    )

    class RoutingSession(Session):
        def get_bind(self, mapper=None, clause=None):
            if isinstance(clause, (Select)):
                return engine_reader
            else:
                return engine_writer

    Base.metadata.create_all(engine_writer)
    db_session = sessionmaker(class_=RoutingSession, autocommit=False, autoflush=True)
    session = db_session()
    return session

def add_to_es(thumbnail_data, domain_id):
    es = Elasticsearch(
        hosts=[ES_HOSTNAME + ":" + ES_PORT],
        http_auth=(ES_USERNAME, ES_PASSWORD),
        verify_certs=False,
        ssl_show_warn=False,
        retry_on_timeout=True,
        timeout=30,
    )
    actions = []
    for data in thumbnail_data:
        action = {
            "update":{
                "_index": f"{domain_id}_prod_image",
                "_id": data["id"]
            }
        }
        doc = {
            "doc": {
                "thumbnail_info": data["thumbnail_info"]
            },
            "doc_as_upsert": True #note
        }
        actions.append(action)
        actions.append(doc)
    # try:
    response = es.bulk(body=actions, refresh=True)
        # print(f"Batch upsert completed: {response}")
    # except exceptions.ElasticsearchException as e:
    #     # print(f"Failed to perform batch upsert: {e}")
    #     logging.error(f"ES update failed for domain: {thumbnail_data}")
    es.close()
    del es
    del actions
    gc.collect()

def process_row(row):
    try: 
        s3_url = row[2]["image_url"].replace("%2F", "/")
        img, bucket, base_path, filename = download_image_from_s3(s3_url)
        original_resolution = img.size
        max_width, max_height = original_resolution

        results = {}
        results["raw"] = s3_url

        # Save original compressed
        compressed_webp_image = compress_and_save_as_webp(img)
        results["compressed"] = upload_to_s3(
            compressed_webp_image,
            base_path,
            f"{filename}_compressed.webp",
            bucket,
            IMAGE_TYPE,
        )

        # Generate thumbnails only if the image has a high enough resolution
        for size_name, (target_width, target_height) in sizes.items():
            if max_width >= target_width and max_height >= target_height:
                img_resized = img.copy()
                img_resized.thumbnail((target_width, target_height), Image.LANCZOS)
                webp_image = compress_and_save_as_webp(img_resized)
                results[size_name] = upload_to_s3(
                    webp_image, base_path, f"{filename}_{size_name}.webp", bucket, IMAGE_TYPE
                )
                del img_resized
                del webp_image
                gc.collect()

        # Generate BlurHash
        blurhash_str = generate_blurhash(img)

        thumbnail_info = {
            "resolution": original_resolution,
            "thumbnail_location": results,
            "blurhash": blurhash_str,
        }
        del img
        del compressed_webp_image
        del results
        gc.collect()
        return thumbnail_info
    except Exception as e:
        with open('error.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([row[0], e, "Failed to create thumbnail"])
        return None

def process_record(content_id, db_session):
    record = (
        db_session.query(Content.id, Content.domain_id, Content.metadata_)
        .filter(
            Content.id == content_id,
            Content.thumbnail_info == None,
        )
    ).one_or_none()
    #print(type(record), record)
    if record:
        #print(f"processing: {record}")
        thumbnail_info = process_row(record)
        if thumbnail_info:
            thumbnail_data = [{
                    "id":content_id,
                    "thumbnail_info":thumbnail_info
                }]
            db_session.execute(
                update(Content),
                thumbnail_data
            )
            db_session.commit() 
            add_to_es(thumbnail_data, record[1])
        
        del record
        gc.collect()

if __name__ == "__main__":
    df = pd.read_csv("big_image_prod.csv", header=None)
    db_session = get_db_session()
    for id, row in tqdm(df.iterrows()):
        process_record(row[0], db_session)
        #break
    db_session.close()
    del db_session
    print("Migration Completed.")
