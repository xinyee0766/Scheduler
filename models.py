import sqlite3
import os

def init_db():
    """Initialize the database with classes table if it doesn't exist"""
    db_path = os.path.join(os.path.dirname(__file__), 'classes.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 day TEXT NOT NULL,
                 time TEXT NOT NULL,
                 location TEXT NOT NULL,
                 notes TEXT)''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Create and return a database connection"""
    db_path = os.path.join(os.path.dirname(__file__), 'classes.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

class Class:
    """Class representing a scheduled class"""
    
    def __init__(self, id=None, name="", day="", time="", location="", notes=""):
        self.id = id
        self.name = name
        self.day = day
        self.time = time
        self.location = location
        self.notes = notes
    
    def save(self):
        """Save the class to the database"""
        conn = get_db_connection()
        c = conn.cursor()
        
        if self.id:
            c.execute('''UPDATE classes 
                         SET name=?, day=?, time=?, location=?, notes=?
                         WHERE id=?''',
                      (self.name, self.day, self.time, self.location, self.notes, self.id))
        else:
            c.execute('''INSERT INTO classes (name, day, time, location, notes)
                         VALUES (?, ?, ?, ?, ?)''',
                      (self.name, self.day, self.time, self.location, self.notes))
            self.id = c.lastrowid
        
        conn.commit()
        conn.close()
        return True
    
    def delete(self):
        """Delete the class from the database"""
        if not self.id:
            return False
            
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM classes WHERE id=?', (self.id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_all():
        """Get all classes from the database"""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM classes ORDER BY day, time')
        classes = [Class(id=row['id'], name=row['name'], day=row['day'], 
                         time=row['time'], location=row['location'], notes=row['notes']) 
                   for row in c.fetchall()]
        conn.close()
        return classes
    
    @staticmethod
    def get_by_id(class_id):
        """Get a class by its ID"""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM classes WHERE id=?', (class_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return Class(id=row['id'], name=row['name'], day=row['day'], 
                         time=row['time'], location=row['location'], notes=row['notes'])
        return None
    
    @staticmethod
    def search(query):
        """Search for classes by name"""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM classes WHERE name LIKE ? ORDER BY day, time', 
                  ('%' + query + '%',))
        classes = [Class(id=row['id'], name=row['name'], day=row['day'], 
                         time=row['time'], location=row['location'], notes=row['notes']) 
                   for row in c.fetchall()]
        conn.close()
        return classes