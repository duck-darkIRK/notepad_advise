from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy import create_engine
from model import User, user_major_association, major_subject_association
from sql_connect import engine

SessionLocal = sessionmaker(bind=engine)

class DatabaseError(Exception):
    pass

def read_entry(session, model, **filters):
    """Read entries from the database based on filters."""
    if not filters:
        raise ValueError("Filters cannot be empty")
    try:
        query = session.query(model).filter_by(**filters)
        entry = query.one_or_none()
        if not entry:
            raise NoResultFound(f"No {model.__name__} found with filters: {filters}")
        return entry
    except Exception as e:
        raise DatabaseError(f"Error reading {model.__name__}: {e}")

def get_all_entries(session, model, **filters):
    """Get all entries from the database, with optional filters."""
    try:
        query = session.query(model)
        if filters:
            query = query.filter_by(**filters)
        return query.all()
    except Exception as e:
        raise DatabaseError(f"Error retrieving entries from {model.__name__}: {e}")

def insert_entry(session, model, **kwargs):
    """Insert a new entry into the database."""
    try:
        entry = model(**kwargs)
        session.add(entry)
        session.commit()
        return entry
    except Exception as e:
        session.rollback()
        raise DatabaseError(f"Error inserting {model.__name__}: {e}")

def update_entry(session, model, filters: dict, updates: dict):
    """Update entries in the database based on filters."""
    if not filters or not updates:
        raise ValueError("Filters and updates cannot be empty")
    try:
        query = session.query(model).filter_by(**filters)
        entry = query.one_or_none()
        if not entry:
            raise NoResultFound(f"No {model.__name__} found with filters: {filters}")

        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
            else:
                raise AttributeError(f"Attribute {key} not found in {model.__name__}")
        session.commit()
        return entry
    except Exception as e:
        session.rollback()
        raise DatabaseError(f"Error updating {model.__name__}: {e}")

def delete_entry(session, model, **filters):
    """Soft delete an entry by setting `is_deleted` to True."""
    if not filters:
        raise ValueError("Filters cannot be empty")
    try:
        query = session.query(model).filter_by(**filters)
        entry = query.one_or_none()
        if not entry:
            raise NoResultFound(f"No {model.__name__} found with filters: {filters}")

        if hasattr(entry, 'is_deleted'):
            entry.is_deleted = True
            session.commit()
            return entry
        else:
            raise AttributeError(f"{model.__name__} does not support soft deletion.")
    except Exception as e:
        session.rollback()
        raise DatabaseError(f"Error deleting {model.__name__}: {e}")

def restore_entry(session, model, **filters):
    """Restore an entry by setting `is_deleted` to False."""
    if not filters:
        raise ValueError("Filters cannot be empty")
    try:
        query = session.query(model).filter_by(**filters)
        entry = query.one_or_none()
        if not entry:
            raise NoResultFound(f"No {model.__name__} found with filters: {filters}")

        if hasattr(entry, 'is_deleted'):
            entry.is_deleted = False
            session.commit()
            return entry
        else:
            raise AttributeError(f"{model.__name__} does not support soft deletion.")
    except Exception as e:
        session.rollback()
        raise DatabaseError(f"Error restoring {model.__name__}: {e}")

def get_all_pks(session, model):
    """Get all primary keys of a table without retrieving all data."""
    try:
        pk_column = model.__table__.primary_key.columns.values()[0]
        pks = session.query(model).with_entities(pk_column).all()
        return [pk[0] for pk in pks]
    except Exception as e:
        raise DatabaseError(f"Error fetching PKs from {model.__name__}: {e}")

def insert_into_join_table(session, join_table, **kwargs):
    """Insert entries into a join table for Many-to-Many relationships."""
    try:
        session.execute(join_table.insert().values(**kwargs))
        session.commit()
        return kwargs
    except Exception as e:
        session.rollback()
        raise DatabaseError(f"Error inserting into join table {join_table.name}: {e}")

def get_existing_association(session, major_id: str, subject_id: str):
    """Tìm quan hệ Giữa A và B"""
    try:
        result = session.query(major_subject_association).filter(
            major_subject_association.c.major_id == major_id,
            major_subject_association.c.subject_id == subject_id
        ).first()
        return result
    except Exception as e:
        raise DatabaseError(f"Error checking association: {e}")
