from model import User, Major, Subject, Transcript, Class, user_major_association
from sql_query import get_all_pks, restore_entry, delete_entry, update_entry, insert_entry, read_entry, \
    insert_into_join_table


def run_tests():
    try:
        # Test với User
        print("--- Testing User ---")
        insert_entry(User, uuid="12345", code="U001", role="student", password="securepassword")
        users = read_entry(User, code="U001")
        print("Users after creation:", users)
        updated_user = update_entry(User, {"code": "U001"}, {"role": "admin"})
        print("Updated user:", updated_user)
        deleted_user = delete_entry(User, code="U001")
        print("Deleted user:", deleted_user)
        restored_user = restore_entry(User, code="U001")
        print("Restored user:", restored_user)
        pks = get_all_pks(User)
        print("All User PKs:", pks)

        # Test với Major
        print("--- Testing Major ---")
        insert_entry(Major, id="M001", name="Computer Science")
        majors = read_entry(Major, id="M001")
        print("Majors after creation:", majors)
        updated_major = update_entry(Major, {"id": "M001"}, {"name": "Advanced CS"})
        print("Updated major:", updated_major)
        deleted_major = delete_entry(Major, id="M001")
        print("Deleted major:", deleted_major)
        restored_major = restore_entry(Major, id="M001")
        print("Restored major:", restored_major)
        pks_majors = get_all_pks(Major)
        print("All Major PKs:", pks_majors)

        # Test với Subject
        print("--- Testing Subject ---")
        insert_entry(Subject, id="S001", name="Algorithms", weight=3.0)
        subjects = read_entry(Subject, id="S001")
        print("Subjects after creation:", subjects)
        updated_subject = update_entry(Subject, {"id": "S001"}, {"name": "Advanced Algorithms"})
        print("Updated subject:", updated_subject)
        deleted_subject = delete_entry(Subject, id="S001")
        print("Deleted subject:", deleted_subject)
        restored_subject = restore_entry(Subject, id="S001")
        print("Restored subject:", restored_subject)
        pks_subjects = get_all_pks(Subject)
        print("All Subject PKs:", pks_subjects)

        # Test với Transcript
        print("--- Testing Transcript ---")
        insert_entry(Transcript, id=1, score=95.0, owner_id="12345", subject_id="S001")
        transcripts = read_entry(Transcript, id=1)
        print("Transcripts after creation:", transcripts)
        updated_transcript = update_entry(Transcript, {"id": 1}, {"score": 97.0})
        print("Updated transcript:", updated_transcript)
        deleted_transcript = delete_entry(Transcript, id=1)
        print("Deleted transcript:", deleted_transcript)
        restored_transcript = restore_entry(Transcript, id=1)
        print("Restored transcript:", restored_transcript)
        pks_transcripts = get_all_pks(Transcript)
        print("All Transcript PKs:", pks_transcripts)

        # Test với Class
        print("--- Testing Class ---")
        insert_entry(Class, id="C001", semester="2024-1", name="Data Structures", time=10, day=2, subject_id="S001")
        classes = read_entry(Class, id="C001")
        print("Classes after creation:", classes)
        updated_class = update_entry(Class, {"id": "C001"}, {"name": "Advanced Data Structures"})
        print("Updated class:", updated_class)
        deleted_class = delete_entry(Class, id="C001")
        print("Deleted class:", deleted_class)
        restored_class = restore_entry(Class, id="C001")
        print("Restored class:", restored_class)
        pks_classes = get_all_pks(Class)
        print("All Class PKs:", pks_classes)

        insert_into_join_table(user_major_association, user_id="12345", major_id="M01")


    except Exception as e:
        print(f"An error occurred: {e}")



if __name__ == "__main__":
    run_tests()
