-- Create database
CREATE DATABASE mnch_training_tracker;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'trainer', 'trainee', 'supervisor')),
    full_name VARCHAR(100) NOT NULL,
    facility VARCHAR(100),
    region VARCHAR(50),
    woreda VARCHAR(50),
    contact_number VARCHAR(20),
    gender VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trainings table
CREATE TABLE trainings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    training_type VARCHAR(50) NOT NULL CHECK (training_type IN ('EPI', 'Cold Chain', 'Data', 'Clinical', 'Community', 'Other')),
    objectives TEXT,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    venue VARCHAR(200),
    max_participants INTEGER,
    trainer_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'ongoing', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Participants table (junction table)
CREATE TABLE training_participants (
    id SERIAL PRIMARY KEY,
    training_id INTEGER REFERENCES trainings(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    attendance_status VARCHAR(20) DEFAULT 'registered' CHECK (attendance_status IN ('registered', 'attended', 'absent')),
    certificate_issued BOOLEAN DEFAULT FALSE,
    certificate_id VARCHAR(100) UNIQUE,
    evaluation_score INTEGER,
    feedback TEXT,
    UNIQUE(training_id, user_id)
);

-- Attendance table for daily sessions
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    training_id INTEGER REFERENCES trainings(id),
    user_id INTEGER REFERENCES users(id),
    session_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('present', 'absent', 'late')),
    session_topic VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(training_id, user_id, session_date)
);

-- Certificates table
CREATE TABLE certificates (
    id SERIAL PRIMARY KEY,
    certificate_id VARCHAR(100) UNIQUE NOT NULL,
    training_id INTEGER REFERENCES trainings(id),
    user_id INTEGER REFERENCES users(id),
    issue_date DATE NOT NULL,
    expiry_date DATE,
    qr_code_data TEXT,
    file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feedback table
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    training_id INTEGER REFERENCES trainings(id),
    user_id INTEGER REFERENCES users(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comments TEXT,
    suggestions TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);