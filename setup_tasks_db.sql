-- 1️⃣ Create the database
CREATE DATABASE IF NOT EXISTS sonline_ai_db;
USE sonline_ai_db;

-- 2️⃣ Create a table for tasks
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3️⃣ Insert sample tasks
INSERT INTO tasks (title, description, status) VALUES
('Finish report', 'Complete the monthly report by today', 'pending'),
('Call client', 'Follow up with client regarding project', 'pending'),
('Update AI model', 'Train AI with new data', 'completed')
ON DUPLICATE KEY UPDATE title=VALUES(title);

