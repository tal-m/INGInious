# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" A course class with some modification for users """

from collections import OrderedDict
from datetime import datetime

from common.courses import Course
from webapp.accessible_time import AccessibleTime
from common_frontend.database import get_database
from webapp.custom.tasks import FrontendTask
from webapp.user_data import UserData
from common_frontend.configuration import INGIniousConfiguration


class FrontendCourse(Course):
    """ A course with some modification for users """

    def __init__(self, courseid, content, task_factory):
        Course.__init__(self, courseid, content, task_factory)

        if self._content.get('nofrontend', False):
            raise Exception("That course is not allowed to be displayed directly in the webapp")

        if "name" in self._content and "admins" in self._content and isinstance(self._content["admins"], list):
            self._name = self._content['name']
            self._admins = self._content['admins']
            self._tutors = self._content.get('tutors', [])
            self._accessible = AccessibleTime(self._content.get("accessible", None))
            self._registration = AccessibleTime(self._content.get("registration", None))
            self._registration_password = self._content.get('registration_password', None)
            self._registration_ac = self._content.get('registration_ac', None)
            if self._registration_ac not in [None, "username", "realname", "email"]:
                raise Exception("Course has an invalid value for registration_ac: " + self.get_id())
            self._registration_ac_list = self._content.get('registration_ac_list', [])
            self._groups = self._content.get("groups", False)
            self._groups_student_choice = self._content.get("groups_student_choice", False)
        else:
            raise Exception("Course has an invalid description: " + self.get_id())

    def get_name(self):
        """ Return the name of this course """
        return self._name

    def get_staff(self, with_superadmin=True):
        """ Returns a list containing the usernames of all the staff users """
        return list(set(self.get_tutors() + self.get_admins(with_superadmin)))

    def get_admins(self, with_superadmin=True):
        """ Returns a list containing the usernames of the administrators of this course """
        if with_superadmin:
            return list(set(self._admins + INGIniousConfiguration.get('superadmins', [])))
        else:
            return self._admins

    def get_tutors(self):
        """ Returns a list containing the usernames of the tutors assigned to this course """
        return self._tutors

    def get_groups(self):
        """ Returns a list of the course groups"""
        return list(get_database().groups.find({"course_id": self.get_id()}).sort("description"))

    def is_open_to_non_staff(self):
        """ Returns true if the course is accessible by users that are not administrator of this course """
        return self._accessible.is_open()

    def is_open_to_user(self, username, check_group=False):
        """ Returns true if the course is open to this user """
        return (self._accessible.is_open() and self.is_user_registered(username, check_group)) or username in self.get_staff()

    def is_registration_possible(self, username):
        """ Returns true if users can register for this course """
        return self._accessible.is_open() and self._registration.is_open() and self.is_user_accepted_by_access_control(username)

    def is_password_needed_for_registration(self):
        """ Returns true if a password is needed for registration """
        return self._registration_password is not None

    def get_registration_password(self):
        """ Returns the password needed for registration (None if there is no password) """
        return self._registration_password

    def register_user(self, username, password=None, force=False):
        """ Register a user to the course. Returns True if the registration succeeded, False else. """
        if not force:
            if not self.is_registration_possible(username):
                return False
            if self.is_password_needed_for_registration() and self._registration_password != password:
                return False
        if self.is_open_to_user(username):
            return False  # already registered?
        get_database().registration.insert({"username": username, "courseid": self.get_id(), "date": datetime.now()})
        return True

    def unregister_user(self, username):
        """ Unregister a user from this course """
        get_database().registration.remove({"username": username, "courseid": self.get_id()})
        if self.is_group_course():
            get_database().groups.update({"course_id": self.get_id(), "users": username}, {"$pull":{"users": username}})

    def is_user_registered(self, username, check_group=False):
        """ Returns True if the user is registered """
        has_group = (not check_group) or \
                    (get_database().groups.find_one({"users": username, "course_id": self.get_id()}) is not None)

        return (get_database().registration.find_one({"username": username, "courseid": self.get_id()}) is not None)\
               and has_group or username in self.get_staff()

    def get_registered_users(self, with_admins=True):
        """ Get all the usernames that are registered to this course (in no particular order)"""
        l = [entry['username'] for entry in list(get_database().registration.find({"courseid": self.get_id()}, {"username": True, "_id": False}))]
        if with_admins:
            return list(set(l + self.get_staff()))
        else:
            return l

    def get_accessibility(self):
        """ Return the AccessibleTime object associated with the accessibility of this course """
        return self._accessible

    def get_registration_accessibility(self):
        """ Return the AccessibleTime object associated with the registration """
        return self._registration

    def get_user_completion_percentage(self, username=None):
        """ Returns the percentage (integer) of completion of this course by the current user (or username if it is not None)"""
        if username is None:
            import webapp.user as User

            username = User.get_username()
        cache = UserData(username).get_course_data(self)
        if cache is None:
            return 0
        if cache["total_tasks"] == 0:
            return 100
        return int(cache["task_succeeded"] * 100 / cache["total_tasks"])

    def get_user_grade(self, username=None):
        """ Return the grade (a floating-point number between 0 and 100) of the user (if username is None, it uses the currently logged-in user) """
        if username is None:
            import webapp.user as User

            username = User.get_username()
        cache = UserData(username).get_course_data(self)
        if cache is None:
            return 0
        total_weight = 0
        grade = 0

        for task_id, task in self.get_tasks().iteritems():
            if task.is_visible_by_user(username):
                total_weight += task.get_grading_weight()
                grade += cache["task_grades"].get(task_id, 0.0) * task.get_grading_weight()

        if total_weight == 0:
            return 0

        return grade / total_weight

    def get_tasks(self):
        return OrderedDict(sorted(Course.get_tasks(self).items(), key=lambda t: t[1].get_order()))

    def get_access_control_method(self):
        """ Returns either None, "username", "realname", or "email", depending on the method used to verify that users can register to the course """
        return self._registration_ac

    def get_access_control_list(self):
        """ Returns the list of all users allowed by the AC list """
        return self._registration_ac_list

    def get_user_group(self, username):
        """ Returns the group whose username belongs to """
        return get_database().groups.find_one({"course_id": self.get_id(), "users": username})

    def is_group_course(self):
        """ Returns True if the course submissions are made by groups """
        return self._groups

    def can_students_choose_group(self):
        """ Returns True if the students can choose their groups """
        return self._groups_student_choice

    def is_user_accepted_by_access_control(self, username):
        """ Returns True if the user is allowed by the ACL """
        if self.get_access_control_method() is None:
            return True
        elif self.get_access_control_method() == "username":
            return username in self.get_access_control_list()
        elif self.get_access_control_method() == "realname":
            return UserData(username).get_data()["realname"] in self.get_access_control_list()
        elif self.get_access_control_method() == "email":
            return UserData(username).get_data()["email"] in self.get_access_control_list()
        return False
