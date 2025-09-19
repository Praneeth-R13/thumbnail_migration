from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DATE, Column, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import (
    UUID,
    VARCHAR,
    JSON,
    TIMESTAMP,
    JSONB,
    BOOLEAN,
    INTEGER,
    TEXT,
    ARRAY,
)
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from uuid import uuid4
import datetime
from datetime import timedelta
from enum import Enum

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True, index=True)
    name = Column(VARCHAR)
    email = Column(VARCHAR)
    cognito_username = Column(VARCHAR)
    cognito_pool_id = Column(VARCHAR)
    user_role = Column(VARCHAR)
    domain_id = Column(UUID, nullable=True)
    company_name = Column(VARCHAR)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    update_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    domain_join = Column(VARCHAR)
    status = Column(VARCHAR)
    user_config = Column(JSONB)

    User = relationship("Domain")
    User2 = relationship("Proposal")
    User3 = relationship("Domain_invite")
    User4 = relationship("workspace")
    User5 = relationship("Analytic_Upload")
    User6 = relationship("User_Search_History")
    User7 = relationship("RFx_Upload")


class Domain(Base):
    __tablename__ = "domains"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(VARCHAR)
    subdomain = Column(VARCHAR, nullable=True)
    policy = Column(VARCHAR)
    owner = Column(UUID, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    update_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    active = Column(Boolean, default=True)
    access_control = Column(JSON)
    chat_instructions = Column(JSON)

    domain = relationship("Proposal")
    domain2 = relationship("Domain_invite")
    domain3 = relationship("Analytic_Upload")
    domain4 = relationship("RFx_Upload")


class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    proposal_name = Column(VARCHAR)
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    location = Column(VARCHAR)
    client = Column(VARCHAR)
    market_sectors = Column(ARRAY(TEXT))
    tags = Column(MutableDict.as_mutable(JSONB))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    last_modified_date = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    fine_tuned = Column(BOOLEAN, default=False)
    linearized = Column(BOOLEAN, default=False)
    linearized_location = Column(VARCHAR)
    compressed_location = Column(VARCHAR)
    linearized_compress_location = Column(VARCHAR)
    proposal_sha_id = Column(VARCHAR)
    total_pages = Column(INTEGER)
    status = Column(VARCHAR)
    file_type = Column(VARCHAR)
    file_extension = Column(VARCHAR)
    notes = Column(VARCHAR)
    hidden_from_search = Column(Boolean, default=False)
    hidden_from_search_manual = Column(Boolean, default=False)
    source = Column(VARCHAR)
    pages_hidden_from_search = Column(JSONB)
    document_type = Column(VARCHAR)
    status_object = Column(MutableDict.as_mutable(JSON))
    is_deleted = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "proposal_name": self.proposal_name,
            "created_by_user": self.created_by_user,
            "created_for_domain": self.created_for_domain,
            "location": self.location,
            "client": self.client,
            "market_sector": self.market_sectors,
            "tags": self.tags,
            "created_at": self.created_at,
            "fine_tuned": self.fine_tuned,
            "linearized": self.linearized,
            "linearized_location": self.linearized_location,
            "compressed_location": self.compressed_location,
            "linearized_compress_location": self.linearized_compress_location,
            "proposal_sha_id": self.proposal_sha_id,
            "total_pages": self.total_pages,
            "status": self.status,
            "file_type": self.file_type,
            "file_extension": self.file_extension,
            "notes": self.notes,
            "hidden_from_search": self.hidden_from_search,
        }


class Domain_invite(Base):
    __tablename__ = "domain_invites"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    invited_by = Column(UUID, ForeignKey("users.id"))
    email = Column(VARCHAR)
    status = Column(VARCHAR)
    expires_on = Column(
        TIMESTAMP, default=str(datetime.datetime.utcnow() + timedelta(days=7))
    )
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    active = Column(Boolean, default=True)
    join_type = Column(VARCHAR)
    user_role = Column(VARCHAR)


