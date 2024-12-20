import json
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from sql_query import insert_entry, get_all_pks, insert_into_join_table, get_existing_association
from model import Subject, major_subject_association, Major


async def process_subjects_file(file: UploadFile, db_session: Session):
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    existing_ids = get_all_pks(db_session, Subject)

    added_subjects = []
    duplicates = []
    errors = []

    for item in data:
        subject_id = item.get("id")
        subject_name = item.get("name")

        if not subject_id or not subject_name:
            errors.append({"error": "Missing 'id' or 'name' in subject", "subject": item})
            continue

        if subject_id in existing_ids:
            duplicates.append(item)
            continue

        try:
            subject = insert_entry(
                session=db_session,
                model=Subject,
                id=subject_id,
                name=subject_name,
                weight=item["weight"],
                required=item.get("required", "")
            )
            added_subjects.append(subject_id)
        except Exception as e:
            errors.append({"error": str(e), "subject": item})

    return {
        "message": f"Processed {len(data)} subjects",
        "added_subjects": added_subjects,
        "duplicates": duplicates,
        "errors": errors
    }


async def process_majors_file(file, db):
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Input data must be a list of objects")

    existing_major_ids = get_all_pks(db, Major)
    existing_subject_ids = get_all_pks(db, Subject)

    added_majors = []
    added_associations = []
    errors = []

    for item in data:
        major_data = item.get("major")
        subjects_data = item.get("subjects", [])

        if not major_data or not subjects_data:
            errors.append({"error": "Missing 'major' or 'subjects' in one of the items", "item": item})
            continue

        major_id = major_data.get("id")
        major_name = major_data.get("name")

        if not major_id or not major_name:
            errors.append({"error": "Major must have an 'id' and 'name'", "major": major_data})
            continue

        missing_subjects = [sub for sub in subjects_data if sub["id"] not in existing_subject_ids]
        if missing_subjects:
            errors.append({"error": "Some subjects do not exist", "missing_subjects": missing_subjects})
            continue

        if major_id not in existing_major_ids:
            try:
                insert_entry(db, Major, id=major_id, name=major_name)
                added_majors.append(major_id)
                existing_major_ids.add(major_id)
            except Exception as e:
                db.rollback()
                errors.append({"error": str(e), "major": major_data})
                continue

        for subject in subjects_data:
            subject_id = subject["id"]
            subject_type = subject.get("type", "required")

            try:
                existing_association = db.query(major_subject_association).filter(
                    major_subject_association.c.major_id == major_id,
                    major_subject_association.c.subject_id == subject_id
                ).first()

                if not existing_association:
                    new_association = major_subject_association.insert().values(
                        major_id=major_id,
                        subject_id=subject_id,
                        type=subject_type
                    )
                    db.execute(new_association)
                    added_associations.append({"major_id": major_id, "subject_id": subject_id})

            except Exception as e:
                db.rollback()
                errors.append({
                    "error": str(e),
                    "major_id": major_id,
                    "subject_id": subject_id
                })

    db.commit()
    return {
        "message": f"Processed {len(data)} majors",
        "added_majors": added_majors,
        "added_associations": added_associations,
        "errors": errors
    }

