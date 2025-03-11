#!/bin/bash
python3 manage.py test ticket.tests.test_auth ticket.tests.test_student_dashboard ticket.tests.test_staff_views ticket.tests.test_staff_forms -v 2 