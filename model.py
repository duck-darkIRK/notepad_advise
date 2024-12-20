from sqlalchemy import (
    Column, String, Integer, ForeignKey, Table, Float, create_engine, Boolean, Text
)
from sqlalchemy.orm import relationship, declarative_base
import uuid
import time

Base = declarative_base()

user_major_association = Table(
    'user_major', Base.metadata,
    Column('user_id', String(36), ForeignKey('users.uuid')),
    Column('major_id', String(255), ForeignKey('majors.id')),
)

major_subject_association = Table(
    'major_subject', Base.metadata,
    Column('major_id', String(255), ForeignKey('majors.id')),
    Column('subject_id', String(255), ForeignKey('subjects.id')),
    Column('type', String(255), default="required", nullable=False)
)

user_subject_association = Table(
    'user_subject', Base.metadata,
    Column('user_id', String(36), ForeignKey('users.uuid'), primary_key=True),
    Column('subject_id', String(255), ForeignKey('subjects.id'), primary_key=True),
    Column('score', Float, nullable=True),
    Column('note', Text, nullable=True)
)


class User(Base):
    __tablename__ = 'users'

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    role = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    session = Column(String(255), nullable=True)
    semester = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False)

    majors = relationship('Major', secondary=user_major_association, back_populates='users')
    subjects = relationship('Subject', secondary=user_subject_association, back_populates='users')
    transcript = relationship('Transcript', back_populates='owner')

    created_at = Column(Float, default=lambda: time.time())
    updated_at = Column(Float, default=lambda: time.time(), onupdate=lambda: time.time())


class Major(Base):
    __tablename__ = 'majors'

    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    is_deleted = Column(Boolean, default=False)

    users = relationship('User', secondary=user_major_association, back_populates='majors')
    subjects = relationship('Subject', secondary=major_subject_association, back_populates='majors')

    created_at = Column(Float, default=lambda: time.time())
    updated_at = Column(Float, default=lambda: time.time(), onupdate=lambda: time.time())


class Subject(Base):
    __tablename__ = 'subjects'

    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=True)
    weight = Column(Integer, nullable=False)
    required = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False)

    majors = relationship('Major', secondary=major_subject_association, back_populates='subjects')
    users = relationship('User', secondary=user_subject_association, back_populates='subjects')

    transcripts = relationship('Transcript', back_populates='subject')
    in_class = relationship('Class', back_populates='subject')

    created_at = Column(Float, default=lambda: time.time())
    updated_at = Column(Float, default=lambda: time.time(), onupdate=lambda: time.time())


class Transcript(Base):
    __tablename__ = 'transcripts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    score = Column(Float, nullable=False)
    owner_id = Column(String(36), ForeignKey('users.uuid'))
    subject_id = Column(String(255), ForeignKey('subjects.id'), nullable=False)
    is_deleted = Column(Boolean, default=False)

    subject = relationship('Subject', back_populates='transcripts')
    owner = relationship('User', back_populates='transcript')

    created_at = Column(Float, default=lambda: time.time())
    updated_at = Column(Float, default=lambda: time.time(), onupdate=lambda: time.time())


class Class(Base):
    __tablename__ = 'classes'

    id = Column(String(255), primary_key=True)
    semester = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    time = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    subject_id = Column(String(255), ForeignKey('subjects.id'), nullable=False)
    is_deleted = Column(Boolean, default=False)

    subject = relationship('Subject', back_populates='in_class')

    created_at = Column(Float, default=lambda: time.time())
    updated_at = Column(Float, default=lambda: time.time(), onupdate=lambda: time.time())

