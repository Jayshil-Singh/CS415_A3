-- instance/schema.sql (Add/Modify these lines)

CREATE TABLE courses (
    -- ... other columns ...
    FeeID VARCHAR(50), -- Add this column
    FOREIGN KEY (FeeID) REFERENCES course_fees(FeeID)
);

CREATE TABLE course_fees (
    FeeID VARCHAR(50) PRIMARY KEY,
    amount INTEGER NOT NULL,
    description VARCHAR(255),
    CourseID VARCHAR(50), -- Add this column
    FOREIGN KEY (CourseID) REFERENCES courses(CourseID)
);