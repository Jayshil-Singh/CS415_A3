-- Add passport and visa columns to Student table in enrollment.db
ALTER TABLE Student ADD PassportNumber TEXT;
ALTER TABLE Student ADD VisaStatus TEXT;
ALTER TABLE Student ADD VisaExpiryDate TEXT; 