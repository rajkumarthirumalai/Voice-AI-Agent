-- DDL Schema for Hall Booking System (PostgreSQL)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create Halls Table
CREATE TABLE IF NOT EXISTS halls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    base_price DECIMAL(10, 2) NOT NULL,
    tax_rate DECIMAL(4, 2) NOT NULL DEFAULT 18.00,
    capacity INTEGER NOT NULL,
    description VARCHAR(500)
);

-- Create Bookings Table
CREATE TABLE IF NOT EXISTS bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hall_id UUID NOT NULL REFERENCES halls(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    customer_name VARCHAR(150) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_hall_date_booking UNIQUE (hall_id, date)
);

-- Create Index for fast date lookups
CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(date);
CREATE INDEX IF NOT EXISTS idx_halls_name ON halls(name);

-- Seed Initial Data for Demonstration
INSERT INTO halls (name, base_price, tax_rate, capacity, description) VALUES
('Main Hall', 50000.00, 18.00, 1000, 'Spacious luxury wedding hall with modern seating.'),
('Mini Hall', 25000.00, 18.00, 300, 'Perfect for seminars, family events, and functions.'),
('Party Hall', 15000.00, 18.00, 150, 'Cozy hall for small social get-togethers.')
ON CONFLICT (name) DO NOTHING;
