# Add document tables to the list of tables to replicate
TABLES_TO_REPLICATE = [
    'Campus',
    'ProgramType',
    'Program',
    'SubProgram',
    'Student',
    'Student_Level',
    'Student_Program',
    'Student_SubProgram',
    'BirthCertificate',
    'ValidID',
    'AcademicTranscript',
    'Addressing_Student',
    'Emergency_Contact'
]

# Update the table dependencies to include document tables
TABLE_DEPENDENCIES = {
    'Student': [],
    'Campus': [],
    'ProgramType': [],
    'Program': ['ProgramType'],
    'SubProgram': ['Program'],
    'Student_Level': ['Student'],
    'Student_Program': ['Student', 'Program'],
    'Student_SubProgram': ['Student', 'SubProgram'],
    'BirthCertificate': ['Student'],
    'ValidID': ['Student'],
    'AcademicTranscript': ['Student'],
    'Addressing_Student': ['Student'],
    'Emergency_Contact': ['Student']
} 