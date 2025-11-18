-- Drop and create event5 database
DROP DATABASE IF EXISTS event5;
CREATE DATABASE event5;
USE event5;

-- Create users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL, 
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create events table 
CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(255) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create attendees table
CREATE TABLE attendees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- Create vendors table with amount_to_be_paid column
CREATE TABLE vendors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    service VARCHAR(255) NOT NULL, 
    amount_to_be_paid DECIMAL(10,2) DEFAULT 0.00, -- New column for amount to be paid
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- Create sponsors table
CREATE TABLE sponsors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL,
    contribution DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- Create event_items table
CREATE TABLE event_items (
    item_id INT AUTO_INCREMENT,
    event_id INT,
    item_name VARCHAR(100) NOT NULL,
    quantity INT DEFAULT 1,
    PRIMARY KEY (item_id, event_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- Create function to check login credentials
DELIMITER //

CREATE FUNCTION check_login_credentials(
    user_email VARCHAR(100),
    user_password VARCHAR(255)
)
RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE user_id INT;
    DECLARE stored_password VARCHAR(255);
    
    -- Get user details
    SELECT id, password INTO user_id, stored_password
    FROM users
    WHERE email = user_email;
    
    -- Return 0 if user not found
    IF user_id IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Return user_id if passwords match, 0 otherwise
    RETURN user_id;
END //

DELIMITER ;


DELIMITER //

CREATE TRIGGER prevent_venue_conflicts
BEFORE INSERT ON events
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1
        FROM events e
        WHERE e.location = NEW.location
        AND (
            (e.start_time <= NEW.start_time AND e.end_time >= NEW.start_time)  -- Overlaps with start of new event
            OR
            (e.start_time <= NEW.end_time AND e.end_time >= NEW.end_time)      -- Overlaps with end of new event
            OR
            (e.start_time >= NEW.start_time AND e.end_time <= NEW.end_time)    -- Existing event within new event
        )
        AND e.id != NEW.id
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Venue conflict: Another event is scheduled at the same time and venue.';
    END IF;
END //

DELIMITER ;

DELIMITER //

CREATE TRIGGER prevent_venue_conflicts_update
BEFORE UPDATE ON events
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1
        FROM events e
        WHERE e.location = NEW.location
        AND e.start_time <= NEW.start_time
        AND e.end_time >= NEW.start_time
        AND e.id != NEW.id
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Venue conflict: Another event is scheduled at the same time and venue.';
    END IF;
END //

DELIMITER ;

DELIMITER //
CREATE PROCEDURE get_event_summary(IN eventId INT)
BEGIN
    SELECT e.title, e.location, COUNT(a.id) AS attendees, 
           SUM(v.amount_to_be_paid) AS total_vendor_cost
    FROM events e
    LEFT JOIN attendees a ON e.id = a.event_id
    LEFT JOIN vendors v ON e.id = v.event_id
    WHERE e.id = eventId
    GROUP BY e.id;
END //
DELIMITER ;

-- nested query
SELECT username 
FROM users 
WHERE id IN (SELECT user_id FROM events WHERE location = 'Auditorium');

-- Correlated Subquery
SELECT e.title, 
       (SELECT COUNT(*) FROM attendees a WHERE a.event_id = e.id) AS attendee_count
FROM events e;

-- Aggregate with GROUP BY
SELECT location, COUNT(*) AS total_events
FROM events
GROUP BY location;

-- HAVING Clause
SELECT user_id, COUNT(*) AS total_events
FROM events
GROUP BY user_id
HAVING total_events > 1;

-- JOIN + WHERE
SELECT e.title, v.name AS vendor_name, v.amount_to_be_paid
FROM events e
JOIN vendors v ON e.id = v.event_id
WHERE v.amount_to_be_paid > 1000;



