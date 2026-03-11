 -- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Dimension Tables

-- Secret Questions Dimension
CREATE TABLE dim_questions (
    question_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_text VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- User Type Dimension
CREATE TABLE dim_usertype (
    user_type_id VARCHAR(10) PRIMARY KEY,
    user_type_desc VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Role Dimension
CREATE TABLE dim_user_role_type (
    user_role_id VARCHAR(10) PRIMARY KEY,
    user_role_desc VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Type - Role Mapping
CREATE TABLE dim_user_type_role_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_type_id VARCHAR(10) REFERENCES dim_usertype(user_type_id),
    user_role_id VARCHAR(10) REFERENCES dim_user_role_type(user_role_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_type_id, user_role_id)
);

-- Subscription Tier Dimension
CREATE TABLE dim_subscription_tier (
    tier_id VARCHAR(10) PRIMARY KEY,
    tier_name VARCHAR(50) NOT NULL,
    request_limit INTEGER NOT NULL,
    price_usd DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- User Dimension (SCD Type 2)
CREATE TABLE dim_user (
    user_sk UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL,
    user_login_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    user_type_id VARCHAR(10) REFERENCES dim_usertype(user_type_id),
    subscription_tier_id VARCHAR(10) REFERENCES dim_subscription_tier(tier_id),
    record_start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    record_end_date TIMESTAMP WITH TIME ZONE,
    is_current BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Continuing from previous schema...

-- API Location Dimension
CREATE TABLE dim_api_location (
    location_sk UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_name VARCHAR(100) NOT NULL,
    location_ip INET NOT NULL,
    location_port INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Batch Dimension
CREATE TABLE dim_batch (
    batch_sk UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document Dimension
CREATE TABLE dim_document (
    document_sk UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_name VARCHAR(100) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fact Tables
CREATE TABLE fact_api_header (
    api_sk UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_id VARCHAR(50) UNIQUE NOT NULL,
    api_name VARCHAR(100) NOT NULL,
    location_sk UUID REFERENCES dim_api_location(location_sk),
    batch_sk UUID REFERENCES dim_batch(batch_sk),
    launch_by_sk UUID REFERENCES dim_user(user_sk),
    active_row BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fact_api_detail (
    api_detail_sk UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_sk UUID REFERENCES fact_api_header(api_sk),
    document_sk UUID REFERENCES dim_document(document_sk),
    blob_link VARCHAR(255),
    active_row BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Security Tables
CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_sk UUID REFERENCES dim_user(user_sk),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE api_keys (
    key_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_sk UUID REFERENCES dim_user(user_sk),
    api_key VARCHAR(64) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- Logging Tables
CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_sk UUID REFERENCES dim_user(user_sk),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_usage_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_sk UUID REFERENCES dim_user(user_sk),
    api_sk UUID REFERENCES fact_api_header(api_sk),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_status INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);