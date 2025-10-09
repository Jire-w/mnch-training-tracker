-- Create tables (same as previous SQL)
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

-- ... (include all other tables from the previous SQL code)