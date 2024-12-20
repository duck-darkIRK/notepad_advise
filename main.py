import json
import time

from fastapi import FastAPI, HTTPException, File, UploadFile, Response, Depends, Request
from sqlalchemy import insert
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from generate_module import generate_path
from model import Subject, Major, major_subject_association, User, user_major_association, user_subject_association
from sql_connect import get_db
from auth import AuthService
from services import process_subjects_file, process_majors_file

app = FastAPI()

def verify_cookie_and_session(request: Request, db_session: Session):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Session not found")
    return AuthService.verify_session(session_id, db_session)


@app.post("/register/")
async def register_user(user_data: dict, db_session: Session = Depends(get_db)):
    print(user_data)
    try:
        return AuthService.register_user(user_data, db_session)
    except HTTPException as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)

@app.post("/login/")
async def login_user(login_data: dict, response: Response, db_session: Session = Depends(get_db)):
    try:
        return AuthService.login_user(login_data, response, db_session)
    except HTTPException as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@app.post("/logout/")
async def logout_user(request: Request, response: Response, db_session: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Session not found")

    try:
        AuthService.logout_user(response, db_session, session_id)

        response.delete_cookie("session_id")

        return {"message": "Logged out successfully"}
    except HTTPException as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@app.post("/upload-subjects/")
async def upload_subjects(request: Request, file: UploadFile = File(...), db_session: Session = Depends(get_db)):
    print(request.cookies.get("session_id"))

    try:
        session_info = verify_cookie_and_session(request, db_session)

        if session_info['user']['role'] != 'admin':
            raise HTTPException(status_code=403, detail="You do not have permission to upload subjects")

        result = await process_subjects_file(file, db_session)
        return {"status": "success", "data": result}

    except HTTPException as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/subjects/")
async def get_all_subjects(request: Request, db: Session = Depends(get_db)):
    print(request.cookies.get("session_id"))
    try:
        verify_cookie_and_session(request, db)

        subjects = db.query(Subject).all()
        if subjects:
            return subjects
        else: return []

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/user-subjects/")
async def get_all_user_subjects(request: Request, db: Session = Depends(get_db)):
    try:
        profile = verify_cookie_and_session(request, db)
        user_id = profile["user"]["id"]

        user_majors = db.query(Major).join(user_major_association).filter(user_major_association.c.user_id == user_id).all()

        if not user_majors:
            raise HTTPException(status_code=404, detail="User is not enrolled in any major")

        subjects_with_type = {}

        for major in user_majors:
            for assoc in major.subjects:
                major_subject_assoc = db.query(major_subject_association).filter(
                    major_subject_association.c.major_id == major.id,
                    major_subject_association.c.subject_id == assoc.id
                ).all()

                subject_key = assoc.id
                if subject_key not in subjects_with_type:
                    subjects_with_type[subject_key] = {
                        "id": assoc.id,
                        "name": assoc.name,
                        "weight": assoc.weight,
                        "required": assoc.required,
                        "is_deleted": assoc.is_deleted,
                        "type": "optional"
                    }

                for assoc_item in major_subject_assoc:
                    if assoc_item.type == "required":
                        subjects_with_type[subject_key]["type"] = "required"
                        break
        return list(subjects_with_type.values())

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving subjects: {str(e)}")



@app.post("/subjects/")
async def create_subject(request: Request, subject: dict, db: Session = Depends(get_db)):
    try:
        session_info = verify_cookie_and_session(request, db)

        if session_info['user']['role'] != 'admin':
            raise HTTPException(status_code=403, detail="You do not have permission to create subjects")

        existing_subject = db.query(Subject).filter(Subject.id == subject['id']).first()
        if existing_subject:
            raise HTTPException(status_code=400, detail=f"Subject with id {subject['id']} already exists.")

        current_time = time.time()

        new_subject = Subject(
            id=subject['id'],
            name=subject.get('name'),
            weight=subject['weight'],
            required=subject.get('required', ''),
            is_deleted=subject.get('is_deleted', False),
            created_at=current_time,
            updated_at=current_time
        )

        db.add(new_subject)
        db.commit()
        db.refresh(new_subject)

        return {"status": "success", "data": new_subject}

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating subject: Integrity error: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating subject: {str(e)}")


@app.get("/subjects/{subject_code}")
async def get_subject(request: Request, subject_code: str, db: Session = Depends(get_db)):
    try:
        verify_cookie_and_session(request, db)

        subject = db.query(Subject).filter(Subject.id == subject_code).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        return subject
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error finding subject: {str(e)}")


@app.put("/subjects/{subject_code}")
async def update_subject(request: Request, subject_code: str, subject: dict, db: Session = Depends(get_db)):
    try:
        session_info = verify_cookie_and_session(request, db)

        if session_info['user']['role'] != 'admin':
            raise HTTPException(status_code=403, detail="You do not have permission to update subjects")

        existing_subject = db.query(Subject).filter(Subject.id == subject_code).first()
        if not existing_subject:
            raise HTTPException(status_code=404, detail="Subject not found")
            existing_subject.name = subject.get('name', existing_subject.name)
            existing_subject.weight = subject.get('weight', existing_subject.weight)
            existing_subject.required = subject.get('required', existing_subject.required)
            existing_subject.is_deleted = subject.get('is_deleted', existing_subject.is_deleted)
            existing_subject.updated_at = time.time()

            db.commit()
            db.refresh(existing_subject)

            return {"status": "success", "data": existing_subject}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating subject: {str(e)}")


@app.get("/subjects/")
async def get_all_subjects(db: Session = Depends(get_db)):
    try:
        subjects = db.query(Subject).filter(Subject.is_deleted == False).all()
        if not subjects:
            return []
        return subjects
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving subjects: {str(e)}")


@app.delete("/subjects/{subject_code}")
async def delete_subject(subject_code: str, db: Session = Depends(get_db)):
    try:
        subject = db.query(Subject).filter(Subject.id == subject_code).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        subject.is_deleted = True
        db.commit()
        db.refresh(subject)

        return {"status": "success", "message": "Subject deleted successfully"}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting subject: {str(e)}")


@app.get("/majors/")
async def get_all_majors(request: Request, db: Session = Depends(get_db)):
    try:
        verify_cookie_and_session(request, db)

        majors = db.query(Major).filter(Major.is_deleted == False).all()
        return majors
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error occurred.")


@app.get("/majors/{major_id}")
async def get_major_by_id(request: Request, major_id: str, db: Session = Depends(get_db)):
    try:
        verify_cookie_and_session(request, db)

        major = db.query(Major).filter(Major.id == major_id, Major.is_deleted == False).first()
        if not major:
            raise HTTPException(status_code=404, detail="Major not found")

        subjects = db.query(Subject).join(major_subject_association).filter(
            major_subject_association.c.major_id == major_id
        ).all()

        result = {
            "id": major.id,
            "name": major.name,
            "subjects": [{"id": subject.id, "name": subject.name, "weight": subject.weight} for subject in subjects]
        }

        return result
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error occurred.")



@app.post("/majors/")
async def create_major(request: Request, major: dict, db: Session = Depends(get_db)):
    try:
        session_info = verify_cookie_and_session(request, db)

        if session_info['user']['role'] != 'admin':
            raise HTTPException(status_code=403, detail="You do not have permission to create a major")

        new_major = Major(
            id=major.get('id'),
            name=major.get('name'),
            created_at=time.time(),
            updated_at=time.time()
        )
        db.add(new_major)
        db.commit()
        db.refresh(new_major)
        return {"status": "success", "data": new_major}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/majors/{major_id}")
async def update_major(request: Request, major_id: str, major: dict, db: Session = Depends(get_db)):
    try:
        session_info = verify_cookie_and_session(request, db)

        if session_info['user']['role'] != 'admin':
            raise HTTPException(status_code=403, detail="You do not have permission to update majors")

        existing_major = db.query(Major).filter(Major.id == major_id, Major.is_deleted == False).first()
        if not existing_major:
            raise HTTPException(status_code=404, detail="Major not found")

        existing_major.name = major.get('name', existing_major.name)
        existing_major.updated_at = time.time()

        db.commit()
        db.refresh(existing_major)
        return {"status": "success", "data": existing_major}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/majors/{major_id}")
async def delete_major(request: Request, major_id: str, db: Session = Depends(get_db)):
    try:
        session_info = verify_cookie_and_session(request, db)

        if session_info['user']['role'] != 'admin':
            raise HTTPException(status_code=403, detail="You do not have permission to delete majors")

        existing_major = db.query(Major).filter(Major.id == major_id).first()
        if not existing_major:
            raise HTTPException(status_code=404, detail="Major not found")

        existing_major.is_deleted = True
        existing_major.updated_at = time.time()

        db.commit()
        return {"status": "success", "message": "Major deleted successfully"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/upload-majors/")
async def upload_major(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        result = await process_majors_file(file, db)
        return result
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

@app.post("/assign-subject/")
async def assign_subject(request: Request, db: Session = Depends(get_db)):
    body = await request.json()

    major_id = body.get("major_id")
    subject_id = body.get("subject_id")
    subject_type = body.get("subject_type")

    if not major_id or not subject_id or not subject_type:
        raise HTTPException(status_code=400, detail="Thiếu thông tin ngành hoặc môn học")

    if subject_type not in ["required", "optional"]:
        raise HTTPException(status_code=400, detail="Loại môn không hợp lệ")

    major = db.query(Major).filter(Major.id == major_id).first()
    if not major:
        raise HTTPException(status_code=404, detail="Ngành không tồn tại")

    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Môn học không tồn tại")

    existing_assignment = db.execute(
        major_subject_association.select()
        .where(major_subject_association.c.major_id == major_id)
        .where(major_subject_association.c.subject_id == subject_id)
    ).fetchone()

    if existing_assignment:
        raise HTTPException(status_code=400, detail="Môn học đã được gán cho ngành này")

    stmt = insert(major_subject_association).values(
        major_id=major_id,
        subject_id=subject_id,
        type=subject_type
    )
    db.execute(stmt)
    db.commit()

    return {"message": "Môn học đã được gán thành công"}

@app.get("/profile/")
async def get_profile(request: Request, db: Session = Depends(get_db)):
    return verify_cookie_and_session(request, db)

@app.post("/add-score/")
async def add_score(request: Request, db: Session = Depends(get_db)):
    profile = verify_cookie_and_session(request, db)
    user_id = profile["user"]["id"]

    body = await request.json()
    subject_id = body.get("subject_id")
    score = body.get("score")
    note = body.get("note")

    if not user_id or not subject_id or score is None:
        print(user_id, subject_id, score)
        raise HTTPException(status_code=400, detail="Thiếu thông tin đầu vào")

    try:
        association = db.execute(
            user_subject_association.select().where(
                user_subject_association.c.user_id == user_id,
                user_subject_association.c.subject_id == subject_id
            )
        ).first()

        if association:
            db.execute(
                user_subject_association.update()
                .where(
                    user_subject_association.c.user_id == user_id,
                    user_subject_association.c.subject_id == subject_id
                )
                .values(score=score, note=note)
            )
            message = "Cập nhật điểm thành công"
        else:
            db.execute(
                user_subject_association.insert().values(
                    user_id=user_id,
                    subject_id=subject_id,
                    score=score,
                    note=note
                )
            )
            message = "Thêm điểm thành công"

        db.commit()
        return {"message": message}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Đã xảy ra lỗi: {str(e)}")

@app.get("/user-scores/")
async def get_user_scores(request: Request, db: Session = Depends(get_db)):
    try:
        session_data = verify_cookie_and_session(request, db)
        if "user" not in session_data or not session_data["user"].get("id"):
            raise HTTPException(status_code=401, detail="Không xác định được người dùng từ session")

        user_id = session_data["user"]["id"]

        query = db.execute(
            user_subject_association
            .join(Subject, user_subject_association.c.subject_id == Subject.id)
            .select()
            .where(user_subject_association.c.user_id == user_id)
        ).fetchall()

        if not query:
            return []

        result = []
        print(query)
        for row in query:
            result.append({
                "subject_id": row[1],
                "subject_name": row[4].name,
                "score": row[2] if row[2] is not None else "Chưa có điểm",
                "weight": row[4].weight,
                "created_at": row[4].created_at,
                "note": row[3]
            })

        return {"user_id": user_id, "scores": result}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Đã xảy ra lỗi: {str(e)}")

@app.post("/add-major/")
async def add_major(request: Request, db: Session = Depends(get_db)):
    profile = verify_cookie_and_session(request, db)
    user_id = profile["user"]["id"]

    body = await request.json()
    major_id = body.get("major_id")

    if not user_id or not major_id:
        raise HTTPException(status_code=400, detail="Thiếu thông tin đầu vào")

    try:
        association = db.execute(
            user_major_association.select().where(
                user_major_association.c.user_id == user_id,
                user_major_association.c.major_id == major_id
            )
        ).first()

        if association:
            message = "Chuyên ngành đã được gán cho người dùng"
        else:
            db.execute(
                insert(user_major_association).values(
                    user_id=user_id,
                    major_id=major_id
                )
            )
            message = "Thêm chuyên ngành cho người dùng thành công"

        db.commit()
        return {"message": message}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Đã xảy ra lỗi: {str(e)}")

@app.post("/remove-major/")
async def remove_major(request: Request, db: Session = Depends(get_db)):
    profile = verify_cookie_and_session(request, db)
    user_id = profile["user"]["id"]

    try:
        body = await request.json()
        major_id = body.get("major_id")

        if not user_id or not major_id:
            raise HTTPException(status_code=400, detail="Thiếu thông tin đầu vào")

        association = db.execute(
            user_major_association.select().where(
                user_major_association.c.user_id == user_id,
                user_major_association.c.major_id == major_id
            )
        ).first()

        print(f"Association found: {association}")

        if not association:
            raise HTTPException(status_code=404, detail="Bạn không có chuyên ngành này")

        db.execute(
            user_major_association.delete().where(
                user_major_association.c.user_id == user_id,
                user_major_association.c.major_id == major_id
            )
        )
        db.commit()

        return {"message": "Xóa chuyên ngành khỏi người dùng thành công"}

    except HTTPException as e:
        print(f"HTTPException: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"SQLAlchemyError: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    except Exception as e:
        print(f"General Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Đã xảy ra lỗi: {str(e)}")


@app.get("/full-learned-subject/")
async def get_all_learned_subjects(request: Request, db: Session = Depends(get_db)):
    try:
        profile = verify_cookie_and_session(request, db)
        user_id = profile["user"]["id"]

        user_subjects = db.query(Subject).join(user_subject_association).filter(user_subject_association.c.user_id == user_id).all()

        if not user_subjects:
            return  []

        subjects_with_type = {}

        for subject in user_subjects:
            major_subject_assoc = db.query(major_subject_association).filter(
                major_subject_association.c.subject_id == subject.id
            ).all()

            subject_key = subject.id

            if subject_key not in subjects_with_type:
                subjects_with_type[subject_key] = {
                    "id": subject.id,
                    "name": subject.name,
                    "weight": subject.weight,
                    "required": subject.required,
                    "is_deleted": subject.is_deleted,
                    "type": "optional"
                }

            for assoc_item in major_subject_assoc:
                if assoc_item.type == "required":
                    subjects_with_type[subject_key]["type"] = "required"
                    break

        return list(subjects_with_type.values())

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving subjects: {str(e)}")

@app.post("/generate_path/")
async def generate_path_src(request: Request, db: Session = Depends(get_db)):
    verify_cookie_and_session(request, db)

    try:
        data = await request.json()
        min_weight = int(data.get('min_weight'))
        max_weight = int(data.get('max_weight'))
        force = bool(data.get('force', True))
    except KeyError:
        return {"error": "min_weight and max_weight are required"}

    subjects = await get_all_user_subjects(request, db)
    learned = await get_all_learned_subjects(request, db)

    if not force:
        subjects = [subject for subject in subjects if subject['type'] == 'required']

    return generate_path(subjects, learned, min_weight, max_weight)
