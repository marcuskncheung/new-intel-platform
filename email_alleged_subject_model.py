"""
EmailAllegedSubject Model

Add this model to your models file (e.g., models.py or app1_production.py)

This represents the new relational structure for email alleged subjects.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Assuming db is your SQLAlchemy instance
# db = SQLAlchemy()

class EmailAllegedSubject(db.Model):
    """
    Relational table for email alleged subjects.
    Replaces comma-separated storage in email table.
    
    Each alleged person is a separate row, ensuring:
    - Correct English-Chinese name pairing
    - Individual license info per person
    - Easy querying and updating
    - No limit on persons per email
    """
    __tablename__ = 'email_alleged_subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id', ondelete='CASCADE'), nullable=False)
    
    # Person names
    english_name = db.Column(db.String(255), nullable=True)
    chinese_name = db.Column(db.String(255), nullable=True)
    
    # Insurance intermediary info
    is_insurance_intermediary = db.Column(db.Boolean, default=False)
    license_type = db.Column(db.String(100), nullable=True)  # Agent, Broker, etc.
    license_number = db.Column(db.String(100), nullable=True)
    
    # Ordering
    sequence_order = db.Column(db.Integer, nullable=False)  # 1, 2, 3, ...
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    email = db.relationship('Email', backref=db.backref('alleged_subjects', 
                                                        lazy='dynamic',
                                                        cascade='all, delete-orphan'))
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('english_name IS NOT NULL OR chinese_name IS NOT NULL',
                          name='check_has_name'),
        db.UniqueConstraint('email_id', 'sequence_order',
                           name='unique_email_subject'),
        db.Index('idx_email_alleged_subjects_email_id', 'email_id'),
        db.Index('idx_email_alleged_subjects_english', 'english_name'),
        db.Index('idx_email_alleged_subjects_chinese', 'chinese_name'),
    )
    
    def __repr__(self):
        return f'<EmailAllegedSubject {self.id}: {self.english_name} ({self.chinese_name})>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'english_name': self.english_name,
            'chinese_name': self.chinese_name,
            'is_insurance_intermediary': self.is_insurance_intermediary,
            'license_type': self.license_type,
            'license_number': self.license_number,
            'sequence_order': self.sequence_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Helper functions for working with EmailAllegedSubject

def get_email_alleged_subjects(email_id):
    """Get all alleged subjects for an email, ordered by sequence"""
    return EmailAllegedSubject.query.filter_by(email_id=email_id)\
                                    .order_by(EmailAllegedSubject.sequence_order)\
                                    .all()


def save_email_alleged_subjects(db, email_id, subjects_data):
    """
    Save alleged subjects for an email.
    
    Args:
        db: SQLAlchemy database instance
        email_id: Email ID
        subjects_data: List of dicts with keys:
            - english_name (optional)
            - chinese_name (optional)
            - is_insurance_intermediary (optional)
            - license_type (optional)
            - license_number (optional)
    
    Returns:
        List of created EmailAllegedSubject objects
    """
    # Delete old subjects
    EmailAllegedSubject.query.filter_by(email_id=email_id).delete()
    
    # Create new subjects
    created = []
    for i, data in enumerate(subjects_data, start=1):
        # Skip if both names are empty
        if not data.get('english_name') and not data.get('chinese_name'):
            continue
        
        subject = EmailAllegedSubject(
            email_id=email_id,
            english_name=data.get('english_name'),
            chinese_name=data.get('chinese_name'),
            is_insurance_intermediary=data.get('is_insurance_intermediary', False),
            license_type=data.get('license_type'),
            license_number=data.get('license_number'),
            sequence_order=i
        )
        db.session.add(subject)
        created.append(subject)
    
    return created


def format_alleged_subjects_legacy(email_id):
    """
    Format alleged subjects in legacy comma-separated format.
    Used for backward compatibility.
    
    Returns:
        tuple: (english_string, chinese_string, combined_string)
    """
    subjects = get_email_alleged_subjects(email_id)
    
    english_names = [s.english_name for s in subjects if s.english_name]
    chinese_names = [s.chinese_name for s in subjects if s.chinese_name]
    
    # Combined format: "English (Chinese)"
    combined = []
    for subject in subjects:
        if subject.english_name and subject.chinese_name:
            combined.append(f"{subject.english_name} ({subject.chinese_name})")
        elif subject.english_name:
            combined.append(subject.english_name)
        elif subject.chinese_name:
            combined.append(f"({subject.chinese_name})")
    
    return (
        ', '.join(english_names) if english_names else None,
        ', '.join(chinese_names) if chinese_names else None,
        ', '.join(combined) if combined else None
    )