class workspace(Base):
    __tablename__ = "workspaces"
    id = Column(UUID, primary_key=True, default=uuid4)
    user = Column(UUID, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    saved_searches = Column(JSON)
    workspace_data = Column(JSON)


class Workspace_Document(Base):
    __tablename__ = "workspace_document"
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_name = Column(VARCHAR)
    document_content = Column(JSON)
    client = Column(VARCHAR)
    market_sector = Column(VARCHAR)
    tags = Column(MutableDict.as_mutable(JSONB))
    due_date = Column(DATE)
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_by = Column(VARCHAR)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    active = Column(Boolean, default=True)


class Library(Base):
    __tablename__ = "library"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_name = Column(VARCHAR)
    document_content = Column(JSON)
    document_html = Column(VARCHAR)
    metadata_ = Column(MutableDict.as_mutable(JSONB))
    tags = Column(ARRAY(TEXT))
    collections = Column(MutableDict.as_mutable(JSONB))
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_by = Column(UUID)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    similarity = Column(ARRAY(TEXT))
    active = Column(Boolean, default=True)
    score = Column(INTEGER)


class Collection(Base):
    __tablename__ = "collections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(VARCHAR)
    library_id = Column(ARRAY(UUID, ForeignKey("library.id")))
    visibility = Column(VARCHAR)
    visible_users = Column(ARRAY(UUID, ForeignKey("users.id")))
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_by = Column(UUID)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    active = Column(Boolean, default=True)


class Library_History(Base):
    __tablename__ = "library_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    library_id = Column(UUID)
    library_data = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    updated_by_user = Column(UUID)


class Finetune_Model(Base):
    __tablename__ = "finetune_model"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(VARCHAR)
    file_id = Column(VARCHAR)
    model_id = Column(VARCHAR)
    base_model = Column(VARCHAR)
    time_taken = Column(VARCHAR)
    training_cost = Column(INTEGER)
    finetuned_model_name = Column(VARCHAR)
    proposals = Column(ARRAY(TEXT))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    is_completed = Column(BOOLEAN, default=False)


class Text_Generator(Base):
    __tablename__ = "text_generator_chats"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    model_name = Column(TEXT)
    input_text = Column(TEXT)
    output_text = Column(TEXT)
    input_tokens = Column(INTEGER)
    output_tokens = Column(INTEGER)
    total_tokens = Column(INTEGER)
    input_words = Column(INTEGER)
    output_words = Column(INTEGER)
    total_words = Column(INTEGER)
    input_chars = Column(INTEGER)
    output_chars = Column(INTEGER)
    total_chars = Column(INTEGER)
    hit_count = Column(INTEGER, default=1)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    req_num_words = Column(INTEGER)
    exception = Column(TEXT)
    type = Column(VARCHAR)
    # type: session, completion, proposal, workspaces, analytics, rfx
    input_type = Column(VARCHAR)
    # input_type: text, image
    domain_id = Column(UUID, ForeignKey("domains.id"))
    referrer_id = Column(UUID)
    referrer_name = Column(VARCHAR)
    user_id = Column(UUID, ForeignKey("users.id"))
    partial_output_text = Column(TEXT)
    feedback = Column(TEXT)
    reaction = Column(TEXT)
    prompt = Column(TEXT)
    classifier = Column(JSONB)
    filter = Column(JSONB)
    lambda_logs = Column(JSONB)
    lambda_context = Column(JSONB)


class Content(Base):
    __tablename__ = "content"
    id = Column(UUID, primary_key=True)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    proposal_id = Column(UUID, ForeignKey("proposals.id"))
    proposal_url = Column(VARCHAR)
    name = Column(VARCHAR)
    linearized_proposal_url = Column(VARCHAR)
    thumbnail_url = Column(VARCHAR)
    metadata_ = Column(MutableDict.as_mutable(JSONB))
    page_number = Column(INTEGER)
    status = Column(VARCHAR)
    version = Column(VARCHAR)
    approved_by = Column(VARCHAR)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    hidden_from_search = Column(Boolean, default=False)
    hidden_from_search_manual = Column(Boolean, default=False)
    # active = Column(Boolean, unique=True, default=True)
    similarity_processed = Column(Boolean, default=False)
    similarity = Column(JSON)
    content_type = Column(VARCHAR)
    split = Column(VARCHAR)
    es_index_status = Column(VARCHAR)
    iteration_count = Column(INTEGER, default=0)
    thumbnail_info = Column(MutableDict.as_mutable(JSONB))


class Save_Content(Base):
    __tablename__ = "save_content"
    save_id = Column(UUID, primary_key=True)
    domain_id = Column(VARCHAR)
    document_id = Column(VARCHAR)
    user_id = Column(UUID)
    proposal_id = Column(UUID)
    content_id = Column(UUID, ForeignKey("content.id"))
    data_type = Column(VARCHAR)
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_by = Column(VARCHAR)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    active = Column(Boolean, default=True)


class Analytic_Upload(Base):
    __tablename__ = "analytic_upload"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_name = Column(VARCHAR)
    analytic_document_name = Column(VARCHAR)
    pdf_location = Column(VARCHAR)
    processed_pdf_location = Column(VARCHAR)
    linearized_location = Column(VARCHAR)
    compressed_location = Column(VARCHAR)
    linearized_compress_location = Column(VARCHAR)
    tags = Column(MutableDict.as_mutable(JSONB))
    status = Column(VARCHAR)
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    active = Column(Boolean, default=True)
    win_strategy = Column(TEXT)
    overused_words = Column(JSON)
    duplicate_sentences = Column(JSON)
    inconsistant_usage = Column(JSON)
    slack_notification_ts = Column(VARCHAR)


class Analytics_Logs(Base):
    __tablename__ = "analytics_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analytic_id = Column(UUID(as_uuid=True), ForeignKey("analytic_upload.id"))
    logs = Column(TEXT)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)


