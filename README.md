# 📘 Event Management System

A MySQL-based event management backend designed to handle users, events, attendees, vendors, sponsors, and event items efficiently.  
The project includes **triggers, stored procedures, functions, ER design, and advanced SQL queries** with complete relational integrity.

---

## 🚀 Features

### ✅ User Management
- Stores user accounts with unique email & username.
- Login verification using a stored SQL function (`check_login_credentials`).

### ✅ Event Management
- Create, update, delete events.
- Auto-prevents **venue/timing conflicts** using SQL triggers.
- Each event linked to its organizer (user).

### ✅ Attendee Management
- Register attendees for each event.
- Automatically deleted when an event is deleted.

### ✅ Vendor Management
- Stores vendor details and payments.
- Tracks `amount_to_be_paid` for budgeting.

### ✅ Sponsor Management
- Records sponsors, sponsorship levels, and contributions.

### ✅ Event Items
- Stores required items and quantities for each event.

### ✅ Analytics (Stored Procedure)
- `get_event_summary(eventId)` provides:
  - Event title  
  - Location  
  - Attendee count  
  - Total vendor cost  

---

## 🛠️ Tech Stack

| Component | Technology |
|----------|------------|
| Database | MySQL |
| Language | SQL |
| Integrity | Triggers, Foreign Keys, Cascades |
| Analytics | Stored Procedures & Functions |

---

## 📂 Database Schema Overview

### **Tables Included**
- `users`
- `events`
- `attendees`
- `vendors`
- `sponsors`
- `event_items`

### **Relationships**
- One **User** → Many **Events**
- One **Event** → Many **Attendees**
- One **Event** → Many **Vendors**
- One **Event** → Many **Sponsors**
- One **Event** → Many **Event Items**

---

## 📑 SQL Components

### **1️⃣ Tables with Constraints**
- Primary Keys  
- Unique constraints  
- Foreign keys with **ON DELETE CASCADE**  

### **2️⃣ Triggers**
- `prevent_venue_conflicts`
- `prevent_venue_conflicts_update`

Used to avoid event overlap at the same venue.

### **3️⃣ Stored Function**
`check_login_credentials(email, password)`  
Returns user ID or 0.

### **4️⃣ Stored Procedure**
`get_event_summary(eventId)`  
Returns aggregated event data.

### **5️⃣ Advanced SQL Queries**
- Nested queries  
- Correlated subqueries  
- Aggregation + GROUP BY  
- HAVING filters  
- JOIN queries  

---

## 🧪 Sample Queries

### ✔️ Count events by location
```sql
SELECT location, COUNT(*) AS total_events
FROM events
GROUP BY location;
