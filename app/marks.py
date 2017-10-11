# coding=utf-8

import requests
from urlparse import urljoin

from constants import BASE_API_URL, DISCIPLINE, SESSIONID_GTP, CSRF, MARKS_TO_SET


def join_urls(*args):
    result = ""
    for part in args:
        result = urljoin(result, str(part) if str(part)[-1] == '/' else str(part) + '/')
    return result


def prepare_session():
    session = requests.session()
    session.cookies["sessionid_gtp"] = SESSIONID_GTP
    session.cookies["csrftoken"] = CSRF
    session.headers["Accept-Language"] = "ru,en"
    session.headers["x-csrftoken"] = CSRF
    return session


def check_students_consistent(name_index):
    api_miss_students = []
    for student, marks in MARKS_TO_SET.iteritems():
        if student not in name_index:
            api_miss_students.append(student)
    marks_miss_students = []
    for student in name_index:
        if student not in MARKS_TO_SET:
            marks_miss_students.append(student)
    if api_miss_students or marks_miss_students:
        print "Students that are in mark set but is absent in API:"
        print u", ".join(api_miss_students)
        print "Students that are in API set but is absent in mark set:"
        print u", ".join(marks_miss_students)
        exit(1)


if __name__ == "__main__":
    if not SESSIONID_GTP or not CSRF or not DISCIPLINE or not BASE_API_URL:
        print "You should set the constants first. See constants.py"
        exit(2)
    session = prepare_session()
    response = session.get(join_urls(BASE_API_URL, "discipline_versions", DISCIPLINE, "students"))
    assert response.status_code == 200
    students = response.json()
    name_index = {student["full_name"]: student for student in students}

    check_students_consistent(name_index)

    print "Marks set is consistent with API\n"

    response = session.get(join_urls(BASE_API_URL, "discipline_versions", DISCIPLINE, "curriculum_marks"))
    assert response.status_code == 200
    marks_meta = response.json()

    response = session.get(join_urls(BASE_API_URL, "discipline_versions", DISCIPLINE, "student_marks"))
    assert response.status_code == 200
    marks = response.json()
    marks_index = {frozenset([mark["user"], mark["discipline_mark"]]): mark for mark in marks}

    for student_name, student_marks in MARKS_TO_SET.iteritems():
        for (student_mark, mark_meta) in zip(student_marks, marks_meta):
            student = name_index[student_name]
            if mark_meta is None:
                print u"WARNING: student {name} is tend to have more marks than is available in discipline." + \
                      u" There is no place for {value}" \
                    .format(name=student_name,
                            value=student_mark)
                continue
            if student_mark > mark_meta["max_value"]:
                print u"WARNING: student {name} is tend to have {value} points for {mark_name}. But max is {max}\n" \
                    .format(name=student_name,
                            value=student_mark,
                            mark_name=mark_meta["short_title"],
                            max=mark_meta["max_value"])
                student_mark = mark_meta["max_value"]
            mark = marks_index.get(frozenset([student["id"], mark_meta["id"]]))
            if mark is not None:
                response = session.patch(join_urls(BASE_API_URL, "discipline_versions", DISCIPLINE, "student_marks", mark["id"]),
                                         json=dict(value=student_mark))
                response.raise_for_status()
            else:
                response = session.post(join_urls(BASE_API_URL, "discipline_versions", DISCIPLINE, "student_marks"),
                                        json=dict(user=student["id"],
                                                  discipline_mark=mark_meta["id"],
                                                  value=student_mark))
                response.raise_for_status()
    print "All marks were successfully set"
    exit(0)