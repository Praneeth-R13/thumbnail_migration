from PIL import Image
from tqdm import tqdm
from sqlalchemy.sql import Select
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session
from elasticsearch import Elasticsearch, exceptions
from langchain_core.runnables import RunnableLambda, RunnableParallel
from utils import download_image_from_s3, compress_and_save_as_webp, upload_to_s3, generate_blurhash, sizes, IMAGE_TYPE
from sqlalchemy.orm import sessionmaker
from db import Base, Content, Domain, Proposal
import logging
import csv

ES_HOSTNAME="https://search.joist.ai"
ES_PORT="443" 
ES_USERNAME="fds_user"
ES_PASSWORD="QGzHpFm&Cosr#Y39j5ye"
APP_STAGE="dev"

logging.basicConfig(
    filename='error.log', 
    level=logging.ERROR, 
    format='%(message)s'
)

def get_db_session():
    SQLALCHEMY_DATABASE_URL_READER = (
        "postgresql://fds_dev:4duyNK2Npr9AYrnc2t!qj24Bb@fds-dev-cluster.cluster-cyqstyz3e64b.us-east-1.rds.amazonaws.com:5432/fds_dev"
    )
    SQLALCHEMY_DATABASE_URL_WRITER = (
        "postgresql://fds_dev:4duyNK2Npr9AYrnc2t!qj24Bb@fds-dev-cluster.cluster-cyqstyz3e64b.us-east-1.rds.amazonaws.com:5432/fds_dev"
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
        #print("updating ES") 
        response = es.bulk(body=actions, refresh=True)
        # print(f"Batch upsert completed: {response}")
    except exceptions.ElasticsearchException as e:
        # print(f"Failed to perform batch upsert: {e}")
        logging.error(f"ES update failed for domain: {domain_id} | Offset: {batch_start}. Error: {e}")
    es.close()

def process_row(row):
    try: 
        s3_url = row.metadata_["image_url"].replace("%2F", "/")
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

        # Generate BlurHash
        blurhash_str = generate_blurhash(img)

        thumbnail_info = {
            "resolution": original_resolution,
            "thumbnail_location": results,
            "blurhash": blurhash_str,
        }
        return thumbnail_info
    except Exception as e:
        with open('error.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([row.id, e, "Failed to create thumbnail"])
        return None

def create_task(record):
        # Create a RunnableLambda for processing a specific section
        return RunnableLambda(lambda _: process_row(record))

def process_domain(domain):
    domain_id = str(domain.id)
    print(f"Processing Domain: {domain_id}")
    db_session = get_db_session()
    query = (
        db_session.query(Content.id, Content.domain_id, Content.metadata_)
        .join(Proposal, Content.proposal_id == Proposal.id)
        .filter(
            Proposal.is_deleted == False,
            Content.domain_id == domain_id,
            Content.status != 'DELETED',
            Content.content_type.contains('image')
        )
        .execution_options(stream_results=True)
    )
    
    # Fetch records one by one and track progress
    total_records = query.count()
    print(f"Records in Domain: {total_records}")
    batch_size = 1000
    for batch_start in tqdm(range(0, total_records, batch_size)):
        try:
            batch_end = min(batch_start + batch_size, total_records)
            batch_query = query.offset(batch_start).limit(batch_size)

            parallel_tasks = RunnableParallel(
                {
                    f"{record.id}": create_task(record)
                    for record in batch_query.yield_per(batch_size)
                }
            )
            result = parallel_tasks.invoke({})
            thumbnail_data = []
            for id, thumbnail_info in result.items():
                if thumbnail_info:
                    thumbnail_data.append({
                        "id": id,
                        "thumbnail_info": thumbnail_info
                    })
            if len(thumbnail_data) > 0: 
                db_session.execute(
                    update(Content),
                    thumbnail_data
                )
                db_session.commit()
                add_to_es(thumbnail_data, domain_id, batch_start)  
        except Exception as e:
            logging.error(f"Failed to process batch for domain: {domain_id} | Offset: {batch_start}. Error: {e}")
    db_session.close()

if __name__ == "__main__":
    print("Creating DB Session")
    db_session = get_db_session()

    print("Querying Domains")
    domains = db_session.query(Domain).all()
    db_session.close()

    for domain in tqdm(domains):
        process_domain(domain)

    print("Migration Completed.")
