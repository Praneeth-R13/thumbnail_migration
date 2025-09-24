from PIL import Image
from tqdm import tqdm
from sqlalchemy.sql import Select
from sqlalchemy import create_engine, update
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import Session
from elasticsearch import Elasticsearch, exceptions
from langchain_core.runnables import RunnableLambda, RunnableParallel
from utils import download_image_from_s3, compress_and_save_as_webp, compress_and_save_as_png, upload_to_s3, generate_blurhash, sizes, IMAGE_TYPE
from sqlalchemy.orm import sessionmaker
from db import Base, Content, Proposal, Domain
import logging
import csv
import gc
import os
from dotenv import load_dotenv

load_dotenv()

ES_HOSTNAME= os.getenv("ES_HOSTNAME")
ES_PORT= os.getenv("ES_PORT")
ES_USERNAME= os.getenv("ES_USERNAME")
ES_PASSWORD= os.getenv("ES_PASSWORD")
APP_STAGE= os.getenv("APP_STAGE")

print(ES_HOSTNAME, ES_PORT, ES_USERNAME, ES_PASSWORD, APP_STAGE)

Image.MAX_IMAGE_PIXELS = 100000000

logging.basicConfig(
    filename='prod_error.log', 
    level=logging.ERROR, 
    format='%(message)s'
)

def get_db_session():
    SQLALCHEMY_DATABASE_URL_READER = (
        os.getenv("SQLALCHEMY_DATABASE_URL_READER")
    )
    SQLALCHEMY_DATABASE_URL_WRITER = (
        os.getenv("SQLALCHEMY_DATABASE_URL_WRITER")
    )

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

def add_to_es(thumbnail_data, domain_id, batch_start):
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
                "_index": f"{domain_id}_dev_image",
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
    try:
        response = es.bulk(body=actions, refresh=True)
        # print(f"Batch upsert completed: {response}")
    except exceptions.ElasticsearchException as e:
        # print(f"Failed to perform batch upsert: {e}")
        logging.error(f"ES update failed for domain: {domain_id} | Offset: {batch_start}. Error: {e}")
    es.close()
    del es
    del actions
    gc.collect()

def process_row(row_data):
    try: 
        if(row_data.get('thumbnail_info') and row_data.get('thumbnail_info').get('thumbnail_location') and not row_data.get('thumbnail_info').get('thumbnail_location').get('png')):
            thumbnail_info = row_data.get('thumbnail_info') or {}
            s3_url = row_data['metadata_']['image_url'].replace("%2F", "/")
            try:
                img, bucket, base_path, filename = download_image_from_s3(s3_url)
            except Image.DecompressionBombError as e:
                with open('big_image_prod.csv', 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([row_data['id'], row_data['domain_id'], e, "Image too big"])
                return None
            original_resolution = img.size
            max_width, max_height = original_resolution

            results = {}
            results["raw"] = s3_url

            
            if max_width >= 240 and max_height >= 240:
                img_resized = img.copy()
                img_resized.thumbnail((240, 240), Image.LANCZOS)


                png_image = compress_and_save_as_png(img_resized)
                results["png"] = upload_to_s3(
                    png_image, base_path, f"{filename}_png.png", bucket, IMAGE_TYPE
                )
                
                # Update thumbnail_info with the png key inside thumbnail_location
                if "thumbnail_location" not in thumbnail_info:
                    thumbnail_info["thumbnail_location"] = {}
                thumbnail_info["thumbnail_location"]["png"] = results["png"]
                del img_resized
                del png_image
                gc.collect()
            
            
            del img
            del results
            gc.collect()
            return thumbnail_info
        
    except Exception as e:
        with open('error.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            
            writer.writerow([row_data.get('id'), e, "Failed to create thumbnail"])
        return None

def create_task(record):
        # Create a RunnableLambda for processing a specific section
        return RunnableLambda(lambda _: process_row(record))

def process_domain(domain):
    domain_id = str(domain)
    #domain_id = domain
    print(f"Processing Domain: {domain_id}")
    db_session = get_db_session()
    query = (
        db_session.query(Content.id, Content.domain_id, Content.metadata_, Content.thumbnail_info)
        .join(Proposal, Content.proposal_id == Proposal.id)
        .filter(
            Proposal.is_deleted == False,
            Content.domain_id == domain_id,
            Content.status != 'DELETED',
            Content.content_type.contains('image'),

        )
        .execution_options(stream_results=True)
    )
    
    
    # Fetch records one by one and track progress
    total_records = query.count()
    
    batch_size = 20
    for batch_start in tqdm(range(0, total_records, batch_size)):
        try:
            # batch_end = min(batch_start + batch_size, total_records)
            batch_query = query.offset(batch_start).limit(batch_size)
            parallel_tasks = RunnableParallel(
                {
                    f"{record.id}": create_task({
                        'id': record.id,
                        'domain_id': record.domain_id,
                        'metadata_': record.metadata_,
                        'thumbnail_info': record.thumbnail_info
                    })
                    for record in batch_query.yield_per(batch_size)
                }
            )
            result = parallel_tasks.invoke({})
            thumbnail_data = []
            for id, thumbnail_info in result.items():
                if thumbnail_info:
                    # Find the record and update it directly
                    record = db_session.query(Content).filter(Content.id == id).first()
                    if record:
                        record.thumbnail_info = thumbnail_info
                        flag_modified(record, 'thumbnail_info')
                    
                    thumbnail_data.append({
                        "id": id,
                        "thumbnail_info": thumbnail_info
                    })
            if len(thumbnail_data) > 0: 
                add_to_es(thumbnail_data, domain_id, batch_start)
            del thumbnail_data  
            del result
            del parallel_tasks
            del batch_query
            gc.collect()
        except Exception as e:
            logging.error(f"Failed to process batch for domain: {domain_id} | Offset: {batch_start}. Error: {e}")
    db_session.commit()
    db_session.close()
    del db_session
    del query
    gc.collect()

if __name__ == "__main__":
    print("Creating DB Session")
    db_session = get_db_session()

    print("Querying Domains")
    domains = db_session.query(Domain).all()
    db_session.close()
    # domains = ["7e9ec0fc-8b9f-4e96-a246-17751572c5ef"]
    for domain in tqdm(domains):
        if domain=="7e9ec0fc-8b9f-4e96-a246-17751572c5ef" or domain=="8ce2a320-bba6-4d5f-9543-a7b2b28736ee":
            continue
        print(f"Processing Domain: {domain.id}")
        process_domain(domain.id)

    print("Migration Completed.")

    
