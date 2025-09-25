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
        with open('prod_thumbnail_error.csv', 'a', newline='') as file:
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
    #domains = db_session.query(Domain).all()
    #db_session.close()
    #domains = ["05ed5f5b-8777-49b7-97cd-7a057488f749"]
    domains = [
  "285248ed-c186-4d5a-907f-e4534fbfe15d",
  "2ad8560e-29b9-47ac-922d-6075feda923a",
  "e6304aac-7ff8-4e15-a751-d94e095c97b6",
  "56ad5b18-4a1c-464d-8830-878d1daf5121",
  "f3e58caa-f29c-41f2-8ade-0b74587bf152",
  "d1ed1222-6677-4233-8786-33349d4529ca",
  "58a95c65-1941-420b-b32b-2fcc2652a84b",
  "1d38dc97-0d6a-4409-8d99-0ebb941ebbc7",
  "f6303c74-1afe-40c5-bdd5-23a96e998286",
  "718454e7-01be-485c-bad2-ab68715bbee9",
  "a5c6a017-9df2-42c2-9ca1-1a63b136ad56",
  "46e5d66a-833e-499f-914d-05ac6be9918f",
  "98e2acc9-b514-45cf-9e8f-6180e6e8338a",
  "49641675-ffb6-452f-8f77-b4e7517ffa24",
  "f20e0063-4f32-422e-afb8-167dfec41217",
  "4dc373e2-9494-4c83-806c-fbe17835f7cf",
  "d4aecbe2-d5c3-4b44-a309-c0ecd434b58c",
  "2473de36-a5aa-4cf6-83ab-9b6b88f573b7",
  "f01ef784-be74-45ac-8068-26d803bd3302",
  "d4a891bf-a977-452e-8bc2-cd68a1ffa520",
  "3261ef93-191b-4691-94a4-badc0c07f038",
  "ab358a1c-6731-4872-b3ee-a91a7213ac0a",
  "7b4109ab-6e52-4de6-8486-7b315c5a61e1",
  "8086008a-0e51-4854-8cb5-994944b26ddc",
  "36433986-be88-4707-901d-a27e4dec6de2",
  "1bce102e-7095-4d96-ae09-433715e8c007",
  "a9386eb2-85c3-43db-b09d-e1e6e569f909",
  "8ba6faed-d6c5-4ca2-99a5-105f411522d5",
  "2af213d0-ef86-45ca-a251-cf0bf95b6bd0",
  "486adf24-be96-4047-b9b5-db6e25e6fd2d",
  "1e40aed8-77cd-45a8-a79b-160a4f48a7bb",
  "7eaaadd2-e81e-4934-a378-70b94fdb5136",
  "363a69d8-a30b-4dcf-995f-fadbab9d8b2d",
  "c5b6186b-efc4-4014-91dd-e737072aa1f2",
  "bb8834e1-8385-4146-8808-0d2651038a52",
  "9733d3f3-20d2-4deb-bd83-2176011c4d57",
  "b36edc1a-a701-48e8-8d0c-cf9248fe2f28",
  "6fa169f9-0cd0-4cae-a105-2151de93d1e1"
    ];
    for domain in domains:
        if domain=="7e9ec0fc-8b9f-4e96-a246-17751572c5ef" or domain=="8ce2a320-bba6-4d5f-9543-a7b2b28736ee":
            continue
        print(f"Processing Domain: {domain}")
        #process_domain(domains)

    print("Migration Completed.")

    
