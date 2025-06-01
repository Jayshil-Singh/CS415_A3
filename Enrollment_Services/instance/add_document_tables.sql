-- Add document tables to enrollment.db

-- Birth Certificate table
CREATE TABLE IF NOT EXISTS BirthCertificate (
    id INTEGER PRIMARY KEY,
    student_id VARCHAR(50) REFERENCES Student(StudentID) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified INTEGER DEFAULT 0
);

-- Valid ID table
CREATE TABLE IF NOT EXISTS ValidID (
    id INTEGER PRIMARY KEY,
    student_id VARCHAR(50) REFERENCES Student(StudentID) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified INTEGER DEFAULT 0,
    id_type VARCHAR(50) NOT NULL
);

-- Academic Transcript table
CREATE TABLE IF NOT EXISTS AcademicTranscript (
    id INTEGER PRIMARY KEY,
    student_id VARCHAR(50) REFERENCES Student(StudentID) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified INTEGER DEFAULT 0,
    year_level VARCHAR(20) NOT NULL
); 