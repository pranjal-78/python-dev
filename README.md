🗓️ Event Management System API

A RESTful Event Management System built using Django and Django REST Framework (DRF).
This project allows users to create events, RSVP, and leave reviews — with proper authentication, permissions, and validations.

🚀 Features
👤 User Management

Users can register, log in, and manage their profile.

Each user has a UserProfile with additional fields like bio, location, and profile_picture.

🎟️ Events

Authenticated users can create, edit, and delete their own events.

Events include details like title, description, organizer, location, start and end time, etc.

Public events are visible to all, while private events are accessible only to invited users.

📅 RSVP System

Users can RSVP to events as "Going", "Maybe", or "Not Going".

Organizers can view and manage RSVPs.

⭐ Reviews

Users can add reviews (with ratings and comments) for events they attended.

Reviews are paginated and linked to their respective events.

🧩 Tech Stack

Backend: Django, Django REST Framework

Authentication: JWT (using djangorestframework-simplejwt)

Database: SQLite (default, can be switched to PostgreSQL/MySQL)

Environment: Python 3.x
