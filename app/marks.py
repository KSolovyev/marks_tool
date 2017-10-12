#!/usr/bin/env python
# coding=utf-8
import json
from optparse import OptionParser

import requests
from urlparse import urljoin
import unicodecsv as csv
from voluptuous import Schema, Coerce

from validators_utils import Sequence

BASE_API_URL = "https://park.mail.ru/rest_api/"


def join_urls(*args):
    result = ""
    for part in args:
        result = urljoin(result, str(part) if str(part)[-1] == '/' else str(part) + '/')
    return result


def prepare_session(csrf, cookie):
    session = requests.session()
    session.cookies["sessionid_gtp"] = cookie
    session.cookies["csrftoken"] = csrf
    session.headers["Accept-Language"] = "ru,en"
    session.headers["x-csrftoken"] = csrf
    return session


def check_students_consistent(name_index, new_marks, partial):
    api_miss_students = []
    for student, marks in new_marks.iteritems():
        if student not in name_index:
            api_miss_students.append(student)
    marks_miss_students = []
    for student in name_index:
        if student not in new_marks:
            marks_miss_students.append(student)
    if api_miss_students or (marks_miss_students and not partial):
        print "Students that are in the mark FILE but is absent in API data:"
        print u", ".join(api_miss_students)
        if not partial:
            print "Students that are in API set but is absent in the mark FILE:"
            print u", ".join(marks_miss_students)
        exit(1)


def execute(new_marks, csrf, cookie, discipline, options):
    discipline_url = join_urls(BASE_API_URL, "discipline_versions", discipline)
    session = prepare_session(csrf, cookie)
    response = session.get(join_urls(discipline_url, "students"))
    assert response.status_code == 200
    students = response.json()
    name_index = {student["full_name"]: student for student in students}

    check_students_consistent(name_index, new_marks, options.partial)

    print "Marks set is consistent with API\n"

    response = session.get(join_urls(discipline_url, "curriculum_marks"))
    assert response.status_code == 200
    marks_meta = response.json()

    response = session.get(join_urls(discipline_url, "student_marks"))
    assert response.status_code == 200
    marks = response.json()
    marks_index = {frozenset([mark["user"], mark["discipline_mark"]]): mark for mark in marks}

    for student_name, student_marks in new_marks.iteritems():
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
                response = session.patch(join_urls(discipline_url, "student_marks", mark["id"]),
                                         json=dict(value=student_mark))
                response.raise_for_status()
            else:
                response = session.post(join_urls(discipline_url, "student_marks"),
                                        json=dict(user=student["id"],
                                                  discipline_mark=mark_meta["id"],
                                                  value=student_mark))
                response.raise_for_status()
    print "All marks were successfully set"


def validate_marks(marks):
    return Schema({basestring: Sequence(Coerce(int))})(marks)


def parse_csv(csv_file):
    marks = {}
    with open(csv_file, 'r') as marks_csv:
        for line in csv.reader(marks_csv):
            marks[line[0]] = line[1:]
    return marks


def parse_json(json_file):
    with open(json_file, 'r') as marks_json:
        return json.load(marks_json)


if __name__ == "__main__":
    parser = OptionParser(usage="usage: %prog --csrf CSRF --cookie COOKIE --discipline DISCIPLINE FILE",
                          description="updates students' marks on park.mail.ru")

    # parser.add_option("--csv", help="CSV file with students and marks", metavar="FILE")
    parser.add_option("--partial",
                      help="check it when you use partial student list",
                      dest="partial",
                      action="store_true",
                      default=False)
    parser.add_option("--csrf", help="CSRF token from the park.mail.ru", metavar="CSRF")
    parser.add_option("--cookie", help="'sessionid_gtp' cookie from the park.mail.ru", metavar="COOKIE")
    parser.add_option("--discipline",
                      help="desired discipline id. Could be found from the browser dev tools",
                      metavar="DISCIPLINE_ID",
                      type="int")

    (option, args) = parser.parse_args()

    if not all([option.csrf, option.cookie, option.discipline]):
        parser.error("Not all required option are provided")

    if len(args) < 1:
        parser.error("You should specify csv or json file")

    try:
        marks = parse_json(args[0])
    except ValueError as e:
        marks = parse_csv(args[0])
    # else:
    #     marks = parse_json(option.json)
    marks = validate_marks(marks)
    execute(marks, option.csrf, option.cookie, option.discipline, option)