class Analytic_Content(Base):
    __tablename__ = "analytic_content"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    analytic_id = Column(UUID, ForeignKey("analytic_upload.id"))
    content = Column(TEXT)
    analysed_content = Column(JSON)
    page_number = Column(INTEGER)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    active = Column(Boolean, default=True)


class User_Search_History(Base):
    __tablename__ = "user_search_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    user_id = Column(UUID, ForeignKey("users.id"))
    search_keyword = Column(VARCHAR)
    search_type = Column(VARCHAR)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    active = Column(Boolean, default=True)


class Proposal_Logs(Base):
    __tablename__ = "proposal_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    proposal_id = Column(UUID, ForeignKey("proposals.id"))
    logs = Column(TEXT)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)


class Assets(Base):
    __tablename__ = "assets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(VARCHAR)
    client = Column(VARCHAR)
    market_sector = Column(VARCHAR)
    asset_type = Column(VARCHAR)
    tags = Column(ARRAY(JSON))
    location = Column(VARCHAR)
    thumbnail_location = Column(VARCHAR)
    metadata_ = Column(MutableDict.as_mutable(JSONB))
    analysed_data = Column(ARRAY(MutableDict.as_mutable(JSONB)))
    status = Column(VARCHAR)
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    active = Column(BOOLEAN, unique=True, default=True)
    hidden_from_search = Column(Boolean, default=False)
    hidden_from_search_manual = Column(Boolean, default=False)
    similarity_processed = Column(Boolean, default=False)
    similarity = Column(JSON)
    thumbnail_info = Column(MutableDict.as_mutable(JSONB))


class Prompts(Base):
    __tablename__ = "prompts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    label = Column(VARCHAR)
    name = Column(VARCHAR)
    keywords = Column(ARRAY(TEXT))
    prompt = Column(ARRAY(TEXT))
    placeholderText = Column(ARRAY(TEXT))
    prompt_type = Column(VARCHAR)
    followUpPrompt = Column(ARRAY(TEXT))
    button_text = Column(VARCHAR)
    help_text = Column(VARCHAR)


class Assets_Logs(Base):
    __tablename__ = "assets_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    logs = Column(TEXT)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)


class Cognito_Identity_Providers(Base):
    __tablename__ = "cognito_identity_providers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    idp_name = Column(VARCHAR)
    company = Column(VARCHAR)
    subdomain = Column(VARCHAR)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    update_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class Annotation_Status(Base):
    __tablename__ = "annotation_status"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    proposal_id = Column(UUID, ForeignKey("proposals.id"))
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id"))
    first_pass = Column(TEXT)
    formatting = Column(TEXT)
    image_annotation = Column(TEXT)
    annotator = Column(TEXT)
    annotation_status = Column(TEXT)
    annotation_url = Column(TEXT)


class Style_Guide_Settings(Base):
    __tablename__ = "style_guide_settings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    settings_json = Column(MutableDict.as_mutable(JSONB))
    version = Column(INTEGER, default=1)
    created_by_user = Column(UUID, ForeignKey("users.id"))
    updated_by_user = Column(UUID, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    update_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class Text_Generator_Session(Base):
    __tablename__ = "text_generator_session"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_title = Column(TEXT)
    created_by = Column(UUID)
    active = active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    domain_id = Column(UUID)
    type = Column(VARCHAR)
    refferer_id = Column(UUID)
    # workspace, session
    session_summary = Column(TEXT)
    filtered_proposal_ids = Column(ARRAY(TEXT))
    filtered_options = Column(JSON)


class Pdf_Orchestrator_jobs(Base):
    __tablename__ = "pdf_orchestrator_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_type = Column(VARCHAR)
    payload = Column(JSON)
    domain_id = Column(UUID)
    proposal_id = Column(UUID)
    status = Column(VARCHAR)
    iteration_count = Column(INTEGER, default=0)
    active = Column(BOOLEAN, default=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    logs = Column(ARRAY(TEXT))
    lambda_context = Column(ARRAY(JSON))


class Pdf_Orchestrator_analytics_splits(Base):
    __tablename__ = "pdf_orchestrator_analytics_splits"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analytic_id = Column(UUID)
    domain_id = Column(UUID)
    job_id = Column(UUID, ForeignKey("pdf_orchestrator_jobs.id"))
    split_from_page = Column(INTEGER)
    split_to_page = Column(INTEGER)
    total_pages = Column(INTEGER)
    pdf_extracted = Column(BOOLEAN, default=False)
    analysed = Column(BOOLEAN, default=False)
    active = Column(BOOLEAN, default=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    skip = Column(BOOLEAN, default=False)


class JobStatus(Enum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    ERRORED = "errored"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class JobTypes(Enum):
    PDF_LINEARIZE = "pdf_linearize"
    PDF_EXTRACT_SPLIT = "pdf_split"
    PDF_COMPRESS = "pdf_compress"
    PDF_POLL = "pdf_poll"
    PDF_EXTRACT_PROCESS = "pdf_extract_process"
    PDF_ANALYTICS_PROCESS = "pdf_analytics_process"
    PDF_WIN_STRATEGY = "pdf_win_strategy"
    IMAGE_CAPTION = "image_caption"
    IMAGE_LABEL_DETECTION = "image_label_detection"
    IMAGE_VECTORS = "image_vectors"
    PDF_SNAPSHOT = "pdf_snapshot"
    PDF_PARSER_INVOKER = "pdf_parser_invoker"
    PROJECT_GROUPING_INVOKER = "project_grouping_invoker"
    RFx_EXTRACT_REQUIREMENTS = "rfx_extract_requirements"


class StyleGuideFeatures(Enum):
    CLARITY = "clarity_checker"
    PASSIVE = "passive_voice"
    SPLIT_INFINITIVE = "split_infinitive"
    LONG_SENTENCE = "long_sentences"
    READABILITY = "readability"
    PUNCTUATION_CHECKER = "punctuation_checker"
    PUNCTUATION_STYLE = "punctuation_style"
    AMPERSAND = "ampersand"
    POSSESSIVE_NOUNS = "possessive_nouns"
    PLURALS = "plurals"
    COLONS = "colons"
    CONTRACTIONS = "contractions"
    COMMA = "comma"
    ELLIPSIS = "ellipsis"
    EXCLAMATION = "exclamation_points"
    PERCENT = "percentages"
    QUOTES = "quotes"
    WORDY_PHRASE = "wordy_phrase"
    DATES = "dates"
    CURRENCY = "currency"
    NUMBERS = "numbers"
    LOCATIONS = "locations"
    PEOPLE_NAMES = "people_names"
    CONTACT_NUMBERS = "contact_numbers"
    ACRONYMS = "acronyms"
    EMAIL = "email_id"
    ORGANIZATION_NAMES = "organization_names"
    WORDS_TO_AVOID = "words_to_avoid"
    GRAMMAR_CHECKER = "grammar_checker"
    SPELL_CHECKER = "spell_check"
    WORD_EXCEPMT = "word_exempt"
    WORD_EXCEPMT_LIST = "word_exempt_list"


class RFx_Upload(Base):
    __tablename__ = "rfx_upload"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_name = Column(VARCHAR)
    document_type = Column(VARCHAR)
    location = Column(VARCHAR)
    client = Column(VARCHAR)
    market_sector = Column(VARCHAR)
    tags = Column(MutableDict.as_mutable(JSONB))
    total_pages = Column(INTEGER)
    document_content = Column(JSON)
    linearized_location = Column(VARCHAR)
    compressed_location = Column(VARCHAR)
    linearized_compress_location = Column(VARCHAR)
    status = Column(VARCHAR)
    analysis_report = Column(JSON)
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    active = Column(Boolean, default=True)
    slack_notification_ts = Column(VARCHAR)


class Rfx_Public_Share(Base):
    __tablename__ = "rfx_public_share"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    shared_by = Column(UUID, ForeignKey("users.id"))
    rfx_id = Column(UUID, ForeignKey("rfx_upload.id"))
    analytic_id = Column(UUID, ForeignKey("analytic_upload.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    valid_for_days = Column(INTEGER)
    pdf_location = Column(VARCHAR)
    link_active = Column(Boolean, default=False)


class People(Base):
    __tablename__ = "people"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    proposal_id = Column(UUID, ForeignKey("proposals.id"))
    metadata_ = Column(JSONB)
    page_number = Column(INTEGER)
    similar_processed = Column(Boolean, default=False)
    similar_people = Column(JSONB)
    thumbnail_url = Column(VARCHAR)
    profile_picture_location = Column(VARCHAR)
    es_index_status = Column(VARCHAR)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    resume_data = Column(JSONB)
    proposal_name = Column(VARCHAR)
    iteration_count = Column(INTEGER, default=0)
    face_group_id = Column(UUID)
    verified = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "domain_id": str(self.domain_id),
            "proposal_id": str(self.proposal_id),
            "metadata_": self.metadata_,
            "page_number": self.page_number,
            "similar_processed": self.similar_processed,
            "similar_people": self.similar_people,
            "profile_picture_location": self.profile_picture_location,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resume_data": self.resume_data,
            "proposal_name": self.proposal_name,
            "es_index_status": self.es_index_status,
            "thumbnail_url": self.thumbnail_url,
            "iteration_count": self.iteration_count,
            "face_group_id": str(self.face_group_id),
            "verified": self.verified,
        }


class Page_data(Base):
    __tablename__ = "page_data"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    proposal_id = Column(UUID, ForeignKey("proposals.id"))
    page_number = Column(INTEGER)
    source_type = Column(VARCHAR)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    content_type = Column(VARCHAR)
    parsing_status = Column(Boolean, default=False)
    metadata_ = Column(MutableDict.as_mutable(JSONB))
    people_project_type = Column(VARCHAR)
    status = Column(VARCHAR)


class PageDataStatus(Enum):
    READY_TO_PARSE = "ready_to_parsed"
    READY_TO_REPARSE = "ready_to_reparsed"
    PARSED = "parsed"
    ERRORED = "errored"
    DELETED = "deleted"


class ESIndexStatus(Enum):
    READY_TO_INDEX = "ready_to_index"
    INDEXED = "indexed"
    READY_TO_REINDEX = "ready_to_reindex"
    ERRORED = "errored"
    DELETED = "deleted"
    DELETED_FROM_ES = "deleted_from_es"
    PAUSED = "paused"


class MappingStatus(Enum):
    MAPPED = "mapped"
    UNMAPPED = "unmapped"


class Faces(Base):
    __tablename__ = "faces"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID)
    proposal_id = Column(UUID)
    image_url = Column(VARCHAR)
    page_number = Column(INTEGER)
    metadata_ = Column(MutableDict.as_mutable(JSONB))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    mapped_people_ids = Column(ARRAY(TEXT))
    mapping_status = Column(VARCHAR)
    similarity_processed = Column(Boolean, default=False)
    similar_faces = Column(JSONB)
    es_index_status = Column(VARCHAR)
    face_group_id = Column(UUID)

    def to_dict(self):
        return {
            "id": str(self.id),
            "domain_id": str(self.domain_id),
            "proposal_id": str(self.proposal_id),
            "image_url": self.image_url,
            "page_number": self.page_number,
            "metadata_": self.metadata_,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "mapped_people_ids": self.mapped_people_ids,
            "mapping_status": self.mapping_status,
            "es_index_status": self.es_index_status,
            "similarity_processed": self.similarity_processed,
            "similar_faces": self.similar_faces,
            "face_group_id": str(self.face_group_id),
        }


class Master_people(Base):
    __tablename__ = "master_people"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    mapping_data = Column(JSONB)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    es_index_status = Column(VARCHAR)
    emp_name_list = Column(ARRAY(TEXT))
    emp_name = Column(VARCHAR)
    verified = Column(Boolean, default=False)
    master_resume_content = Column(JSONB)
    processed = Column(Boolean, default=False)
    profile_picture = Column(JSON)
    notes = Column(VARCHAR)


class MappingStatus(Enum):
    MAPPED = "mapped"
    UNMAPPED = "unmapped"


class Annotation_Text_Extracts(Base):
    __tablename__ = "annotation_text_extracts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    proposal_id = Column(UUID, ForeignKey("proposals.id"))
    created_by_user = Column(UUID, ForeignKey("users.id"))
    page_number = Column(INTEGER)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    tables = Column(JSONB)
    forms = Column(JSONB)
    page_dims = Column(JSONB)
    status = Column(VARCHAR)


class PipelinePrompts(Base):
    __tablename__ = "pipeline_prompts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    prompt_type = Column(VARCHAR)
    description = Column(TEXT)
    prompt = Column(TEXT)
    version = Column(INTEGER, default=1)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class PromptTypes(Enum):
    CHAT_CONTENT_SEARCH = "chat_content_search"
    CHAT_FOLLOWUP_HISTORY = "chat_followup_with_history"
    CHAT_FOLLOWUP_SUMMARY = "chat_followup_with_summary"
    CHAT_FOLLOWUP = "chat_followup"
    CHAT_GENERAL_INQUIRY = "chat_general_inquiry"
    CHAT_ANALYTICS = "chat_pdf_analytics"
    CHAT_PROPOSALS_RFX = "chat_pdf_proposal/rfx"
    CHAT_QUESTION_CLASSIFIER = "chat_question_classifier"
    CHAT_RESUME_SEARCH = "chat_resume_search"
    CHAT_PROPOSAL_BY_ES = "chat_proposal_by_es"
    CHAT_PROPOSAL = "chat_proposal"
    STYLE_GUIDE = "style_guide"
    PAGE_CLASSIFIER = "pdf_page_classifier"
    GENERATE_MASTER_RESUME = "generate_master_resume"
    GENERATE_PEOPLE_RESUME = "generate_people_resume"
    CHAT_TITLE_GENERATOR = "chat_title_generator"
    GENERATE_PROJECT_RESUME = "generate_project"
    CHECK_REQUIREMENTS_COMPLIANCE = "check_requirements_compliance"
    RFx_REFRESH = "rfx_refresh"


class ProjectCollection(Base):
    __tablename__ = "project_collection"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    title = Column(VARCHAR)
    content_ids = Column(ARRAY(UUID))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    active = Column(Boolean, default=True)
    notes = Column(VARCHAR)


class Tag_Center(Base):
    __tablename__ = "tag_center"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tag_key = Column(VARCHAR)
    tag_key_type = Column(ARRAY(VARCHAR))
    tag_value = Column(VARCHAR)
    usage_count = Column(INTEGER)
    tag_type = Column(VARCHAR)
    tag_value_type = Column(VARCHAR)
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    updated_by_user = Column(UUID, ForeignKey("users.id"))
    editable = Column(Boolean, default=True)
    active = Column(Boolean, default=True)


class Tag_Center_Relation(Base):
    __tablename__ = "tag_center_relation"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tag_center_id = Column(UUID, ForeignKey("tag_center.id"))
    document_id = Column(UUID)
    document_type = Column(VARCHAR)
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "tag_center_id": str(self.tag_center_id),
            "document_id": str(self.document_id),
            "document_type": self.document_type,
            "created_for_domain": str(self.created_for_domain),
            "created_by_user": str(self.created_by_user),
            "created_at": self.created_at,
            "active": self.active,
        }


class DocumentTypes(Enum):
    PROPOSAL = "proposal"
    ASSET = "asset"
    CONTENT = "content"
    DOCUMENT = "document"
    RESUME = "resume"
    MASTER_RESUME = "masterresume"
    PEOPLE = "people"
    PROJECT = "project"
    IMAGES = "image"
    VIDEOS = "video"
    PROPOSAL_IMAGES = "proposalimage"


class Collections_Group(Base):
    __tablename__ = "collections_group"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(VARCHAR)
    parent_id = Column(UUID, ForeignKey("collections_group.id"))
    created_by = Column(UUID, ForeignKey("users.id"))
    updated_by = Column(UUID, ForeignKey("users.id"))
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    description = Column(VARCHAR)
    icon = Column(VARCHAR)
    color = Column(VARCHAR)
    access_config = Column(JSONB)
    is_public = Column(Boolean, default=False)
    nesting = Column(ARRAY(UUID))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "parent_id": str(self.parent_id),
            "created_by": str(self.created_by),
            "updated_by": str(self.updated_by),
            "created_for_domain": str(self.created_for_domain),
            "access_config": self.access_config,
            "is_public": self.is_public,
            "nesting": self.nesting,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
        }


class Collections_Relation(Base):
    __tablename__ = "collections_documents_relation"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    collection_id = Column(UUID, ForeignKey("collections_group.id"))
    document_id = Column(UUID)
    document_type = Column(VARCHAR)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    created_by = Column(UUID, ForeignKey("users.id"))
    created_for_domain = Column(UUID, ForeignKey("domains.id"))

    def to_dict(self):
        return {
            "id": str(self.id),
            "collection_id": str(self.collection_id),
            "document_id": str(self.document_id),
            "document_type": self.document_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": str(self.created_by),
            "created_for_domain": str(self.created_for_domain),
        }


class RFx_Analytics_Compliance(Base):
    __tablename__ = "rfx_analytics_compliance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(UUID, ForeignKey("domains.id"))
    rfx_id = Column(UUID)
    analytic_id = Column(UUID)
    compliance = Column(JSON)
    active = Column(Boolean, default=True)
    status = Column(VARCHAR)
    uploaded_by = Column(UUID)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class Document_Upload(Base):
    __tablename__ = "document_upload"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(VARCHAR)
    file_type = Column(VARCHAR)
    file_extension = Column(VARCHAR)
    last_modified_date = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    notes = Column(VARCHAR)
    location = Column(VARCHAR)
    status = Column(VARCHAR)
    hidden_from_search_manual = Column(Boolean, default=False)
    hidden_from_search = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    created_by_user = Column(UUID, ForeignKey("users.id"))
    created_for_domain = Column(UUID, ForeignKey("domains.id"))
    source = Column(VARCHAR)
    sha_id = Column(VARCHAR)
