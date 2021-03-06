# -*- coding: utf-8 -*-
import sys

import six
from nose.plugins.skip import SkipTest

sys.path[0:0] = [""]

import datetime
import unittest
import uuid
import math
import itertools
import re
import six

try:
    import dateutil
except ImportError:
    dateutil = None

from decimal import Decimal

from bson import Binary, DBRef, ObjectId
try:
    from bson.int64 import Int64
except ImportError:
    Int64 = long

from mongoengine import *
from mongoengine.connection import get_db
from mongoengine.base import _document_registry
from mongoengine.base.datastructures import BaseDict, EmbeddedDocumentList
from mongoengine.errors import NotRegistered
from mongoengine.python_support import PY3, b, bin_type

__all__ = ("FieldTest", "EmbeddedDocumentListFieldTestCase")


class FieldTest(unittest.TestCase):

    def setUp(self):
        connect(db='mongoenginetest')
        self.db = get_db()

    def tearDown(self):
        self.db.drop_collection('fs.files')
        self.db.drop_collection('fs.chunks')
        self.db.drop_collection('mongoengine.counters')

    def test_default_values_nothing_set(self):
        """Ensure that default field values are used when creating a document.
        """
        class Person(Document):
            name = StringField()
            age = IntField(default=30, required=False)
            userid = StringField(default=lambda: 'test', required=True)
            created = DateTimeField(default=datetime.datetime.utcnow)

        person = Person(name="Ross")

        # Confirm saving now would store values
        data_to_be_saved = sorted(person.to_mongo().keys())
        self.assertEqual(
            data_to_be_saved, ['age', 'created', 'name', 'userid'])

        self.assertTrue(person.validate() is None)

        self.assertEqual(person.name, person.name)
        self.assertEqual(person.age, person.age)
        self.assertEqual(person.userid, person.userid)
        self.assertEqual(person.created, person.created)

        self.assertEqual(person._data['name'], person.name)
        self.assertEqual(person._data['age'], person.age)
        self.assertEqual(person._data['userid'], person.userid)
        self.assertEqual(person._data['created'], person.created)

        # Confirm introspection changes nothing
        data_to_be_saved = sorted(person.to_mongo().keys())
        self.assertEqual(
            data_to_be_saved, ['age', 'created', 'name', 'userid'])

    def test_default_values_set_to_None(self):
        """Ensure that default field values are used when creating a document.
        """
        class Person(Document):
            name = StringField()
            age = IntField(default=30, required=False)
            userid = StringField(default=lambda: 'test', required=True)
            created = DateTimeField(default=datetime.datetime.utcnow)

        # Trying setting values to None
        person = Person(name=None, age=None, userid=None, created=None)

        # Confirm saving now would store values
        data_to_be_saved = sorted(person.to_mongo().keys())
        self.assertEqual(data_to_be_saved, ['age', 'created', 'userid'])

        self.assertTrue(person.validate() is None)

        self.assertEqual(person.name, person.name)
        self.assertEqual(person.age, person.age)
        self.assertEqual(person.userid, person.userid)
        self.assertEqual(person.created, person.created)

        self.assertEqual(person._data['name'], person.name)
        self.assertEqual(person._data['age'], person.age)
        self.assertEqual(person._data['userid'], person.userid)
        self.assertEqual(person._data['created'], person.created)

        # Confirm introspection changes nothing
        data_to_be_saved = sorted(person.to_mongo().keys())
        self.assertEqual(data_to_be_saved, ['age', 'created', 'userid'])

    def test_default_values_when_setting_to_None(self):
        """Ensure that default field values are used when creating a document.
        """
        class Person(Document):
            name = StringField()
            age = IntField(default=30, required=False)
            userid = StringField(default=lambda: 'test', required=True)
            created = DateTimeField(default=datetime.datetime.utcnow)

        person = Person()
        person.name = None
        person.age = None
        person.userid = None
        person.created = None

        # Confirm saving now would store values
        data_to_be_saved = sorted(person.to_mongo().keys())
        self.assertEqual(data_to_be_saved, ['age', 'created', 'userid'])

        self.assertTrue(person.validate() is None)

        self.assertEqual(person.name, person.name)
        self.assertEqual(person.age, person.age)
        self.assertEqual(person.userid, person.userid)
        self.assertEqual(person.created, person.created)

        self.assertEqual(person._data['name'], person.name)
        self.assertEqual(person._data['age'], person.age)
        self.assertEqual(person._data['userid'], person.userid)
        self.assertEqual(person._data['created'], person.created)

        # Confirm introspection changes nothing
        data_to_be_saved = sorted(person.to_mongo().keys())
        self.assertEqual(data_to_be_saved, ['age', 'created', 'userid'])

    def test_default_values_when_deleting_value(self):
        """Ensure that default field values are used when creating a document.
        """
        class Person(Document):
            name = StringField()
            age = IntField(default=30, required=False)
            userid = StringField(default=lambda: 'test', required=True)
            created = DateTimeField(default=datetime.datetime.utcnow)

        person = Person(name="Ross")
        del person.name
        del person.age
        del person.userid
        del person.created

        data_to_be_saved = sorted(person.to_mongo().keys())
        self.assertEqual(data_to_be_saved, ['age', 'created', 'userid'])

        self.assertTrue(person.validate() is None)

        self.assertEqual(person.name, person.name)
        self.assertEqual(person.age, person.age)
        self.assertEqual(person.userid, person.userid)
        self.assertEqual(person.created, person.created)

        self.assertEqual(person._data['name'], person.name)
        self.assertEqual(person._data['age'], person.age)
        self.assertEqual(person._data['userid'], person.userid)
        self.assertEqual(person._data['created'], person.created)

        # Confirm introspection changes nothing
        data_to_be_saved = sorted(person.to_mongo().keys())
        self.assertEqual(data_to_be_saved, ['age', 'created', 'userid'])

    def test_required_values(self):
        """Ensure that required field constraints are enforced.
        """
        class Person(Document):
            name = StringField(required=True)
            age = IntField(required=True)
            userid = StringField()

        person = Person(name="Test User")
        self.assertRaises(ValidationError, person.validate)
        person = Person(age=30)
        self.assertRaises(ValidationError, person.validate)

    def test_not_required_handles_none_in_update(self):
        """Ensure that every fields should accept None if required is False.
        """

        class HandleNoneFields(Document):
            str_fld = StringField()
            int_fld = IntField()
            flt_fld = FloatField()
            comp_dt_fld = ComplexDateTimeField()

        HandleNoneFields.drop_collection()

        doc = HandleNoneFields()
        doc.str_fld = u'spam ham egg'
        doc.int_fld = 42
        doc.flt_fld = 4.2
        doc.com_dt_fld = datetime.datetime.utcnow()
        doc.save()

        res = HandleNoneFields.objects(id=doc.id).update(
            set__str_fld=None,
            set__int_fld=None,
            set__flt_fld=None,
            set__comp_dt_fld=None,
        )
        self.assertEqual(res, 1)

        # Retrive data from db and verify it.
        ret = HandleNoneFields.objects.all()[0]
        self.assertEqual(ret.str_fld, None)
        self.assertEqual(ret.int_fld, None)
        self.assertEqual(ret.flt_fld, None)

        # Return current time if retrived value is None.
        self.assertTrue(isinstance(ret.comp_dt_fld, datetime.datetime))

    def test_not_required_handles_none_from_database(self):
        """Ensure that every fields can handle null values from the database.
        """

        class HandleNoneFields(Document):
            str_fld = StringField(required=True)
            int_fld = IntField(required=True)
            flt_fld = FloatField(required=True)
            comp_dt_fld = ComplexDateTimeField(required=True)

        HandleNoneFields.drop_collection()

        doc = HandleNoneFields()
        doc.str_fld = u'spam ham egg'
        doc.int_fld = 42
        doc.flt_fld = 4.2
        doc.com_dt_fld = datetime.datetime.utcnow()
        doc.save()

        collection = self.db[HandleNoneFields._get_collection_name()]
        obj = collection.update({"_id": doc.id}, {"$unset": {
            "str_fld": 1,
            "int_fld": 1,
            "flt_fld": 1,
            "comp_dt_fld": 1}
        })

        # Retrive data from db and verify it.
        ret = HandleNoneFields.objects.all()[0]

        self.assertEqual(ret.str_fld, None)
        self.assertEqual(ret.int_fld, None)
        self.assertEqual(ret.flt_fld, None)
        # Return current time if retrived value is None.
        self.assertTrue(isinstance(ret.comp_dt_fld, datetime.datetime))

        self.assertRaises(ValidationError, ret.validate)

    def test_int_and_float_ne_operator(self):
        class TestDocument(Document):
            int_fld = IntField()
            float_fld = FloatField()

        TestDocument.drop_collection()

        TestDocument(int_fld=None, float_fld=None).save()
        TestDocument(int_fld=1, float_fld=1).save()

        self.assertEqual(1, TestDocument.objects(int_fld__ne=None).count())
        self.assertEqual(1, TestDocument.objects(float_fld__ne=None).count())

    def test_long_ne_operator(self):
        class TestDocument(Document):
            long_fld = LongField()

        TestDocument.drop_collection()

        TestDocument(long_fld=None).save()
        TestDocument(long_fld=1).save()

        self.assertEqual(1, TestDocument.objects(long_fld__ne=None).count())

    def test_object_id_validation(self):
        """Ensure that invalid values cannot be assigned to string fields.
        """
        class Person(Document):
            name = StringField()

        person = Person(name='Test User')
        self.assertEqual(person.id, None)

        person.id = 47
        self.assertRaises(ValidationError, person.validate)

        person.id = 'abc'
        self.assertRaises(ValidationError, person.validate)

        person.id = '497ce96f395f2f052a494fd4'
        person.validate()

    def test_string_validation(self):
        """Ensure that invalid values cannot be assigned to string fields.
        """
        class Person(Document):
            name = StringField(max_length=20)
            userid = StringField(r'[0-9a-z_]+$')

        person = Person(name=34)
        self.assertRaises(ValidationError, person.validate)

        # Test regex validation on userid
        person = Person(userid='test.User')
        self.assertRaises(ValidationError, person.validate)

        person.userid = 'test_user'
        self.assertEqual(person.userid, 'test_user')
        person.validate()

        # Test max length validation on name
        person = Person(name='Name that is more than twenty characters')
        self.assertRaises(ValidationError, person.validate)

        person.name = 'Shorter name'
        person.validate()

    def test_url_validation(self):
        """Ensure that URLFields validate urls properly.
        """
        class Link(Document):
            url = URLField()

        link = Link()
        link.url = 'google'
        self.assertRaises(ValidationError, link.validate)

        link.url = 'http://www.google.com:8080'
        link.validate()

    def test_url_scheme_validation(self):
        """Ensure that URLFields validate urls with specific schemes properly.
        """
        class Link(Document):
            url = URLField()

        class SchemeLink(Document):
            url = URLField(schemes=['ws', 'irc'])

        link = Link()
        link.url = 'ws://google.com'
        self.assertRaises(ValidationError, link.validate)

        scheme_link = SchemeLink()
        scheme_link.url = 'ws://google.com'
        scheme_link.validate()

    def test_int_validation(self):
        """Ensure that invalid values cannot be assigned to int fields.
        """
        class Person(Document):
            age = IntField(min_value=0, max_value=110)

        person = Person()
        person.age = 50
        person.validate()

        person.age = -1
        self.assertRaises(ValidationError, person.validate)
        person.age = 120
        self.assertRaises(ValidationError, person.validate)
        person.age = 'ten'
        self.assertRaises(ValidationError, person.validate)

    def test_long_validation(self):
        """Ensure that invalid values cannot be assigned to long fields.
        """
        class TestDocument(Document):
            value = LongField(min_value=0, max_value=110)

        doc = TestDocument()
        doc.value = 50
        doc.validate()

        doc.value = -1
        self.assertRaises(ValidationError, doc.validate)
        doc.age = 120
        self.assertRaises(ValidationError, doc.validate)
        doc.age = 'ten'
        self.assertRaises(ValidationError, doc.validate)

    def test_float_validation(self):
        """Ensure that invalid values cannot be assigned to float fields.
        """
        class Person(Document):
            height = FloatField(min_value=0.1, max_value=3.5)

        class BigPerson(Document):
            height = FloatField()

        person = Person()
        person.height = 1.89
        person.validate()

        person.height = '2.0'
        self.assertRaises(ValidationError, person.validate)

        person.height = 0.01
        self.assertRaises(ValidationError, person.validate)

        person.height = 4.0
        self.assertRaises(ValidationError, person.validate)

        person_2 = Person(height='something invalid')
        self.assertRaises(ValidationError, person_2.validate)

        big_person = BigPerson()

        for value, value_type in enumerate(six.integer_types):
            big_person.height = value_type(value)
            big_person.validate()

        big_person.height = 2 ** 500
        big_person.validate()

        big_person.height = 2 ** 100000  # Too big for a float value
        self.assertRaises(ValidationError, big_person.validate)

    def test_decimal_validation(self):
        """Ensure that invalid values cannot be assigned to decimal fields.
        """
        class Person(Document):
            height = DecimalField(min_value=Decimal('0.1'),
                                  max_value=Decimal('3.5'))

        Person.drop_collection()

        Person(height=Decimal('1.89')).save()
        person = Person.objects.first()
        self.assertEqual(person.height, Decimal('1.89'))

        person.height = '2.0'
        person.save()
        person.height = 0.01
        self.assertRaises(ValidationError, person.validate)
        person.height = Decimal('0.01')
        self.assertRaises(ValidationError, person.validate)
        person.height = Decimal('4.0')
        self.assertRaises(ValidationError, person.validate)
        person.height = 'something invalid'
        self.assertRaises(ValidationError, person.validate)

        person_2 = Person(height='something invalid')
        self.assertRaises(ValidationError, person_2.validate)

        Person.drop_collection()

    def test_decimal_comparison(self):

        class Person(Document):
            money = DecimalField()

        Person.drop_collection()

        Person(money=6).save()
        Person(money=8).save()
        Person(money=10).save()

        self.assertEqual(2, Person.objects(money__gt=Decimal("7")).count())
        self.assertEqual(2, Person.objects(money__gt=7).count())
        self.assertEqual(2, Person.objects(money__gt="7").count())

    def test_decimal_storage(self):
        class Person(Document):
            btc = DecimalField(precision=4)

        Person.drop_collection()
        Person(btc=10).save()
        Person(btc=10.1).save()
        Person(btc=10.11).save()
        Person(btc="10.111").save()
        Person(btc=Decimal("10.1111")).save()
        Person(btc=Decimal("10.11111")).save()

        # How its stored
        expected = [{'btc': 10.0}, {'btc': 10.1}, {'btc': 10.11},
                    {'btc': 10.111}, {'btc': 10.1111}, {'btc': 10.1111}]
        actual = list(Person.objects.exclude('id').as_pymongo())
        self.assertEqual(expected, actual)

        # How it comes out locally
        expected = [Decimal('10.0000'), Decimal('10.1000'), Decimal('10.1100'),
                    Decimal('10.1110'), Decimal('10.1111'), Decimal('10.1111')]
        actual = list(Person.objects().scalar('btc'))
        self.assertEqual(expected, actual)

    def test_boolean_validation(self):
        """Ensure that invalid values cannot be assigned to boolean fields.
        """
        class Person(Document):
            admin = BooleanField()

        person = Person()
        person.admin = True
        person.validate()

        person.admin = 2
        self.assertRaises(ValidationError, person.validate)
        person.admin = 'Yes'
        self.assertRaises(ValidationError, person.validate)

    def test_uuid_field_string(self):
        """Test UUID fields storing as String
        """
        class Person(Document):
            api_key = UUIDField(binary=False)

        Person.drop_collection()

        uu = uuid.uuid4()
        Person(api_key=uu).save()
        self.assertEqual(1, Person.objects(api_key=uu).count())
        self.assertEqual(uu, Person.objects.first().api_key)

        person = Person()
        valid = (uuid.uuid4(), uuid.uuid1())
        for api_key in valid:
            person.api_key = api_key
            person.validate()

        invalid = ('9d159858-549b-4975-9f98-dd2f987c113g',
                   '9d159858-549b-4975-9f98-dd2f987c113')
        for api_key in invalid:
            person.api_key = api_key
            self.assertRaises(ValidationError, person.validate)

    def test_uuid_field_binary(self):
        """Test UUID fields storing as Binary object
        """
        class Person(Document):
            api_key = UUIDField(binary=True)

        Person.drop_collection()

        uu = uuid.uuid4()
        Person(api_key=uu).save()
        self.assertEqual(1, Person.objects(api_key=uu).count())
        self.assertEqual(uu, Person.objects.first().api_key)

        person = Person()
        valid = (uuid.uuid4(), uuid.uuid1())
        for api_key in valid:
            person.api_key = api_key
            person.validate()

        invalid = ('9d159858-549b-4975-9f98-dd2f987c113g',
                   '9d159858-549b-4975-9f98-dd2f987c113')
        for api_key in invalid:
            person.api_key = api_key
            self.assertRaises(ValidationError, person.validate)

    def test_datetime_validation(self):
        """Ensure that invalid values cannot be assigned to datetime fields.
        """
        class LogEntry(Document):
            time = DateTimeField()

        log = LogEntry()
        log.time = datetime.datetime.now()
        log.validate()

        log.time = datetime.date.today()
        log.validate()

        log.time = datetime.datetime.now().isoformat(' ')
        log.validate()

        if dateutil:
            log.time = datetime.datetime.now().isoformat('T')
            log.validate()

        log.time = -1
        self.assertRaises(ValidationError, log.validate)
        log.time = 'ABC'
        self.assertRaises(ValidationError, log.validate)

    def test_datetime_tz_aware_mark_as_changed(self):
        from mongoengine import connection

        # Reset the connections
        connection._connection_settings = {}
        connection._connections = {}
        connection._dbs = {}

        connect(db='mongoenginetest', tz_aware=True)

        class LogEntry(Document):
            time = DateTimeField()

        LogEntry.drop_collection()

        LogEntry(time=datetime.datetime(2013, 1, 1, 0, 0, 0)).save()

        log = LogEntry.objects.first()
        log.time = datetime.datetime(2013, 1, 1, 0, 0, 0)
        self.assertEqual(['time'], log._changed_fields)

    def test_datetime(self):
        """Tests showing pymongo datetime fields handling of microseconds.
        Microseconds are rounded to the nearest millisecond and pre UTC
        handling is wonky.

        See: http://api.mongodb.org/python/current/api/bson/son.html#dt
        """
        class LogEntry(Document):
            date = DateTimeField()

        LogEntry.drop_collection()

        # Test can save dates
        log = LogEntry()
        log.date = datetime.date.today()
        log.save()
        log.reload()
        self.assertEqual(log.date.date(), datetime.date.today())

        LogEntry.drop_collection()

        # Post UTC - microseconds are rounded (down) nearest millisecond and
        # dropped
        d1 = datetime.datetime(1970, 01, 01, 00, 00, 01, 999)
        d2 = datetime.datetime(1970, 01, 01, 00, 00, 01)
        log = LogEntry()
        log.date = d1
        log.save()
        log.reload()
        self.assertNotEqual(log.date, d1)
        self.assertEqual(log.date, d2)

        # Post UTC - microseconds are rounded (down) nearest millisecond
        d1 = datetime.datetime(1970, 01, 01, 00, 00, 01, 9999)
        d2 = datetime.datetime(1970, 01, 01, 00, 00, 01, 9000)
        log.date = d1
        log.save()
        log.reload()
        self.assertNotEqual(log.date, d1)
        self.assertEqual(log.date, d2)

        if not PY3:
            # Pre UTC dates microseconds below 1000 are dropped
            # This does not seem to be true in PY3
            d1 = datetime.datetime(1969, 12, 31, 23, 59, 59, 999)
            d2 = datetime.datetime(1969, 12, 31, 23, 59, 59)
            log.date = d1
            log.save()
            log.reload()
            self.assertNotEqual(log.date, d1)
            self.assertEqual(log.date, d2)

        LogEntry.drop_collection()

    def test_datetime_usage(self):
        """Tests for regular datetime fields"""
        class LogEntry(Document):
            date = DateTimeField()

        LogEntry.drop_collection()

        d1 = datetime.datetime(1970, 01, 01, 00, 00, 01)
        log = LogEntry()
        log.date = d1
        log.validate()
        log.save()

        for query in (d1, d1.isoformat(' ')):
            log1 = LogEntry.objects.get(date=query)
            self.assertEqual(log, log1)

        if dateutil:
            log1 = LogEntry.objects.get(date=d1.isoformat('T'))
            self.assertEqual(log, log1)

        LogEntry.drop_collection()

        # create 60 log entries
        for i in xrange(1950, 2010):
            d = datetime.datetime(i, 01, 01, 00, 00, 01)
            LogEntry(date=d).save()

        self.assertEqual(LogEntry.objects.count(), 60)

        # Test ordering
        logs = LogEntry.objects.order_by("date")
        count = logs.count()
        i = 0
        while i == count - 1:
            self.assertTrue(logs[i].date <= logs[i + 1].date)
            i += 1

        logs = LogEntry.objects.order_by("-date")
        count = logs.count()
        i = 0
        while i == count - 1:
            self.assertTrue(logs[i].date >= logs[i + 1].date)
            i += 1

        # Test searching
        logs = LogEntry.objects.filter(date__gte=datetime.datetime(1980, 1, 1))
        self.assertEqual(logs.count(), 30)

        logs = LogEntry.objects.filter(date__lte=datetime.datetime(1980, 1, 1))
        self.assertEqual(logs.count(), 30)

        logs = LogEntry.objects.filter(
            date__lte=datetime.datetime(2011, 1, 1),
            date__gte=datetime.datetime(2000, 1, 1),
        )
        self.assertEqual(logs.count(), 10)

        LogEntry.drop_collection()

    def test_complexdatetime_storage(self):
        """Tests for complex datetime fields - which can handle microseconds
        without rounding.
        """
        class LogEntry(Document):
            date = ComplexDateTimeField()
            date_with_dots = ComplexDateTimeField(separator='.')

        LogEntry.drop_collection()

        # Post UTC - microseconds are rounded (down) nearest millisecond and
        # dropped - with default datetimefields
        d1 = datetime.datetime(1970, 01, 01, 00, 00, 01, 999)
        log = LogEntry()
        log.date = d1
        log.save()
        log.reload()
        self.assertEqual(log.date, d1)

        # Post UTC - microseconds are rounded (down) nearest millisecond - with
        # default datetimefields
        d1 = datetime.datetime(1970, 01, 01, 00, 00, 01, 9999)
        log.date = d1
        log.save()
        log.reload()
        self.assertEqual(log.date, d1)

        # Pre UTC dates microseconds below 1000 are dropped - with default
        # datetimefields
        d1 = datetime.datetime(1969, 12, 31, 23, 59, 59, 999)
        log.date = d1
        log.save()
        log.reload()
        self.assertEqual(log.date, d1)

        # Pre UTC microseconds above 1000 is wonky - with default datetimefields
        # log.date has an invalid microsecond value so I can't construct
        # a date to compare.
        for i in xrange(1001, 3113, 33):
            d1 = datetime.datetime(1969, 12, 31, 23, 59, 59, i)
            log.date = d1
            log.save()
            log.reload()
            self.assertEqual(log.date, d1)
            log1 = LogEntry.objects.get(date=d1)
            self.assertEqual(log, log1)

        # Test string padding
        microsecond = map(int, [math.pow(10, x) for x in xrange(6)])
        mm = dd = hh = ii = ss = [1, 10]

        for values in itertools.product([2014], mm, dd, hh, ii, ss, microsecond):
            stored = LogEntry(date=datetime.datetime(*values)).to_mongo()['date']
            self.assertTrue(re.match('^\d{4},\d{2},\d{2},\d{2},\d{2},\d{2},\d{6}$', stored) is not None)

        # Test separator
        stored = LogEntry(date_with_dots=datetime.datetime(2014, 1, 1)).to_mongo()['date_with_dots']
        self.assertTrue(re.match('^\d{4}.\d{2}.\d{2}.\d{2}.\d{2}.\d{2}.\d{6}$', stored) is not None)

        LogEntry.drop_collection()

    def test_complexdatetime_usage(self):
        """Tests for complex datetime fields - which can handle microseconds
        without rounding.
        """
        class LogEntry(Document):
            date = ComplexDateTimeField()

        LogEntry.drop_collection()

        d1 = datetime.datetime(1970, 01, 01, 00, 00, 01, 999)
        log = LogEntry()
        log.date = d1
        log.save()

        log1 = LogEntry.objects.get(date=d1)
        self.assertEqual(log, log1)

        LogEntry.drop_collection()

        # create 60 log entries
        for i in xrange(1950, 2010):
            d = datetime.datetime(i, 01, 01, 00, 00, 01, 999)
            LogEntry(date=d).save()

        self.assertEqual(LogEntry.objects.count(), 60)

        # Test ordering
        logs = LogEntry.objects.order_by("date")
        count = logs.count()
        i = 0
        while i == count - 1:
            self.assertTrue(logs[i].date <= logs[i + 1].date)
            i += 1

        logs = LogEntry.objects.order_by("-date")
        count = logs.count()
        i = 0
        while i == count - 1:
            self.assertTrue(logs[i].date >= logs[i + 1].date)
            i += 1

        # Test searching
        logs = LogEntry.objects.filter(date__gte=datetime.datetime(1980, 1, 1))
        self.assertEqual(logs.count(), 30)

        logs = LogEntry.objects.filter(date__lte=datetime.datetime(1980, 1, 1))
        self.assertEqual(logs.count(), 30)

        logs = LogEntry.objects.filter(
            date__lte=datetime.datetime(2011, 1, 1),
            date__gte=datetime.datetime(2000, 1, 1),
        )
        self.assertEqual(logs.count(), 10)

        LogEntry.drop_collection()

        # Test microsecond-level ordering/filtering
        for microsecond in (99, 999, 9999, 10000):
            LogEntry(date=datetime.datetime(2015, 1, 1, 0, 0, 0, microsecond)).save()

        logs = list(LogEntry.objects.order_by('date'))
        for next_idx, log in enumerate(logs[:-1], start=1):
            next_log = logs[next_idx]
            self.assertTrue(log.date < next_log.date)

        logs = list(LogEntry.objects.order_by('-date'))
        for next_idx, log in enumerate(logs[:-1], start=1):
            next_log = logs[next_idx]
            self.assertTrue(log.date > next_log.date)

        logs = LogEntry.objects.filter(date__lte=datetime.datetime(2015, 1, 1, 0, 0, 0, 10000))
        self.assertEqual(logs.count(), 4)

        LogEntry.drop_collection()

    def test_list_validation(self):
        """Ensure that a list field only accepts lists with valid elements.
        """
        class User(Document):
            pass

        class Comment(EmbeddedDocument):
            content = StringField()

        class BlogPost(Document):
            content = StringField()
            comments = ListField(EmbeddedDocumentField(Comment))
            tags = ListField(StringField())
            authors = ListField(ReferenceField(User))
            generic = ListField(GenericReferenceField())

        post = BlogPost(content='Went for a walk today...')
        post.validate()

        post.tags = 'fun'
        self.assertRaises(ValidationError, post.validate)
        post.tags = [1, 2]
        self.assertRaises(ValidationError, post.validate)

        post.tags = ['fun', 'leisure']
        post.validate()
        post.tags = ('fun', 'leisure')
        post.validate()

        post.comments = ['a']
        self.assertRaises(ValidationError, post.validate)
        post.comments = 'yay'
        self.assertRaises(ValidationError, post.validate)

        comments = [Comment(content='Good for you'), Comment(content='Yay.')]
        post.comments = comments
        post.validate()

        post.authors = [Comment()]
        self.assertRaises(ValidationError, post.validate)

        post.authors = [User()]
        self.assertRaises(ValidationError, post.validate)

        user = User()
        user.save()
        post.authors = [user]
        post.validate()

        post.generic = [1, 2]
        self.assertRaises(ValidationError, post.validate)

        post.generic = [User(), Comment()]
        self.assertRaises(ValidationError, post.validate)

        post.generic = [Comment()]
        self.assertRaises(ValidationError, post.validate)

        post.generic = [user]
        post.validate()

        User.drop_collection()
        BlogPost.drop_collection()

    def test_sorted_list_sorting(self):
        """Ensure that a sorted list field properly sorts values.
        """
        class Comment(EmbeddedDocument):
            order = IntField()
            content = StringField()

        class BlogPost(Document):
            content = StringField()
            comments = SortedListField(EmbeddedDocumentField(Comment),
                                       ordering='order')
            tags = SortedListField(StringField())

        post = BlogPost(content='Went for a walk today...')
        post.save()

        post.tags = ['leisure', 'fun']
        post.save()
        post.reload()
        self.assertEqual(post.tags, ['fun', 'leisure'])

        comment1 = Comment(content='Good for you', order=1)
        comment2 = Comment(content='Yay.', order=0)
        comments = [comment1, comment2]
        post.comments = comments
        post.save()
        post.reload()
        self.assertEqual(post.comments[0].content, comment2.content)
        self.assertEqual(post.comments[1].content, comment1.content)

        post.comments[0].order = 2
        post.save()
        post.reload()

        self.assertEqual(post.comments[0].content, comment1.content)
        self.assertEqual(post.comments[1].content, comment2.content)

        BlogPost.drop_collection()

    def test_reverse_list_sorting(self):
        """Ensure that a reverse sorted list field properly sorts values"""

        class Category(EmbeddedDocument):
            count = IntField()
            name = StringField()

        class CategoryList(Document):
            categories = SortedListField(EmbeddedDocumentField(Category),
                                         ordering='count', reverse=True)
            name = StringField()

        catlist = CategoryList(name="Top categories")
        cat1 = Category(name='posts', count=10)
        cat2 = Category(name='food', count=100)
        cat3 = Category(name='drink', count=40)
        catlist.categories = [cat1, cat2, cat3]
        catlist.save()
        catlist.reload()

        self.assertEqual(catlist.categories[0].name, cat2.name)
        self.assertEqual(catlist.categories[1].name, cat3.name)
        self.assertEqual(catlist.categories[2].name, cat1.name)

        CategoryList.drop_collection()

    def test_list_field(self):
        """Ensure that list types work as expected.
        """
        class BlogPost(Document):
            info = ListField()

        BlogPost.drop_collection()

        post = BlogPost()
        post.info = 'my post'
        self.assertRaises(ValidationError, post.validate)

        post.info = {'title': 'test'}
        self.assertRaises(ValidationError, post.validate)

        post.info = ['test']
        post.save()

        post = BlogPost()
        post.info = [{'test': 'test'}]
        post.save()

        post = BlogPost()
        post.info = [{'test': 3}]
        post.save()

        self.assertEqual(BlogPost.objects.count(), 3)
        self.assertEqual(
            BlogPost.objects.filter(info__exact='test').count(), 1)
        self.assertEqual(
            BlogPost.objects.filter(info__0__test='test').count(), 1)

        # Confirm handles non strings or non existing keys
        self.assertEqual(
            BlogPost.objects.filter(info__0__test__exact='5').count(), 0)
        self.assertEqual(
            BlogPost.objects.filter(info__100__test__exact='test').count(), 0)

        post = BlogPost()
        post.info = ['1', '2']
        post.save()
        post = BlogPost.objects(info=['1', '2']).get()
        post.info += ['3', '4']
        post.save()
        self.assertEqual(BlogPost.objects(info=['1', '2', '3', '4']).count(), 1)
        post = BlogPost.objects(info=['1', '2', '3', '4']).get()
        post.info *= 2
        post.save()
        self.assertEqual(BlogPost.objects(info=['1', '2', '3', '4', '1', '2', '3', '4']).count(), 1)
        BlogPost.drop_collection()

    def test_list_field_passed_in_value(self):
        class Foo(Document):
            bars = ListField(ReferenceField("Bar"))

        class Bar(Document):
            text = StringField()

        bar = Bar(text="hi")
        bar.save()

        foo = Foo(bars=[])
        foo.bars.append(bar)
        self.assertEqual(repr(foo.bars), '[<Bar: Bar object>]')

    def test_list_field_strict(self):
        """Ensure that list field handles validation if provided a strict field type."""

        class Simple(Document):
            mapping = ListField(field=IntField())

        Simple.drop_collection()

        e = Simple()
        e.mapping = [1]
        e.save()

        def create_invalid_mapping():
            e.mapping = ["abc"]
            e.save()

        self.assertRaises(ValidationError, create_invalid_mapping)

        Simple.drop_collection()

    def test_list_field_rejects_strings(self):
        """Strings aren't valid list field data types"""

        class Simple(Document):
            mapping = ListField()

        Simple.drop_collection()
        e = Simple()
        e.mapping = 'hello world'

        self.assertRaises(ValidationError, e.save)

    def test_complex_field_required(self):
        """Ensure required cant be None / Empty"""

        class Simple(Document):
            mapping = ListField(required=True)

        Simple.drop_collection()
        e = Simple()
        e.mapping = []

        self.assertRaises(ValidationError, e.save)

        class Simple(Document):
            mapping = DictField(required=True)

        Simple.drop_collection()
        e = Simple()
        e.mapping = {}

        self.assertRaises(ValidationError, e.save)

    def test_complex_field_same_value_not_changed(self):
        """
        If a complex field is set to the same value, it should not be marked as
        changed.
        """
        class Simple(Document):
            mapping = ListField()

        Simple.drop_collection()
        e = Simple().save()
        e.mapping = []
        self.assertEqual([], e._changed_fields)

        class Simple(Document):
            mapping = DictField()

        Simple.drop_collection()
        e = Simple().save()
        e.mapping = {}
        self.assertEqual([], e._changed_fields)

    def test_slice_marks_field_as_changed(self):

        class Simple(Document):
            widgets = ListField()

        simple = Simple(widgets=[1, 2, 3, 4]).save()
        simple.widgets[:3] = []
        self.assertEqual(['widgets'], simple._changed_fields)
        simple.save()

        simple = simple.reload()
        self.assertEqual(simple.widgets, [4])

    def test_del_slice_marks_field_as_changed(self):

        class Simple(Document):
            widgets = ListField()

        simple = Simple(widgets=[1, 2, 3, 4]).save()
        del simple.widgets[:3]
        self.assertEqual(['widgets'], simple._changed_fields)
        simple.save()

        simple = simple.reload()
        self.assertEqual(simple.widgets, [4])

    def test_list_field_with_negative_indices(self):
        
        class Simple(Document):
            widgets = ListField()

        simple = Simple(widgets=[1, 2, 3, 4]).save()
        simple.widgets[-1] = 5
        self.assertEqual(['widgets.3'], simple._changed_fields)
        simple.save()

        simple = simple.reload()
        self.assertEqual(simple.widgets, [1, 2, 3, 5])

    def test_list_field_complex(self):
        """Ensure that the list fields can handle the complex types."""

        class SettingBase(EmbeddedDocument):
            meta = {'allow_inheritance': True}

        class StringSetting(SettingBase):
            value = StringField()

        class IntegerSetting(SettingBase):
            value = IntField()

        class Simple(Document):
            mapping = ListField()

        Simple.drop_collection()
        e = Simple()
        e.mapping.append(StringSetting(value='foo'))
        e.mapping.append(IntegerSetting(value=42))
        e.mapping.append({'number': 1, 'string': 'Hi!', 'float': 1.001,
                          'complex': IntegerSetting(value=42),
                          'list': [IntegerSetting(value=42),
                                   StringSetting(value='foo')]})
        e.save()

        e2 = Simple.objects.get(id=e.id)
        self.assertTrue(isinstance(e2.mapping[0], StringSetting))
        self.assertTrue(isinstance(e2.mapping[1], IntegerSetting))

        # Test querying
        self.assertEqual(
            Simple.objects.filter(mapping__1__value=42).count(), 1)
        self.assertEqual(
            Simple.objects.filter(mapping__2__number=1).count(), 1)
        self.assertEqual(
            Simple.objects.filter(mapping__2__complex__value=42).count(), 1)
        self.assertEqual(
            Simple.objects.filter(mapping__2__list__0__value=42).count(), 1)
        self.assertEqual(
            Simple.objects.filter(mapping__2__list__1__value='foo').count(), 1)

        # Confirm can update
        Simple.objects().update(set__mapping__1=IntegerSetting(value=10))
        self.assertEqual(
            Simple.objects.filter(mapping__1__value=10).count(), 1)

        Simple.objects().update(
            set__mapping__2__list__1=StringSetting(value='Boo'))
        self.assertEqual(
            Simple.objects.filter(mapping__2__list__1__value='foo').count(), 0)
        self.assertEqual(
            Simple.objects.filter(mapping__2__list__1__value='Boo').count(), 1)

        Simple.drop_collection()

    def test_dict_field(self):
        """Ensure that dict types work as expected.
        """
        class BlogPost(Document):
            info = DictField()

        BlogPost.drop_collection()

        post = BlogPost()
        post.info = 'my post'
        self.assertRaises(ValidationError, post.validate)

        post.info = ['test', 'test']
        self.assertRaises(ValidationError, post.validate)

        post.info = {'$title': 'test'}
        self.assertRaises(ValidationError, post.validate)

        post.info = {'nested': {'$title': 'test'}}
        self.assertRaises(ValidationError, post.validate)

        post.info = {'the.title': 'test'}
        self.assertRaises(ValidationError, post.validate)

        post.info = {'nested': {'the.title': 'test'}}
        self.assertRaises(ValidationError, post.validate)

        post.info = {1: 'test'}
        self.assertRaises(ValidationError, post.validate)

        post.info = {'title': 'test'}
        post.save()

        post = BlogPost()
        post.info = {'details': {'test': 'test'}}
        post.save()

        post = BlogPost()
        post.info = {'details': {'test': 3}}
        post.save()

        self.assertEqual(BlogPost.objects.count(), 3)
        self.assertEqual(
            BlogPost.objects.filter(info__title__exact='test').count(), 1)
        self.assertEqual(
            BlogPost.objects.filter(info__details__test__exact='test').count(), 1)

        # Confirm handles non strings or non existing keys
        self.assertEqual(
            BlogPost.objects.filter(info__details__test__exact=5).count(), 0)
        self.assertEqual(
            BlogPost.objects.filter(info__made_up__test__exact='test').count(), 0)

        post = BlogPost.objects.create(info={'title': 'original'})
        post.info.update({'title': 'updated'})
        post.save()
        post.reload()
        self.assertEqual('updated', post.info['title'])

        post.info.setdefault('authors', [])
        post.save()
        post.reload()
        self.assertEqual([], post.info['authors'])

        BlogPost.drop_collection()

    def test_dictfield_dump_document(self):
        """Ensure a DictField can handle another document's dump
        """
        class Doc(Document):
            field = DictField()

        class ToEmbed(Document):
            id = IntField(primary_key=True, default=1)
            recursive = DictField()

        class ToEmbedParent(Document):
            id = IntField(primary_key=True, default=1)
            recursive = DictField()

            meta = {'allow_inheritance': True}

        class ToEmbedChild(ToEmbedParent):
            pass

        to_embed_recursive = ToEmbed(id=1).save()
        to_embed = ToEmbed(
            id=2, recursive=to_embed_recursive.to_mongo().to_dict()).save()
        doc = Doc(field=to_embed.to_mongo().to_dict())
        doc.save()
        assert isinstance(doc.field, dict)
        assert doc.field == {'_id': 2, 'recursive': {'_id': 1, 'recursive': {}}}
        # Same thing with a Document with a _cls field
        to_embed_recursive = ToEmbedChild(id=1).save()
        to_embed_child = ToEmbedChild(
            id=2, recursive=to_embed_recursive.to_mongo().to_dict()).save()
        doc = Doc(field=to_embed_child.to_mongo().to_dict())
        doc.save()
        assert isinstance(doc.field, dict)
        assert doc.field == {
            '_id': 2, '_cls': 'ToEmbedParent.ToEmbedChild',
            'recursive': {'_id': 1, '_cls': 'ToEmbedParent.ToEmbedChild', 'recursive': {}}
        }

    def test_dictfield_strict(self):
        """Ensure that dict field handles validation if provided a strict field type."""

        class Simple(Document):
            mapping = DictField(field=IntField())

        Simple.drop_collection()

        e = Simple()
        e.mapping['someint'] = 1
        e.save()

        def create_invalid_mapping():
            e.mapping['somestring'] = "abc"
            e.save()

        self.assertRaises(ValidationError, create_invalid_mapping)

        Simple.drop_collection()

    def test_dictfield_complex(self):
        """Ensure that the dict field can handle the complex types."""

        class SettingBase(EmbeddedDocument):
            meta = {'allow_inheritance': True}

        class StringSetting(SettingBase):
            value = StringField()

        class IntegerSetting(SettingBase):
            value = IntField()

        class Simple(Document):
            mapping = DictField()

        Simple.drop_collection()
        e = Simple()
        e.mapping['somestring'] = StringSetting(value='foo')
        e.mapping['someint'] = IntegerSetting(value=42)
        e.mapping['nested_dict'] = {'number': 1, 'string': 'Hi!',
                                    'float': 1.001,
                                    'complex': IntegerSetting(value=42),
                                    'list': [IntegerSetting(value=42),
                                             StringSetting(value='foo')]}
        e.save()

        e2 = Simple.objects.get(id=e.id)
        self.assertTrue(isinstance(e2.mapping['somestring'], StringSetting))
        self.assertTrue(isinstance(e2.mapping['someint'], IntegerSetting))

        # Test querying
        self.assertEqual(
            Simple.objects.filter(mapping__someint__value=42).count(), 1)
        self.assertEqual(
            Simple.objects.filter(mapping__nested_dict__number=1).count(), 1)
        self.assertEqual(
            Simple.objects.filter(mapping__nested_dict__complex__value=42).count(), 1)
        self.assertEqual(
            Simple.objects.filter(mapping__nested_dict__list__0__value=42).count(), 1)
        self.assertEqual(
            Simple.objects.filter(mapping__nested_dict__list__1__value='foo').count(), 1)

        # Confirm can update
        Simple.objects().update(
            set__mapping={"someint": IntegerSetting(value=10)})
        Simple.objects().update(
            set__mapping__nested_dict__list__1=StringSetting(value='Boo'))
        self.assertEqual(
            Simple.objects.filter(mapping__nested_dict__list__1__value='foo').count(), 0)
        self.assertEqual(
            Simple.objects.filter(mapping__nested_dict__list__1__value='Boo').count(), 1)

        Simple.drop_collection()

    def test_atomic_update_dict_field(self):
        """Ensure that the entire DictField can be atomically updated."""

        class Simple(Document):
            mapping = DictField(field=ListField(IntField(required=True)))

        Simple.drop_collection()

        e = Simple()
        e.mapping['someints'] = [1, 2]
        e.save()
        e.update(set__mapping={"ints": [3, 4]})
        e.reload()
        self.assertEqual(BaseDict, type(e.mapping))
        self.assertEqual({"ints": [3, 4]}, e.mapping)

        def create_invalid_mapping():
            e.update(set__mapping={"somestrings": ["foo", "bar", ]})

        self.assertRaises(ValueError, create_invalid_mapping)

        Simple.drop_collection()

    def test_mapfield(self):
        """Ensure that the MapField handles the declared type."""

        class Simple(Document):
            mapping = MapField(IntField())

        Simple.drop_collection()

        e = Simple()
        e.mapping['someint'] = 1
        e.save()

        def create_invalid_mapping():
            e.mapping['somestring'] = "abc"
            e.save()

        self.assertRaises(ValidationError, create_invalid_mapping)

        def create_invalid_class():
            class NoDeclaredType(Document):
                mapping = MapField()

        self.assertRaises(ValidationError, create_invalid_class)

        Simple.drop_collection()

    def test_complex_mapfield(self):
        """Ensure that the MapField can handle complex declared types."""

        class SettingBase(EmbeddedDocument):
            meta = {"allow_inheritance": True}

        class StringSetting(SettingBase):
            value = StringField()

        class IntegerSetting(SettingBase):
            value = IntField()

        class Extensible(Document):
            mapping = MapField(EmbeddedDocumentField(SettingBase))

        Extensible.drop_collection()

        e = Extensible()
        e.mapping['somestring'] = StringSetting(value='foo')
        e.mapping['someint'] = IntegerSetting(value=42)
        e.save()

        e2 = Extensible.objects.get(id=e.id)
        self.assertTrue(isinstance(e2.mapping['somestring'], StringSetting))
        self.assertTrue(isinstance(e2.mapping['someint'], IntegerSetting))

        def create_invalid_mapping():
            e.mapping['someint'] = 123
            e.save()

        self.assertRaises(ValidationError, create_invalid_mapping)

        Extensible.drop_collection()

    def test_embedded_mapfield_db_field(self):

        class Embedded(EmbeddedDocument):
            number = IntField(default=0, db_field='i')

        class Test(Document):
            my_map = MapField(field=EmbeddedDocumentField(Embedded),
                              db_field='x')

        Test.drop_collection()

        test = Test()
        test.my_map['DICTIONARY_KEY'] = Embedded(number=1)
        test.save()

        Test.objects.update_one(inc__my_map__DICTIONARY_KEY__number=1)

        test = Test.objects.get()
        self.assertEqual(test.my_map['DICTIONARY_KEY'].number, 2)
        doc = self.db.test.find_one()
        self.assertEqual(doc['x']['DICTIONARY_KEY']['i'], 2)

    def test_mapfield_numerical_index(self):
        """Ensure that MapField accept numeric strings as indexes."""
        class Embedded(EmbeddedDocument):
            name = StringField()

        class Test(Document):
            my_map = MapField(EmbeddedDocumentField(Embedded))

        Test.drop_collection()

        test = Test()
        test.my_map['1'] = Embedded(name='test')
        test.save()
        test.my_map['1'].name = 'test updated'
        test.save()

        Test.drop_collection()

    def test_map_field_lookup(self):
        """Ensure MapField lookups succeed on Fields without a lookup method"""

        class Action(EmbeddedDocument):
            operation = StringField()
            object = StringField()

        class Log(Document):
            name = StringField()
            visited = MapField(DateTimeField())
            actions = MapField(EmbeddedDocumentField(Action))

        Log.drop_collection()
        Log(name="wilson", visited={'friends': datetime.datetime.now()},
            actions={'friends': Action(operation='drink', object='beer')}).save()

        self.assertEqual(1, Log.objects(
            visited__friends__exists=True).count())

        self.assertEqual(1, Log.objects(
            actions__friends__operation='drink',
            actions__friends__object='beer').count())

    def test_map_field_unicode(self):

        class Info(EmbeddedDocument):
            description = StringField()
            value_list = ListField(field=StringField())

        class BlogPost(Document):
            info_dict = MapField(field=EmbeddedDocumentField(Info))

        BlogPost.drop_collection()

        tree = BlogPost(info_dict={
            u"éééé": {
                'description': u"VALUE: éééé"
            }
        })

        tree.save()

        self.assertEqual(BlogPost.objects.get(id=tree.id).info_dict[u"éééé"].description, u"VALUE: éééé")

        BlogPost.drop_collection()

    def test_embedded_db_field(self):

        class Embedded(EmbeddedDocument):
            number = IntField(default=0, db_field='i')

        class Test(Document):
            embedded = EmbeddedDocumentField(Embedded, db_field='x')

        Test.drop_collection()

        test = Test()
        test.embedded = Embedded(number=1)
        test.save()

        Test.objects.update_one(inc__embedded__number=1)

        test = Test.objects.get()
        self.assertEqual(test.embedded.number, 2)
        doc = self.db.test.find_one()
        self.assertEqual(doc['x']['i'], 2)

    def test_embedded_document_validation(self):
        """Ensure that invalid embedded documents cannot be assigned to
        embedded document fields.
        """
        class Comment(EmbeddedDocument):
            content = StringField()

        class PersonPreferences(EmbeddedDocument):
            food = StringField(required=True)
            number = IntField()

        class Person(Document):
            name = StringField()
            preferences = EmbeddedDocumentField(PersonPreferences)

        Person.drop_collection()

        person = Person(name='Test User')
        person.preferences = 'My Preferences'
        self.assertRaises(ValidationError, person.validate)

        # Check that only the right embedded doc works
        person.preferences = Comment(content='Nice blog post...')
        self.assertRaises(ValidationError, person.validate)

        # Check that the embedded doc is valid
        person.preferences = PersonPreferences()
        self.assertRaises(ValidationError, person.validate)

        person.preferences = PersonPreferences(food='Cheese', number=47)
        self.assertEqual(person.preferences.food, 'Cheese')
        person.validate()

    def test_embedded_document_inheritance(self):
        """Ensure that subclasses of embedded documents may be provided to
        EmbeddedDocumentFields of the superclass' type.
        """
        class User(EmbeddedDocument):
            name = StringField()

            meta = {'allow_inheritance': True}

        class PowerUser(User):
            power = IntField()

        class BlogPost(Document):
            content = StringField()
            author = EmbeddedDocumentField(User)

        BlogPost.drop_collection()

        post = BlogPost(content='What I did today...')
        post.author = PowerUser(name='Test User', power=47)
        post.save()

        self.assertEqual(47, BlogPost.objects.first().author.power)

    def test_embedded_document_inheritance_with_list(self):
        """Ensure that nested list of subclassed embedded documents is
        handled correctly.
        """

        class Group(EmbeddedDocument):
            name = StringField()
            content = ListField(StringField())

        class Basedoc(Document):
            groups = ListField(EmbeddedDocumentField(Group))
            meta = {'abstract': True}

        class User(Basedoc):
            doctype = StringField(require=True, default='userdata')

        User.drop_collection()

        content = ['la', 'le', 'lu']
        group = Group(name='foo', content=content)
        foobar = User(groups=[group])
        foobar.save()

        self.assertEqual(content, User.objects.first().groups[0].content)

    def test_reference_validation(self):
        """Ensure that invalid docment objects cannot be assigned to reference
        fields.
        """
        class User(Document):
            name = StringField()

        class BlogPost(Document):
            content = StringField()
            author = ReferenceField(User)

        User.drop_collection()
        BlogPost.drop_collection()

        self.assertRaises(ValidationError, ReferenceField, EmbeddedDocument)

        user = User(name='Test User')

        # Ensure that the referenced object must have been saved
        post1 = BlogPost(content='Chips and gravy taste good.')
        post1.author = user
        self.assertRaises(ValidationError, post1.save)

        # Check that an invalid object type cannot be used
        post2 = BlogPost(content='Chips and chilli taste good.')
        post1.author = post2
        self.assertRaises(ValidationError, post1.validate)

        user.save()
        post1.author = user
        post1.save()

        post2.save()
        post1.author = post2
        self.assertRaises(ValidationError, post1.validate)

        User.drop_collection()
        BlogPost.drop_collection()

    def test_dbref_reference_fields(self):

        class Person(Document):
            name = StringField()
            parent = ReferenceField('self', dbref=True)

        Person.drop_collection()

        p1 = Person(name="John").save()
        Person(name="Ross", parent=p1).save()

        col = Person._get_collection()
        data = col.find_one({'name': 'Ross'})
        self.assertEqual(data['parent'], DBRef('person', p1.pk))

        p = Person.objects.get(name="Ross")
        self.assertEqual(p.parent, p1)

    def test_dbref_to_mongo(self):
        class Person(Document):
            name = StringField()
            parent = ReferenceField('self', dbref=False)

        p1 = Person._from_son({'name': "Yakxxx",
                               'parent': "50a234ea469ac1eda42d347d"})
        mongoed = p1.to_mongo()
        self.assertTrue(isinstance(mongoed['parent'], ObjectId))
        
    def test_cached_reference_field_get_and_save(self):
        """
        Tests #1047: CachedReferenceField creates DBRefs on to_python, but can't save them on to_mongo
        """
        class Animal(Document):
            name = StringField()
            tag = StringField()

        class Ocorrence(Document):
            person = StringField()
            animal = CachedReferenceField(Animal)
        
        Animal.drop_collection()
        Ocorrence.drop_collection()
        
        Ocorrence(person="testte", 
                  animal=Animal(name="Leopard", tag="heavy").save()).save()
        p = Ocorrence.objects.get()
        p.person = 'new_testte'
        p.save()

    def test_cached_reference_fields(self):
        class Animal(Document):
            name = StringField()
            tag = StringField()

        class Ocorrence(Document):
            person = StringField()
            animal = CachedReferenceField(
                Animal, fields=['tag'])

        Animal.drop_collection()
        Ocorrence.drop_collection()

        a = Animal(name="Leopard", tag="heavy")
        a.save()

        self.assertEqual(Animal._cached_reference_fields, [Ocorrence.animal])
        o = Ocorrence(person="teste", animal=a)
        o.save()

        p = Ocorrence(person="Wilson")
        p.save()

        self.assertEqual(Ocorrence.objects(animal=None).count(), 1)

        self.assertEqual(
            a.to_mongo(fields=['tag']), {'tag': 'heavy', "_id": a.pk})

        self.assertEqual(o.to_mongo()['animal']['tag'], 'heavy')

        # counts
        Ocorrence(person="teste 2").save()
        Ocorrence(person="teste 3").save()

        count = Ocorrence.objects(animal__tag='heavy').count()
        self.assertEqual(count, 1)

        ocorrence = Ocorrence.objects(animal__tag='heavy').first()
        self.assertEqual(ocorrence.person, "teste")
        self.assertTrue(isinstance(ocorrence.animal, Animal))

    def test_cached_reference_field_decimal(self):
        class PersonAuto(Document):
            name = StringField()
            salary = DecimalField()

        class SocialTest(Document):
            group = StringField()
            person = CachedReferenceField(
                PersonAuto,
                fields=('salary',))

        PersonAuto.drop_collection()
        SocialTest.drop_collection()

        p = PersonAuto(name="Alberto", salary=Decimal('7000.00'))
        p.save()

        s = SocialTest(group="dev", person=p)
        s.save()

        self.assertEqual(
            SocialTest.objects._collection.find_one({'person.salary': 7000.00}), {
                '_id': s.pk,
                'group': s.group,
                'person': {
                    '_id': p.pk,
                    'salary': 7000.00
                }
            })

    def test_cached_reference_field_reference(self):
        class Group(Document):
            name = StringField()

        class Person(Document):
            name = StringField()
            group = ReferenceField(Group)

        class SocialData(Document):
            obs = StringField()
            tags = ListField(
                StringField())
            person = CachedReferenceField(
                Person,
                fields=('group',))

        Group.drop_collection()
        Person.drop_collection()
        SocialData.drop_collection()

        g1 = Group(name='dev')
        g1.save()

        g2 = Group(name="designers")
        g2.save()

        p1 = Person(name="Alberto", group=g1)
        p1.save()

        p2 = Person(name="Andre", group=g1)
        p2.save()

        p3 = Person(name="Afro design", group=g2)
        p3.save()

        s1 = SocialData(obs="testing 123", person=p1, tags=['tag1', 'tag2'])
        s1.save()

        s2 = SocialData(obs="testing 321", person=p3, tags=['tag3', 'tag4'])
        s2.save()

        self.assertEqual(SocialData.objects._collection.find_one(
            {'tags': 'tag2'}), {
                '_id': s1.pk,
                'obs': 'testing 123',
                'tags': ['tag1', 'tag2'],
                'person': {
                    '_id': p1.pk,
                    'group': g1.pk
                }
        })

        self.assertEqual(SocialData.objects(person__group=g2).count(), 1)
        self.assertEqual(SocialData.objects(person__group=g2).first(), s2)

    def test_cached_reference_field_update_all(self):
        class Person(Document):
            TYPES = (
                ('pf', "PF"),
                ('pj', "PJ")
            )
            name = StringField()
            tp = StringField(
                choices=TYPES
            )

            father = CachedReferenceField('self', fields=('tp',))

        Person.drop_collection()

        a1 = Person(name="Wilson Father", tp="pj")
        a1.save()

        a2 = Person(name='Wilson Junior', tp='pf', father=a1)
        a2.save()

        self.assertEqual(dict(a2.to_mongo()), {
            "_id": a2.pk,
            "name": u"Wilson Junior",
            "tp": u"pf",
            "father": {
                "_id": a1.pk,
                "tp": u"pj"
            }
        })

        self.assertEqual(Person.objects(father=a1)._query, {
            'father._id': a1.pk
        })
        self.assertEqual(Person.objects(father=a1).count(), 1)

        Person.objects.update(set__tp="pf")
        Person.father.sync_all()

        a2.reload()
        self.assertEqual(dict(a2.to_mongo()), {
            "_id": a2.pk,
            "name": u"Wilson Junior",
            "tp": u"pf",
            "father": {
                "_id": a1.pk,
                "tp": u"pf"
            }
        })

    def test_cached_reference_fields_on_embedded_documents(self):
        def build():
            class Test(Document):
                name = StringField()

            type('WrongEmbeddedDocument', (
                EmbeddedDocument,), {
                    'test': CachedReferenceField(Test)
            })

        self.assertRaises(InvalidDocumentError, build)

    def test_cached_reference_auto_sync(self):
        class Person(Document):
            TYPES = (
                ('pf', "PF"),
                ('pj', "PJ")
            )
            name = StringField()
            tp = StringField(
                choices=TYPES
            )

            father = CachedReferenceField('self', fields=('tp',))

        Person.drop_collection()

        a1 = Person(name="Wilson Father", tp="pj")
        a1.save()

        a2 = Person(name='Wilson Junior', tp='pf', father=a1)
        a2.save()

        a1.tp = 'pf'
        a1.save()

        a2.reload()
        self.assertEqual(dict(a2.to_mongo()), {
            '_id': a2.pk,
            'name': 'Wilson Junior',
            'tp': 'pf',
            'father': {
                '_id': a1.pk,
                'tp': 'pf'
            }
        })

    def test_cached_reference_auto_sync_disabled(self):
        class Persone(Document):
            TYPES = (
                ('pf', "PF"),
                ('pj', "PJ")
            )
            name = StringField()
            tp = StringField(
                choices=TYPES
            )

            father = CachedReferenceField(
                'self', fields=('tp',), auto_sync=False)

        Persone.drop_collection()

        a1 = Persone(name="Wilson Father", tp="pj")
        a1.save()

        a2 = Persone(name='Wilson Junior', tp='pf', father=a1)
        a2.save()

        a1.tp = 'pf'
        a1.save()

        self.assertEqual(Persone.objects._collection.find_one({'_id': a2.pk}), {
            '_id': a2.pk,
            'name': 'Wilson Junior',
            'tp': 'pf',
            'father': {
                '_id': a1.pk,
                'tp': 'pj'
            }
        })

    def test_cached_reference_embedded_fields(self):
        class Owner(EmbeddedDocument):
            TPS = (
                ('n', "Normal"),
                ('u', "Urgent")
            )
            name = StringField()
            tp = StringField(
                verbose_name="Type",
                db_field="t",
                choices=TPS)

        class Animal(Document):
            name = StringField()
            tag = StringField()

            owner = EmbeddedDocumentField(Owner)

        class Ocorrence(Document):
            person = StringField()
            animal = CachedReferenceField(
                Animal, fields=['tag', 'owner.tp'])

        Animal.drop_collection()
        Ocorrence.drop_collection()

        a = Animal(name="Leopard", tag="heavy",
                   owner=Owner(tp='u', name="Wilson Júnior")
                   )
        a.save()

        o = Ocorrence(person="teste", animal=a)
        o.save()
        self.assertEqual(dict(a.to_mongo(fields=['tag', 'owner.tp'])), {
            '_id': a.pk,
            'tag': 'heavy',
            'owner': {
                't': 'u'
            }
        })
        self.assertEqual(o.to_mongo()['animal']['tag'], 'heavy')
        self.assertEqual(o.to_mongo()['animal']['owner']['t'], 'u')

        # counts
        Ocorrence(person="teste 2").save()
        Ocorrence(person="teste 3").save()

        count = Ocorrence.objects(
            animal__tag='heavy', animal__owner__tp='u').count()
        self.assertEqual(count, 1)

        ocorrence = Ocorrence.objects(
            animal__tag='heavy',
            animal__owner__tp='u').first()
        self.assertEqual(ocorrence.person, "teste")
        self.assertTrue(isinstance(ocorrence.animal, Animal))

    def test_cached_reference_embedded_list_fields(self):
        class Owner(EmbeddedDocument):
            name = StringField()
            tags = ListField(StringField())

        class Animal(Document):
            name = StringField()
            tag = StringField()

            owner = EmbeddedDocumentField(Owner)

        class Ocorrence(Document):
            person = StringField()
            animal = CachedReferenceField(
                Animal, fields=['tag', 'owner.tags'])

        Animal.drop_collection()
        Ocorrence.drop_collection()

        a = Animal(name="Leopard", tag="heavy",
                   owner=Owner(tags=['cool', 'funny'],
                               name="Wilson Júnior")
                   )
        a.save()

        o = Ocorrence(person="teste 2", animal=a)
        o.save()
        self.assertEqual(dict(a.to_mongo(fields=['tag', 'owner.tags'])), {
            '_id': a.pk,
            'tag': 'heavy',
            'owner': {
                'tags': ['cool', 'funny']
            }
        })

        self.assertEqual(o.to_mongo()['animal']['tag'], 'heavy')
        self.assertEqual(o.to_mongo()['animal']['owner']['tags'],
                         ['cool', 'funny'])

        # counts
        Ocorrence(person="teste 2").save()
        Ocorrence(person="teste 3").save()

        query = Ocorrence.objects(
            animal__tag='heavy', animal__owner__tags='cool')._query
        self.assertEqual(
            query, {'animal.owner.tags': 'cool', 'animal.tag': 'heavy'})

        ocorrence = Ocorrence.objects(
            animal__tag='heavy',
            animal__owner__tags='cool').first()
        self.assertEqual(ocorrence.person, "teste 2")
        self.assertTrue(isinstance(ocorrence.animal, Animal))

    def test_objectid_reference_fields(self):

        class Person(Document):
            name = StringField()
            parent = ReferenceField('self', dbref=False)

        Person.drop_collection()

        p1 = Person(name="John").save()
        Person(name="Ross", parent=p1).save()

        col = Person._get_collection()
        data = col.find_one({'name': 'Ross'})
        self.assertEqual(data['parent'], p1.pk)

        p = Person.objects.get(name="Ross")
        self.assertEqual(p.parent, p1)

    def test_list_item_dereference(self):
        """Ensure that DBRef items in ListFields are dereferenced.
        """
        class User(Document):
            name = StringField()

        class Group(Document):
            members = ListField(ReferenceField(User))

        User.drop_collection()
        Group.drop_collection()

        user1 = User(name='user1')
        user1.save()
        user2 = User(name='user2')
        user2.save()

        group = Group(members=[user1, user2])
        group.save()

        group_obj = Group.objects.first()

        self.assertEqual(group_obj.members[0].name, user1.name)
        self.assertEqual(group_obj.members[1].name, user2.name)

        User.drop_collection()
        Group.drop_collection()

    def test_recursive_reference(self):
        """Ensure that ReferenceFields can reference their own documents.
        """
        class Employee(Document):
            name = StringField()
            boss = ReferenceField('self')
            friends = ListField(ReferenceField('self'))

        Employee.drop_collection()
        bill = Employee(name='Bill Lumbergh')
        bill.save()

        michael = Employee(name='Michael Bolton')
        michael.save()

        samir = Employee(name='Samir Nagheenanajar')
        samir.save()

        friends = [michael, samir]
        peter = Employee(name='Peter Gibbons', boss=bill, friends=friends)
        peter.save()

        peter = Employee.objects.with_id(peter.id)
        self.assertEqual(peter.boss, bill)
        self.assertEqual(peter.friends, friends)

    def test_recursive_embedding(self):
        """Ensure that EmbeddedDocumentFields can contain their own documents.
        """
        class TreeNode(EmbeddedDocument):
            name = StringField()
            children = ListField(EmbeddedDocumentField('self'))

        class Tree(Document):
            name = StringField()
            children = ListField(EmbeddedDocumentField('TreeNode'))

        Tree.drop_collection()
        tree = Tree(name="Tree")

        first_child = TreeNode(name="Child 1")
        tree.children.append(first_child)

        second_child = TreeNode(name="Child 2")
        first_child.children.append(second_child)
        tree.save()

        tree = Tree.objects.first()
        self.assertEqual(len(tree.children), 1)

        self.assertEqual(len(tree.children[0].children), 1)

        third_child = TreeNode(name="Child 3")
        tree.children[0].children.append(third_child)
        tree.save()

        self.assertEqual(len(tree.children), 1)
        self.assertEqual(tree.children[0].name, first_child.name)
        self.assertEqual(tree.children[0].children[0].name, second_child.name)
        self.assertEqual(tree.children[0].children[1].name, third_child.name)

        # Test updating
        tree.children[0].name = 'I am Child 1'
        tree.children[0].children[0].name = 'I am Child 2'
        tree.children[0].children[1].name = 'I am Child 3'
        tree.save()

        self.assertEqual(tree.children[0].name, 'I am Child 1')
        self.assertEqual(tree.children[0].children[0].name, 'I am Child 2')
        self.assertEqual(tree.children[0].children[1].name, 'I am Child 3')

        # Test removal
        self.assertEqual(len(tree.children[0].children), 2)
        del(tree.children[0].children[1])

        tree.save()
        self.assertEqual(len(tree.children[0].children), 1)

        tree.children[0].children.pop(0)
        tree.save()
        self.assertEqual(len(tree.children[0].children), 0)
        self.assertEqual(tree.children[0].children, [])

        tree.children[0].children.insert(0, third_child)
        tree.children[0].children.insert(0, second_child)
        tree.save()
        self.assertEqual(len(tree.children[0].children), 2)
        self.assertEqual(tree.children[0].children[0].name, second_child.name)
        self.assertEqual(tree.children[0].children[1].name, third_child.name)

    def test_undefined_reference(self):
        """Ensure that ReferenceFields may reference undefined Documents.
        """
        class Product(Document):
            name = StringField()
            company = ReferenceField('Company')

        class Company(Document):
            name = StringField()

        Product.drop_collection()
        Company.drop_collection()

        ten_gen = Company(name='10gen')
        ten_gen.save()
        mongodb = Product(name='MongoDB', company=ten_gen)
        mongodb.save()

        me = Product(name='MongoEngine')
        me.save()

        obj = Product.objects(company=ten_gen).first()
        self.assertEqual(obj, mongodb)
        self.assertEqual(obj.company, ten_gen)

        obj = Product.objects(company=None).first()
        self.assertEqual(obj, me)

        obj = Product.objects.get(company=None)
        self.assertEqual(obj, me)

    def test_reference_query_conversion(self):
        """Ensure that ReferenceFields can be queried using objects and values
        of the type of the primary key of the referenced object.
        """
        class Member(Document):
            user_num = IntField(primary_key=True)

        class BlogPost(Document):
            title = StringField()
            author = ReferenceField(Member, dbref=False)

        Member.drop_collection()
        BlogPost.drop_collection()

        m1 = Member(user_num=1)
        m1.save()
        m2 = Member(user_num=2)
        m2.save()

        post1 = BlogPost(title='post 1', author=m1)
        post1.save()

        post2 = BlogPost(title='post 2', author=m2)
        post2.save()

        post = BlogPost.objects(author=m1).first()
        self.assertEqual(post.id, post1.id)

        post = BlogPost.objects(author=m2).first()
        self.assertEqual(post.id, post2.id)

        Member.drop_collection()
        BlogPost.drop_collection()

    def test_reference_query_conversion_dbref(self):
        """Ensure that ReferenceFields can be queried using objects and values
        of the type of the primary key of the referenced object.
        """
        class Member(Document):
            user_num = IntField(primary_key=True)

        class BlogPost(Document):
            title = StringField()
            author = ReferenceField(Member, dbref=True)

        Member.drop_collection()
        BlogPost.drop_collection()

        m1 = Member(user_num=1)
        m1.save()
        m2 = Member(user_num=2)
        m2.save()

        post1 = BlogPost(title='post 1', author=m1)
        post1.save()

        post2 = BlogPost(title='post 2', author=m2)
        post2.save()

        post = BlogPost.objects(author=m1).first()
        self.assertEqual(post.id, post1.id)

        post = BlogPost.objects(author=m2).first()
        self.assertEqual(post.id, post2.id)

        Member.drop_collection()
        BlogPost.drop_collection()

    def test_drop_abstract_document(self):
        """Ensure that an abstract document cannot be dropped given it
        has no underlying collection.
        """
        class AbstractDoc(Document):
            name = StringField()
            meta = {"abstract": True}

        self.assertRaises(OperationError, AbstractDoc.drop_collection)

    def test_reference_class_with_abstract_parent(self):
        """Ensure that a class with an abstract parent can be referenced.
        """
        class Sibling(Document):
            name = StringField()
            meta = {"abstract": True}

        class Sister(Sibling):
            pass

        class Brother(Sibling):
            sibling = ReferenceField(Sibling)

        Sister.drop_collection()
        Brother.drop_collection()

        sister = Sister(name="Alice")
        sister.save()
        brother = Brother(name="Bob", sibling=sister)
        brother.save()

        self.assertEquals(Brother.objects[0].sibling.name, sister.name)

        Sister.drop_collection()
        Brother.drop_collection()

    def test_reference_abstract_class(self):
        """Ensure that an abstract class instance cannot be used in the
        reference of that abstract class.
        """
        class Sibling(Document):
            name = StringField()
            meta = {"abstract": True}

        class Sister(Sibling):
            pass

        class Brother(Sibling):
            sibling = ReferenceField(Sibling)

        Sister.drop_collection()
        Brother.drop_collection()

        sister = Sibling(name="Alice")
        brother = Brother(name="Bob", sibling=sister)
        self.assertRaises(ValidationError, brother.save)

        Sister.drop_collection()
        Brother.drop_collection()

    def test_abstract_reference_base_type(self):
        """Ensure that an an abstract reference fails validation when given a
        Document that does not inherit from the abstract type.
        """
        class Sibling(Document):
            name = StringField()
            meta = {"abstract": True}

        class Brother(Sibling):
            sibling = ReferenceField(Sibling)

        class Mother(Document):
            name = StringField()

        Brother.drop_collection()
        Mother.drop_collection()

        mother = Mother(name="Carol")
        mother.save()
        brother = Brother(name="Bob", sibling=mother)
        self.assertRaises(ValidationError, brother.save)

        Brother.drop_collection()
        Mother.drop_collection()

    def test_generic_reference(self):
        """Ensure that a GenericReferenceField properly dereferences items.
        """
        class Link(Document):
            title = StringField()
            meta = {'allow_inheritance': False}

        class Post(Document):
            title = StringField()

        class Bookmark(Document):
            bookmark_object = GenericReferenceField()

        Link.drop_collection()
        Post.drop_collection()
        Bookmark.drop_collection()

        link_1 = Link(title="Pitchfork")
        link_1.save()

        post_1 = Post(title="Behind the Scenes of the Pavement Reunion")
        post_1.save()

        bm = Bookmark(bookmark_object=post_1)
        bm.save()

        bm = Bookmark.objects(bookmark_object=post_1).first()

        self.assertEqual(bm.bookmark_object, post_1)
        self.assertTrue(isinstance(bm.bookmark_object, Post))

        bm.bookmark_object = link_1
        bm.save()

        bm = Bookmark.objects(bookmark_object=link_1).first()

        self.assertEqual(bm.bookmark_object, link_1)
        self.assertTrue(isinstance(bm.bookmark_object, Link))

        Link.drop_collection()
        Post.drop_collection()
        Bookmark.drop_collection()

    def test_generic_reference_list(self):
        """Ensure that a ListField properly dereferences generic references.
        """
        class Link(Document):
            title = StringField()

        class Post(Document):
            title = StringField()

        class User(Document):
            bookmarks = ListField(GenericReferenceField())

        Link.drop_collection()
        Post.drop_collection()
        User.drop_collection()

        link_1 = Link(title="Pitchfork")
        link_1.save()

        post_1 = Post(title="Behind the Scenes of the Pavement Reunion")
        post_1.save()

        user = User(bookmarks=[post_1, link_1])
        user.save()

        user = User.objects(bookmarks__all=[post_1, link_1]).first()

        self.assertEqual(user.bookmarks[0], post_1)
        self.assertEqual(user.bookmarks[1], link_1)

        Link.drop_collection()
        Post.drop_collection()
        User.drop_collection()

    def test_generic_reference_document_not_registered(self):
        """Ensure dereferencing out of the document registry throws a
        `NotRegistered` error.
        """
        class Link(Document):
            title = StringField()

        class User(Document):
            bookmarks = ListField(GenericReferenceField())

        Link.drop_collection()
        User.drop_collection()

        link_1 = Link(title="Pitchfork")
        link_1.save()

        user = User(bookmarks=[link_1])
        user.save()

        # Mimic User and Link definitions being in a different file
        # and the Link model not being imported in the User file.
        del(_document_registry["Link"])

        user = User.objects.first()
        try:
            user.bookmarks
            raise AssertionError("Link was removed from the registry")
        except NotRegistered:
            pass

        Link.drop_collection()
        User.drop_collection()

    def test_generic_reference_is_none(self):

        class Person(Document):
            name = StringField()
            city = GenericReferenceField()

        Person.drop_collection()
        Person(name="Wilson Jr").save()

        self.assertEqual(repr(Person.objects(city=None)),
                         "[<Person: Person object>]")

    def test_generic_reference_choices(self):
        """Ensure that a GenericReferenceField can handle choices
        """
        class Link(Document):
            title = StringField()

        class Post(Document):
            title = StringField()

        class Bookmark(Document):
            bookmark_object = GenericReferenceField(choices=(Post,))

        Link.drop_collection()
        Post.drop_collection()
        Bookmark.drop_collection()

        link_1 = Link(title="Pitchfork")
        link_1.save()

        post_1 = Post(title="Behind the Scenes of the Pavement Reunion")
        post_1.save()

        bm = Bookmark(bookmark_object=link_1)
        self.assertRaises(ValidationError, bm.validate)

        bm = Bookmark(bookmark_object=post_1)
        bm.save()

        bm = Bookmark.objects.first()
        self.assertEqual(bm.bookmark_object, post_1)

    def test_generic_reference_string_choices(self):
        """Ensure that a GenericReferenceField can handle choices as strings
        """
        class Link(Document):
            title = StringField()

        class Post(Document):
            title = StringField()

        class Bookmark(Document):
            bookmark_object = GenericReferenceField(choices=('Post', Link))

        Link.drop_collection()
        Post.drop_collection()
        Bookmark.drop_collection()

        link_1 = Link(title="Pitchfork")
        link_1.save()

        post_1 = Post(title="Behind the Scenes of the Pavement Reunion")
        post_1.save()

        bm = Bookmark(bookmark_object=link_1)
        bm.save()

        bm = Bookmark(bookmark_object=post_1)
        bm.save()

        bm = Bookmark(bookmark_object=bm)
        self.assertRaises(ValidationError, bm.validate)

    def test_generic_reference_choices_no_dereference(self):
        """Ensure that a GenericReferenceField can handle choices on
        non-derefenreced (i.e. DBRef) elements
        """
        class Post(Document):
            title = StringField()

        class Bookmark(Document):
            bookmark_object = GenericReferenceField(choices=(Post, ))
            other_field = StringField()

        Post.drop_collection()
        Bookmark.drop_collection()

        post_1 = Post(title="Behind the Scenes of the Pavement Reunion")
        post_1.save()

        bm = Bookmark(bookmark_object=post_1)
        bm.save()

        bm = Bookmark.objects.get(id=bm.id)
        # bookmark_object is now a DBRef
        bm.other_field = 'dummy_change'
        bm.save()

    def test_generic_reference_list_choices(self):
        """Ensure that a ListField properly dereferences generic references and
        respects choices.
        """
        class Link(Document):
            title = StringField()

        class Post(Document):
            title = StringField()

        class User(Document):
            bookmarks = ListField(GenericReferenceField(choices=(Post,)))

        Link.drop_collection()
        Post.drop_collection()
        User.drop_collection()

        link_1 = Link(title="Pitchfork")
        link_1.save()

        post_1 = Post(title="Behind the Scenes of the Pavement Reunion")
        post_1.save()

        user = User(bookmarks=[link_1])
        self.assertRaises(ValidationError, user.validate)

        user = User(bookmarks=[post_1])
        user.save()

        user = User.objects.first()
        self.assertEqual(user.bookmarks, [post_1])

        Link.drop_collection()
        Post.drop_collection()
        User.drop_collection()

    def test_generic_reference_list_item_modification(self):
        """Ensure that modifications of related documents (through generic reference) don't influence on querying
        """
        class Post(Document):
            title = StringField()

        class User(Document):
            username = StringField()
            bookmarks = ListField(GenericReferenceField())

        Post.drop_collection()
        User.drop_collection()

        post_1 = Post(title="Behind the Scenes of the Pavement Reunion")
        post_1.save()

        user = User(bookmarks=[post_1])
        user.save()

        post_1.title = "Title was modified"
        user.username = "New username"
        user.save()

        user = User.objects(bookmarks__all=[post_1]).first()

        self.assertNotEqual(user, None)
        self.assertEqual(user.bookmarks[0], post_1)

        Post.drop_collection()
        User.drop_collection()

    def test_binary_fields(self):
        """Ensure that binary fields can be stored and retrieved.
        """
        class Attachment(Document):
            content_type = StringField()
            blob = BinaryField()

        BLOB = b('\xe6\x00\xc4\xff\x07')
        MIME_TYPE = 'application/octet-stream'

        Attachment.drop_collection()

        attachment = Attachment(content_type=MIME_TYPE, blob=BLOB)
        attachment.save()

        attachment_1 = Attachment.objects().first()
        self.assertEqual(MIME_TYPE, attachment_1.content_type)
        self.assertEqual(BLOB, bin_type(attachment_1.blob))

        Attachment.drop_collection()

    def test_binary_validation(self):
        """Ensure that invalid values cannot be assigned to binary fields.
        """
        class Attachment(Document):
            blob = BinaryField()

        class AttachmentRequired(Document):
            blob = BinaryField(required=True)

        class AttachmentSizeLimit(Document):
            blob = BinaryField(max_bytes=4)

        Attachment.drop_collection()
        AttachmentRequired.drop_collection()
        AttachmentSizeLimit.drop_collection()

        attachment = Attachment()
        attachment.validate()
        attachment.blob = 2
        self.assertRaises(ValidationError, attachment.validate)

        attachment_required = AttachmentRequired()
        self.assertRaises(ValidationError, attachment_required.validate)
        attachment_required.blob = Binary(b('\xe6\x00\xc4\xff\x07'))
        attachment_required.validate()

        attachment_size_limit = AttachmentSizeLimit(
            blob=b('\xe6\x00\xc4\xff\x07'))
        self.assertRaises(ValidationError, attachment_size_limit.validate)
        attachment_size_limit.blob = b('\xe6\x00\xc4\xff')
        attachment_size_limit.validate()

        Attachment.drop_collection()
        AttachmentRequired.drop_collection()
        AttachmentSizeLimit.drop_collection()

    def test_binary_field_primary(self):

        class Attachment(Document):
            id = BinaryField(primary_key=True)

        Attachment.drop_collection()
        binary_id = uuid.uuid4().bytes
        att = Attachment(id=binary_id).save()
        self.assertEqual(1, Attachment.objects.count())
        self.assertEqual(1, Attachment.objects.filter(id=att.id).count())
        # TODO use assertIsNotNone once Python 2.6 support is dropped
        self.assertTrue(Attachment.objects.filter(id=att.id).first() is not None)
        att.delete()
        self.assertEqual(0, Attachment.objects.count())

    def test_binary_field_primary_filter_by_binary_pk_as_str(self):

        raise SkipTest("Querying by id as string is not currently supported")

        class Attachment(Document):
            id = BinaryField(primary_key=True)

        Attachment.drop_collection()
        binary_id = uuid.uuid4().bytes
        att = Attachment(id=binary_id).save()
        self.assertEqual(1, Attachment.objects.filter(id=binary_id).count())
        # TODO use assertIsNotNone once Python 2.6 support is dropped
        self.assertTrue(Attachment.objects.filter(id=binary_id).first() is not None)
        att.delete()
        self.assertEqual(0, Attachment.objects.count())

    def test_choices_validation(self):
        """Ensure that value is in a container of allowed values.
        """
        class Shirt(Document):
            size = StringField(max_length=3, choices=(
                ('S', 'Small'), ('M', 'Medium'), ('L', 'Large'),
                ('XL', 'Extra Large'), ('XXL', 'Extra Extra Large')))

        Shirt.drop_collection()

        shirt = Shirt()
        shirt.validate()

        shirt.size = "S"
        shirt.validate()

        shirt.size = "XS"
        self.assertRaises(ValidationError, shirt.validate)

        Shirt.drop_collection()

    def test_choices_validation_documents(self):
        """
        Ensure fields with document choices validate given a valid choice.
        """
        class UserComments(EmbeddedDocument):
            author = StringField()
            message = StringField()

        class BlogPost(Document):
            comments = ListField(
                GenericEmbeddedDocumentField(choices=(UserComments,))
            )

        # Ensure Validation Passes
        BlogPost(comments=[
            UserComments(author='user2', message='message2'),
        ]).save()

    def test_choices_validation_documents_invalid(self):
        """
        Ensure fields with document choices validate given an invalid choice.
        This should throw a ValidationError exception.
        """
        class UserComments(EmbeddedDocument):
            author = StringField()
            message = StringField()

        class ModeratorComments(EmbeddedDocument):
            author = StringField()
            message = StringField()

        class BlogPost(Document):
            comments = ListField(
                GenericEmbeddedDocumentField(choices=(UserComments,))
            )

        # Single Entry Failure
        post = BlogPost(comments=[
            ModeratorComments(author='mod1', message='message1'),
        ])
        self.assertRaises(ValidationError, post.save)

        # Mixed Entry Failure
        post = BlogPost(comments=[
            ModeratorComments(author='mod1', message='message1'),
            UserComments(author='user2', message='message2'),
        ])
        self.assertRaises(ValidationError, post.save)

    def test_choices_validation_documents_inheritance(self):
        """
        Ensure fields with document choices validate given subclass of choice.
        """
        class Comments(EmbeddedDocument):
            meta = {
                'abstract': True
            }
            author = StringField()
            message = StringField()

        class UserComments(Comments):
            pass

        class BlogPost(Document):
            comments = ListField(
                GenericEmbeddedDocumentField(choices=(Comments,))
            )

        # Save Valid EmbeddedDocument Type
        BlogPost(comments=[
            UserComments(author='user2', message='message2'),
        ]).save()

    def test_choices_get_field_display(self):
        """Test dynamic helper for returning the display value of a choices
        field.
        """
        class Shirt(Document):
            size = StringField(max_length=3, choices=(
                ('S', 'Small'), ('M', 'Medium'), ('L', 'Large'),
                ('XL', 'Extra Large'), ('XXL', 'Extra Extra Large')))
            style = StringField(max_length=3, choices=(
                ('S', 'Small'), ('B', 'Baggy'), ('W', 'wide')), default='S')

        Shirt.drop_collection()

        shirt = Shirt()

        self.assertEqual(shirt.get_size_display(), None)
        self.assertEqual(shirt.get_style_display(), 'Small')

        shirt.size = "XXL"
        shirt.style = "B"
        self.assertEqual(shirt.get_size_display(), 'Extra Extra Large')
        self.assertEqual(shirt.get_style_display(), 'Baggy')

        # Set as Z - an invalid choice
        shirt.size = "Z"
        shirt.style = "Z"
        self.assertEqual(shirt.get_size_display(), 'Z')
        self.assertEqual(shirt.get_style_display(), 'Z')
        self.assertRaises(ValidationError, shirt.validate)

        Shirt.drop_collection()

    def test_simple_choices_validation(self):
        """Ensure that value is in a container of allowed values.
        """
        class Shirt(Document):
            size = StringField(max_length=3,
                               choices=('S', 'M', 'L', 'XL', 'XXL'))

        Shirt.drop_collection()

        shirt = Shirt()
        shirt.validate()

        shirt.size = "S"
        shirt.validate()

        shirt.size = "XS"
        self.assertRaises(ValidationError, shirt.validate)

        Shirt.drop_collection()

    def test_simple_choices_get_field_display(self):
        """Test dynamic helper for returning the display value of a choices
        field.
        """
        class Shirt(Document):
            size = StringField(max_length=3,
                               choices=('S', 'M', 'L', 'XL', 'XXL'))
            style = StringField(max_length=3,
                                choices=('Small', 'Baggy', 'wide'),
                                default='Small')

        Shirt.drop_collection()

        shirt = Shirt()

        self.assertEqual(shirt.get_size_display(), None)
        self.assertEqual(shirt.get_style_display(), 'Small')

        shirt.size = "XXL"
        shirt.style = "Baggy"
        self.assertEqual(shirt.get_size_display(), 'XXL')
        self.assertEqual(shirt.get_style_display(), 'Baggy')

        # Set as Z - an invalid choice
        shirt.size = "Z"
        shirt.style = "Z"
        self.assertEqual(shirt.get_size_display(), 'Z')
        self.assertEqual(shirt.get_style_display(), 'Z')
        self.assertRaises(ValidationError, shirt.validate)

        Shirt.drop_collection()

    def test_simple_choices_validation_invalid_value(self):
        """Ensure that error messages are correct.
        """
        SIZES = ('S', 'M', 'L', 'XL', 'XXL')
        COLORS = (('R', 'Red'), ('B', 'Blue'))
        SIZE_MESSAGE = u"Value must be one of ('S', 'M', 'L', 'XL', 'XXL')"
        COLOR_MESSAGE = u"Value must be one of ['R', 'B']"

        class Shirt(Document):
            size = StringField(max_length=3, choices=SIZES)
            color = StringField(max_length=1, choices=COLORS)

        Shirt.drop_collection()

        shirt = Shirt()
        shirt.validate()

        shirt.size = "S"
        shirt.color = "R"
        shirt.validate()

        shirt.size = "XS"
        shirt.color = "G"

        try:
            shirt.validate()
        except ValidationError, error:
            # get the validation rules
            error_dict = error.to_dict()
            self.assertEqual(error_dict['size'], SIZE_MESSAGE)
            self.assertEqual(error_dict['color'], COLOR_MESSAGE)

        Shirt.drop_collection()

    def test_ensure_unique_default_instances(self):
        """Ensure that every field has it's own unique default instance."""
        class D(Document):
            data = DictField()
            data2 = DictField(default=lambda: {})

        d1 = D()
        d1.data['foo'] = 'bar'
        d1.data2['foo'] = 'bar'
        d2 = D()
        self.assertEqual(d2.data, {})
        self.assertEqual(d2.data2, {})

    def test_sequence_field(self):
        class Person(Document):
            id = SequenceField(primary_key=True)
            name = StringField()

        self.db['mongoengine.counters'].drop()
        Person.drop_collection()

        for x in xrange(10):
            Person(name="Person %s" % x).save()

        c = self.db['mongoengine.counters'].find_one({'_id': 'person.id'})
        self.assertEqual(c['next'], 10)

        ids = [i.id for i in Person.objects]
        self.assertEqual(ids, range(1, 11))

        c = self.db['mongoengine.counters'].find_one({'_id': 'person.id'})
        self.assertEqual(c['next'], 10)

        Person.id.set_next_value(1000)
        c = self.db['mongoengine.counters'].find_one({'_id': 'person.id'})
        self.assertEqual(c['next'], 1000)

    def test_sequence_field_get_next_value(self):
        class Person(Document):
            id = SequenceField(primary_key=True)
            name = StringField()

        self.db['mongoengine.counters'].drop()
        Person.drop_collection()

        for x in xrange(10):
            Person(name="Person %s" % x).save()

        self.assertEqual(Person.id.get_next_value(), 11)
        self.db['mongoengine.counters'].drop()

        self.assertEqual(Person.id.get_next_value(), 1)

        class Person(Document):
            id = SequenceField(primary_key=True, value_decorator=str)
            name = StringField()

        self.db['mongoengine.counters'].drop()
        Person.drop_collection()

        for x in xrange(10):
            Person(name="Person %s" % x).save()

        self.assertEqual(Person.id.get_next_value(), '11')
        self.db['mongoengine.counters'].drop()

        self.assertEqual(Person.id.get_next_value(), '1')

    def test_sequence_field_sequence_name(self):
        class Person(Document):
            id = SequenceField(primary_key=True, sequence_name='jelly')
            name = StringField()

        self.db['mongoengine.counters'].drop()
        Person.drop_collection()

        for x in xrange(10):
            Person(name="Person %s" % x).save()

        c = self.db['mongoengine.counters'].find_one({'_id': 'jelly.id'})
        self.assertEqual(c['next'], 10)

        ids = [i.id for i in Person.objects]
        self.assertEqual(ids, range(1, 11))

        c = self.db['mongoengine.counters'].find_one({'_id': 'jelly.id'})
        self.assertEqual(c['next'], 10)

        Person.id.set_next_value(1000)
        c = self.db['mongoengine.counters'].find_one({'_id': 'jelly.id'})
        self.assertEqual(c['next'], 1000)

    def test_multiple_sequence_fields(self):
        class Person(Document):
            id = SequenceField(primary_key=True)
            counter = SequenceField()
            name = StringField()

        self.db['mongoengine.counters'].drop()
        Person.drop_collection()

        for x in xrange(10):
            Person(name="Person %s" % x).save()

        c = self.db['mongoengine.counters'].find_one({'_id': 'person.id'})
        self.assertEqual(c['next'], 10)

        ids = [i.id for i in Person.objects]
        self.assertEqual(ids, range(1, 11))

        counters = [i.counter for i in Person.objects]
        self.assertEqual(counters, range(1, 11))

        c = self.db['mongoengine.counters'].find_one({'_id': 'person.id'})
        self.assertEqual(c['next'], 10)

        Person.id.set_next_value(1000)
        c = self.db['mongoengine.counters'].find_one({'_id': 'person.id'})
        self.assertEqual(c['next'], 1000)

        Person.counter.set_next_value(999)
        c = self.db['mongoengine.counters'].find_one({'_id': 'person.counter'})
        self.assertEqual(c['next'], 999)

    def test_sequence_fields_reload(self):
        class Animal(Document):
            counter = SequenceField()
            name = StringField()

        self.db['mongoengine.counters'].drop()
        Animal.drop_collection()

        a = Animal(name="Boi").save()

        self.assertEqual(a.counter, 1)
        a.reload()
        self.assertEqual(a.counter, 1)

        a.counter = None
        self.assertEqual(a.counter, 2)
        a.save()

        self.assertEqual(a.counter, 2)

        a = Animal.objects.first()
        self.assertEqual(a.counter, 2)
        a.reload()
        self.assertEqual(a.counter, 2)

    def test_multiple_sequence_fields_on_docs(self):

        class Animal(Document):
            id = SequenceField(primary_key=True)
            name = StringField()

        class Person(Document):
            id = SequenceField(primary_key=True)
            name = StringField()

        self.db['mongoengine.counters'].drop()
        Animal.drop_collection()
        Person.drop_collection()

        for x in xrange(10):
            Animal(name="Animal %s" % x).save()
            Person(name="Person %s" % x).save()

        c = self.db['mongoengine.counters'].find_one({'_id': 'person.id'})
        self.assertEqual(c['next'], 10)

        c = self.db['mongoengine.counters'].find_one({'_id': 'animal.id'})
        self.assertEqual(c['next'], 10)

        ids = [i.id for i in Person.objects]
        self.assertEqual(ids, range(1, 11))

        id = [i.id for i in Animal.objects]
        self.assertEqual(id, range(1, 11))

        c = self.db['mongoengine.counters'].find_one({'_id': 'person.id'})
        self.assertEqual(c['next'], 10)

        c = self.db['mongoengine.counters'].find_one({'_id': 'animal.id'})
        self.assertEqual(c['next'], 10)

    def test_sequence_field_value_decorator(self):
        class Person(Document):
            id = SequenceField(primary_key=True, value_decorator=str)
            name = StringField()

        self.db['mongoengine.counters'].drop()
        Person.drop_collection()

        for x in xrange(10):
            p = Person(name="Person %s" % x)
            p.save()

        c = self.db['mongoengine.counters'].find_one({'_id': 'person.id'})
        self.assertEqual(c['next'], 10)

        ids = [i.id for i in Person.objects]
        self.assertEqual(ids, map(str, range(1, 11)))

        c = self.db['mongoengine.counters'].find_one({'_id': 'person.id'})
        self.assertEqual(c['next'], 10)

    def test_embedded_sequence_field(self):
        class Comment(EmbeddedDocument):
            id = SequenceField()
            content = StringField(required=True)

        class Post(Document):
            title = StringField(required=True)
            comments = ListField(EmbeddedDocumentField(Comment))

        self.db['mongoengine.counters'].drop()
        Post.drop_collection()

        Post(title="MongoEngine",
             comments=[Comment(content="NoSQL Rocks"),
                       Comment(content="MongoEngine Rocks")]).save()
        c = self.db['mongoengine.counters'].find_one({'_id': 'comment.id'})
        self.assertEqual(c['next'], 2)
        post = Post.objects.first()
        self.assertEqual(1, post.comments[0].id)
        self.assertEqual(2, post.comments[1].id)

    def test_inherited_sequencefield(self):
        class Base(Document):
            name = StringField()
            counter = SequenceField()
            meta = {'abstract': True}

        class Foo(Base):
            pass

        class Bar(Base):
            pass

        bar = Bar(name='Bar')
        bar.save()

        foo = Foo(name='Foo')
        foo.save()

        self.assertTrue('base.counter' in
                        self.db['mongoengine.counters'].find().distinct('_id'))
        self.assertFalse(('foo.counter' or 'bar.counter') in
                         self.db['mongoengine.counters'].find().distinct('_id'))
        self.assertNotEqual(foo.counter, bar.counter)
        self.assertEqual(foo._fields['counter'].owner_document, Base)
        self.assertEqual(bar._fields['counter'].owner_document, Base)

    def test_no_inherited_sequencefield(self):
        class Base(Document):
            name = StringField()
            meta = {'abstract': True}

        class Foo(Base):
            counter = SequenceField()

        class Bar(Base):
            counter = SequenceField()

        bar = Bar(name='Bar')
        bar.save()

        foo = Foo(name='Foo')
        foo.save()

        self.assertFalse('base.counter' in
                         self.db['mongoengine.counters'].find().distinct('_id'))
        self.assertTrue(('foo.counter' and 'bar.counter') in
                         self.db['mongoengine.counters'].find().distinct('_id'))
        self.assertEqual(foo.counter, bar.counter)
        self.assertEqual(foo._fields['counter'].owner_document, Foo)
        self.assertEqual(bar._fields['counter'].owner_document, Bar)

    def test_generic_embedded_document(self):
        class Car(EmbeddedDocument):
            name = StringField()

        class Dish(EmbeddedDocument):
            food = StringField(required=True)
            number = IntField()

        class Person(Document):
            name = StringField()
            like = GenericEmbeddedDocumentField()

        Person.drop_collection()

        person = Person(name='Test User')
        person.like = Car(name='Fiat')
        person.save()

        person = Person.objects.first()
        self.assertTrue(isinstance(person.like, Car))

        person.like = Dish(food="arroz", number=15)
        person.save()

        person = Person.objects.first()
        self.assertTrue(isinstance(person.like, Dish))

    def test_generic_embedded_document_choices(self):
        """Ensure you can limit GenericEmbeddedDocument choices
        """
        class Car(EmbeddedDocument):
            name = StringField()

        class Dish(EmbeddedDocument):
            food = StringField(required=True)
            number = IntField()

        class Person(Document):
            name = StringField()
            like = GenericEmbeddedDocumentField(choices=(Dish,))

        Person.drop_collection()

        person = Person(name='Test User')
        person.like = Car(name='Fiat')
        self.assertRaises(ValidationError, person.validate)

        person.like = Dish(food="arroz", number=15)
        person.save()

        person = Person.objects.first()
        self.assertTrue(isinstance(person.like, Dish))

    def test_generic_list_embedded_document_choices(self):
        """Ensure you can limit GenericEmbeddedDocument choices inside a list
        field
        """
        class Car(EmbeddedDocument):
            name = StringField()

        class Dish(EmbeddedDocument):
            food = StringField(required=True)
            number = IntField()

        class Person(Document):
            name = StringField()
            likes = ListField(GenericEmbeddedDocumentField(choices=(Dish,)))

        Person.drop_collection()

        person = Person(name='Test User')
        person.likes = [Car(name='Fiat')]
        self.assertRaises(ValidationError, person.validate)

        person.likes = [Dish(food="arroz", number=15)]
        person.save()

        person = Person.objects.first()
        self.assertTrue(isinstance(person.likes[0], Dish))

    def test_recursive_validation(self):
        """Ensure that a validation result to_dict is available.
        """
        class Author(EmbeddedDocument):
            name = StringField(required=True)

        class Comment(EmbeddedDocument):
            author = EmbeddedDocumentField(Author, required=True)
            content = StringField(required=True)

        class Post(Document):
            title = StringField(required=True)
            comments = ListField(EmbeddedDocumentField(Comment))

        bob = Author(name='Bob')
        post = Post(title='hello world')
        post.comments.append(Comment(content='hello', author=bob))
        post.comments.append(Comment(author=bob))

        self.assertRaises(ValidationError, post.validate)
        try:
            post.validate()
        except ValidationError, error:
            # ValidationError.errors property
            self.assertTrue(hasattr(error, 'errors'))
            self.assertTrue(isinstance(error.errors, dict))
            self.assertTrue('comments' in error.errors)
            self.assertTrue(1 in error.errors['comments'])
            self.assertTrue(isinstance(error.errors['comments'][1]['content'],
                                       ValidationError))

            # ValidationError.schema property
            error_dict = error.to_dict()
            self.assertTrue(isinstance(error_dict, dict))
            self.assertTrue('comments' in error_dict)
            self.assertTrue(1 in error_dict['comments'])
            self.assertTrue('content' in error_dict['comments'][1])
            self.assertEqual(error_dict['comments'][1]['content'],
                             u'Field is required')

        post.comments[1].content = 'here we go'
        post.validate()

    def test_email_field(self):
        class User(Document):
            email = EmailField()

        user = User(email="ross@example.com")
        self.assertTrue(user.validate() is None)

        user = User(email="ross@example.co.uk")
        self.assertTrue(user.validate() is None)

        user = User(email=("Kofq@rhom0e4klgauOhpbpNdogawnyIKvQS0wk2mjqrgGQ5S"
                           "aJIazqqWkm7.net"))
        self.assertTrue(user.validate() is None)

        user = User(email="new-tld@example.technology")
        self.assertTrue(user.validate() is None)

        user = User(email='me@localhost')
        self.assertRaises(ValidationError, user.validate)

        user = User(email="ross@example.com.")
        self.assertRaises(ValidationError, user.validate)

    def test_email_field_honors_regex(self):
        class User(Document):
            email = EmailField(regex=r'\w+@example.com')

        # Fails regex validation
        user = User(email='me@foo.com')
        self.assertRaises(ValidationError, user.validate)

        # Passes regex validation
        user = User(email='me@example.com')
        self.assertTrue(user.validate() is None)

    def test_tuples_as_tuples(self):
        """
        Ensure that tuples remain tuples when they are
        inside a ComplexBaseField
        """
        from mongoengine.base import BaseField

        class EnumField(BaseField):

            def __init__(self, **kwargs):
                super(EnumField, self).__init__(**kwargs)

            def to_mongo(self, value, **kwargs):
                return value

            def to_python(self, value):
                return tuple(value)

        class TestDoc(Document):
            items = ListField(EnumField())

        TestDoc.drop_collection()
        tuples = [(100, 'Testing')]
        doc = TestDoc()
        doc.items = tuples
        doc.save()
        x = TestDoc.objects().get()
        self.assertTrue(x is not None)
        self.assertTrue(len(x.items) == 1)
        self.assertTrue(tuple(x.items[0]) in tuples)
        self.assertTrue(x.items[0] in tuples)

    def test_dynamic_fields_class(self):

        class Doc2(Document):
            field_1 = StringField(db_field='f')

        class Doc(Document):
            my_id = IntField(required=True, unique=True, primary_key=True)
            embed_me = DynamicField(db_field='e')
            field_x = StringField(db_field='x')

        Doc.drop_collection()
        Doc2.drop_collection()

        doc2 = Doc2(field_1="hello")
        doc = Doc(my_id=1, embed_me=doc2, field_x="x")
        self.assertRaises(OperationError, doc.save)

        doc2.save()
        doc.save()

        doc = Doc.objects.get()
        self.assertEqual(doc.embed_me.field_1, "hello")

    def test_dynamic_fields_embedded_class(self):

        class Embed(EmbeddedDocument):
            field_1 = StringField(db_field='f')

        class Doc(Document):
            my_id = IntField(required=True, unique=True, primary_key=True)
            embed_me = DynamicField(db_field='e')
            field_x = StringField(db_field='x')

        Doc.drop_collection()

        Doc(my_id=1, embed_me=Embed(field_1="hello"), field_x="x").save()

        doc = Doc.objects.get()
        self.assertEqual(doc.embed_me.field_1, "hello")

    def test_dynamicfield_dump_document(self):
        """Ensure a DynamicField can handle another document's dump
        """
        class Doc(Document):
            field = DynamicField()

        class ToEmbed(Document):
            id = IntField(primary_key=True, default=1)
            recursive = DynamicField()

        class ToEmbedParent(Document):
            id = IntField(primary_key=True, default=1)
            recursive = DynamicField()

            meta = {'allow_inheritance': True}

        class ToEmbedChild(ToEmbedParent):
            pass

        to_embed_recursive = ToEmbed(id=1).save()
        to_embed = ToEmbed(id=2, recursive=to_embed_recursive).save()
        doc = Doc(field=to_embed)
        doc.save()
        assert isinstance(doc.field, ToEmbed)
        assert doc.field == to_embed
        # Same thing with a Document with a _cls field
        to_embed_recursive = ToEmbedChild(id=1).save()
        to_embed_child = ToEmbedChild(id=2, recursive=to_embed_recursive).save()
        doc = Doc(field=to_embed_child)
        doc.save()
        assert isinstance(doc.field, ToEmbedChild)
        assert doc.field == to_embed_child

    def test_invalid_dict_value(self):
        class DictFieldTest(Document):
            dictionary = DictField(required=True)

        DictFieldTest.drop_collection()

        test = DictFieldTest(dictionary=None)
        test.dictionary  # Just access to test getter
        self.assertRaises(ValidationError, test.validate)

        test = DictFieldTest(dictionary=False)
        test.dictionary  # Just access to test getter
        self.assertRaises(ValidationError, test.validate)

    def test_cls_field(self):
        class Animal(Document):
            meta = {'allow_inheritance': True}

        class Fish(Animal):
            pass

        class Mammal(Animal):
            pass

        class Dog(Mammal):
            pass

        class Human(Mammal):
            pass

        Animal.objects.delete()
        Dog().save()
        Fish().save()
        Human().save()
        self.assertEquals(Animal.objects(_cls__in=["Animal.Mammal.Dog", "Animal.Fish"]).count(), 2)
        self.assertEquals(Animal.objects(_cls__in=["Animal.Fish.Guppy"]).count(), 0)

    def test_sparse_field(self):
        class Doc(Document):
            name = StringField(required=False, unique=True, sparse=True)
        try:
            Doc().save()
            Doc().save()
        except Exception:
            self.fail()

    def test_undefined_field_exception(self):
        """Tests if a `FieldDoesNotExist` exception is raised when trying to
        instanciate a document with a field that's not defined.
        """

        class Doc(Document):
            foo = StringField(db_field='f')

        def test():
            Doc(bar='test')

        self.assertRaises(FieldDoesNotExist, test)

    def test_undefined_field_exception_with_strict(self):
        """Tests if a `FieldDoesNotExist` exception is raised when trying to
        instanciate a document with a field that's not defined,
        even when strict is set to False.
        """

        class Doc(Document):
            foo = StringField(db_field='f')
            meta = {'strict': False}

        def test():
            Doc(bar='test')

        self.assertRaises(FieldDoesNotExist, test)

    def test_long_field_is_considered_as_int64(self):
        """
        Tests that long fields are stored as long in mongo, even if long value
        is small enough to be an int.
        """
        class TestLongFieldConsideredAsInt64(Document):
            some_long = LongField()

        doc = TestLongFieldConsideredAsInt64(some_long=42).save()
        db = get_db()
        self.assertTrue(isinstance(db.test_long_field_considered_as_int64.find()[0]['some_long'], Int64))
        self.assertTrue(isinstance(doc.some_long, six.integer_types))


class EmbeddedDocumentListFieldTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = connect(db='EmbeddedDocumentListFieldTestCase')

        class Comments(EmbeddedDocument):
            author = StringField()
            message = StringField()

        class BlogPost(Document):
            comments = EmbeddedDocumentListField(Comments)

        cls.Comments = Comments
        cls.BlogPost = BlogPost

    def setUp(self):
        """
        Create two BlogPost entries in the database, each with
        several EmbeddedDocuments.
        """
        self.post1 = self.BlogPost(comments=[
            self.Comments(author='user1', message='message1'),
            self.Comments(author='user2', message='message1')
        ]).save()

        self.post2 = self.BlogPost(comments=[
            self.Comments(author='user2', message='message2'),
            self.Comments(author='user2', message='message3'),
            self.Comments(author='user3', message='message1')
        ]).save()

    def tearDown(self):
        self.BlogPost.drop_collection()

    @classmethod
    def tearDownClass(cls):
        cls.db.drop_database('EmbeddedDocumentListFieldTestCase')

    def test_no_keyword_filter(self):
        """
        Tests the filter method of a List of Embedded Documents
        with a no keyword.
        """
        filtered = self.post1.comments.filter()

        # Ensure nothing was changed
        # < 2.6 Incompatible >
        # self.assertListEqual(filtered, self.post1.comments)
        self.assertEqual(filtered, self.post1.comments)

    def test_single_keyword_filter(self):
        """
        Tests the filter method of a List of Embedded Documents
        with a single keyword.
        """
        filtered = self.post1.comments.filter(author='user1')

        # Ensure only 1 entry was returned.
        self.assertEqual(len(filtered), 1)

        # Ensure the entry returned is the correct entry.
        self.assertEqual(filtered[0].author, 'user1')

    def test_multi_keyword_filter(self):
        """
        Tests the filter method of a List of Embedded Documents
        with multiple keywords.
        """
        filtered = self.post2.comments.filter(
            author='user2', message='message2'
        )

        # Ensure only 1 entry was returned.
        self.assertEqual(len(filtered), 1)

        # Ensure the entry returned is the correct entry.
        self.assertEqual(filtered[0].author, 'user2')
        self.assertEqual(filtered[0].message, 'message2')

    def test_chained_filter(self):
        """
        Tests chained filter methods of a List of Embedded Documents
        """
        filtered = self.post2.comments.filter(author='user2').filter(
            message='message2'
        )

        # Ensure only 1 entry was returned.
        self.assertEqual(len(filtered), 1)

        # Ensure the entry returned is the correct entry.
        self.assertEqual(filtered[0].author, 'user2')
        self.assertEqual(filtered[0].message, 'message2')

    def test_unknown_keyword_filter(self):
        """
        Tests the filter method of a List of Embedded Documents
        when the keyword is not a known keyword.
        """
        # < 2.6 Incompatible >
        # with self.assertRaises(AttributeError):
        #    self.post2.comments.filter(year=2)
        self.assertRaises(AttributeError, self.post2.comments.filter, year=2)

    def test_no_keyword_exclude(self):
        """
        Tests the exclude method of a List of Embedded Documents
        with a no keyword.
        """
        filtered = self.post1.comments.exclude()

        # Ensure everything was removed
        # < 2.6 Incompatible >
        # self.assertListEqual(filtered, [])
        self.assertEqual(filtered, [])

    def test_single_keyword_exclude(self):
        """
        Tests the exclude method of a List of Embedded Documents
        with a single keyword.
        """
        excluded = self.post1.comments.exclude(author='user1')

        # Ensure only 1 entry was returned.
        self.assertEqual(len(excluded), 1)

        # Ensure the entry returned is the correct entry.
        self.assertEqual(excluded[0].author, 'user2')

    def test_multi_keyword_exclude(self):
        """
        Tests the exclude method of a List of Embedded Documents
        with multiple keywords.
        """
        excluded = self.post2.comments.exclude(
            author='user3', message='message1'
        )

        # Ensure only 2 entries were returned.
        self.assertEqual(len(excluded), 2)

        # Ensure the entries returned are the correct entries.
        self.assertEqual(excluded[0].author, 'user2')
        self.assertEqual(excluded[1].author, 'user2')

    def test_non_matching_exclude(self):
        """
        Tests the exclude method of a List of Embedded Documents
        when the keyword does not match any entries.
        """
        excluded = self.post2.comments.exclude(author='user4')

        # Ensure the 3 entries still exist.
        self.assertEqual(len(excluded), 3)

    def test_unknown_keyword_exclude(self):
        """
        Tests the exclude method of a List of Embedded Documents
        when the keyword is not a known keyword.
        """
        # < 2.6 Incompatible >
        # with self.assertRaises(AttributeError):
        #    self.post2.comments.exclude(year=2)
        self.assertRaises(AttributeError, self.post2.comments.exclude, year=2)

    def test_chained_filter_exclude(self):
        """
        Tests the exclude method after a filter method of a List of
        Embedded Documents.
        """
        excluded = self.post2.comments.filter(author='user2').exclude(
            message='message2'
        )

        # Ensure only 1 entry was returned.
        self.assertEqual(len(excluded), 1)

        # Ensure the entry returned is the correct entry.
        self.assertEqual(excluded[0].author, 'user2')
        self.assertEqual(excluded[0].message, 'message3')

    def test_count(self):
        """
        Tests the count method of a List of Embedded Documents.
        """
        self.assertEqual(self.post1.comments.count(), 2)
        self.assertEqual(self.post1.comments.count(), len(self.post1.comments))

    def test_filtered_count(self):
        """
        Tests the filter + count method of a List of Embedded Documents.
        """
        count = self.post1.comments.filter(author='user1').count()
        self.assertEqual(count, 1)

    def test_single_keyword_get(self):
        """
        Tests the get method of a List of Embedded Documents using a
        single keyword.
        """
        comment = self.post1.comments.get(author='user1')

        # < 2.6 Incompatible >
        # self.assertIsInstance(comment, self.Comments)
        self.assertTrue(isinstance(comment, self.Comments))
        self.assertEqual(comment.author, 'user1')

    def test_multi_keyword_get(self):
        """
        Tests the get method of a List of Embedded Documents using
        multiple keywords.
        """
        comment = self.post2.comments.get(author='user2', message='message2')

        # < 2.6 Incompatible >
        # self.assertIsInstance(comment, self.Comments)
        self.assertTrue(isinstance(comment, self.Comments))
        self.assertEqual(comment.author, 'user2')
        self.assertEqual(comment.message, 'message2')

    def test_no_keyword_multiple_return_get(self):
        """
        Tests the get method of a List of Embedded Documents without
        a keyword to return multiple documents.
        """
        # < 2.6 Incompatible >
        # with self.assertRaises(MultipleObjectsReturned):
        #    self.post1.comments.get()
        self.assertRaises(MultipleObjectsReturned, self.post1.comments.get)

    def test_keyword_multiple_return_get(self):
        """
        Tests the get method of a List of Embedded Documents with a keyword
        to return multiple documents.
        """
        # < 2.6 Incompatible >
        # with self.assertRaises(MultipleObjectsReturned):
        #    self.post2.comments.get(author='user2')
        self.assertRaises(
            MultipleObjectsReturned, self.post2.comments.get, author='user2'
        )

    def test_unknown_keyword_get(self):
        """
        Tests the get method of a List of Embedded Documents with an
        unknown keyword.
        """
        # < 2.6 Incompatible >
        # with self.assertRaises(AttributeError):
        #    self.post2.comments.get(year=2020)
        self.assertRaises(AttributeError, self.post2.comments.get, year=2020)

    def test_no_result_get(self):
        """
        Tests the get method of a List of Embedded Documents where get
        returns no results.
        """
        # < 2.6 Incompatible >
        # with self.assertRaises(DoesNotExist):
        #    self.post1.comments.get(author='user3')
        self.assertRaises(
            DoesNotExist, self.post1.comments.get, author='user3'
        )

    def test_first(self):
        """
        Tests the first method of a List of Embedded Documents to
        ensure it returns the first comment.
        """
        comment = self.post1.comments.first()

        # Ensure a Comment object was returned.
        # < 2.6 Incompatible >
        # self.assertIsInstance(comment, self.Comments)
        self.assertTrue(isinstance(comment, self.Comments))
        self.assertEqual(comment, self.post1.comments[0])

    def test_create(self):
        """
        Test the create method of a List of Embedded Documents.
        """
        comment = self.post1.comments.create(
            author='user4', message='message1'
        )
        self.post1.save()

        # Ensure the returned value is the comment object.
        # < 2.6 Incompatible >
        # self.assertIsInstance(comment, self.Comments)
        self.assertTrue(isinstance(comment, self.Comments))
        self.assertEqual(comment.author, 'user4')
        self.assertEqual(comment.message, 'message1')

        # Ensure the new comment was actually saved to the database.
        # < 2.6 Incompatible >
        # self.assertIn(
        #    comment,
        #    self.BlogPost.objects(comments__author='user4')[0].comments
        # )
        self.assertTrue(
            comment in self.BlogPost.objects(
                comments__author='user4'
            )[0].comments
        )

    def test_filtered_create(self):
        """
        Test the create method of a List of Embedded Documents chained
        to a call to the filter method. Filtering should have no effect
        on creation.
        """
        comment = self.post1.comments.filter(author='user1').create(
            author='user4', message='message1'
        )
        self.post1.save()

        # Ensure the returned value is the comment object.
        # < 2.6 Incompatible >
        # self.assertIsInstance(comment, self.Comments)
        self.assertTrue(isinstance(comment, self.Comments))
        self.assertEqual(comment.author, 'user4')
        self.assertEqual(comment.message, 'message1')

        # Ensure the new comment was actually saved to the database.
        # < 2.6 Incompatible >
        # self.assertIn(
        #    comment,
        #    self.BlogPost.objects(comments__author='user4')[0].comments
        # )
        self.assertTrue(
            comment in self.BlogPost.objects(
                comments__author='user4'
            )[0].comments
        )

    def test_no_keyword_update(self):
        """
        Tests the update method of a List of Embedded Documents with
        no keywords.
        """
        original = list(self.post1.comments)
        number = self.post1.comments.update()
        self.post1.save()

        # Ensure that nothing was altered.
        # < 2.6 Incompatible >
        # self.assertIn(
        #    original[0],
        #    self.BlogPost.objects(id=self.post1.id)[0].comments
        # )
        self.assertTrue(
            original[0] in self.BlogPost.objects(id=self.post1.id)[0].comments
        )

        # < 2.6 Incompatible >
        # self.assertIn(
        #    original[1],
        #    self.BlogPost.objects(id=self.post1.id)[0].comments
        # )
        self.assertTrue(
            original[1] in self.BlogPost.objects(id=self.post1.id)[0].comments
        )

        # Ensure the method returned 0 as the number of entries
        # modified
        self.assertEqual(number, 0)

    def test_single_keyword_update(self):
        """
        Tests the update method of a List of Embedded Documents with
        a single keyword.
        """
        number = self.post1.comments.update(author='user4')
        self.post1.save()

        comments = self.BlogPost.objects(id=self.post1.id)[0].comments

        # Ensure that the database was updated properly.
        self.assertEqual(comments[0].author, 'user4')
        self.assertEqual(comments[1].author, 'user4')

        # Ensure the method returned 2 as the number of entries
        # modified
        self.assertEqual(number, 2)

    def test_save(self):
        """
        Tests the save method of a List of Embedded Documents.
        """
        comments = self.post1.comments
        new_comment = self.Comments(author='user4')
        comments.append(new_comment)
        comments.save()

        # Ensure that the new comment has been added to the database.
        # < 2.6 Incompatible >
        # self.assertIn(
        #    new_comment,
        #    self.BlogPost.objects(id=self.post1.id)[0].comments
        # )
        self.assertTrue(
            new_comment in self.BlogPost.objects(id=self.post1.id)[0].comments
        )

    def test_delete(self):
        """
        Tests the delete method of a List of Embedded Documents.
        """
        number = self.post1.comments.delete()
        self.post1.save()

        # Ensure that all the comments under post1 were deleted in the
        # database.
        # < 2.6 Incompatible >
        # self.assertListEqual(
        #    self.BlogPost.objects(id=self.post1.id)[0].comments, []
        # )
        self.assertEqual(
            self.BlogPost.objects(id=self.post1.id)[0].comments, []
        )

        # Ensure that post1 comments were deleted from the list.
        # < 2.6 Incompatible >
        # self.assertListEqual(self.post1.comments, [])
        self.assertEqual(self.post1.comments, [])

        # Ensure that comments still returned a EmbeddedDocumentList object.
        # < 2.6 Incompatible >
        # self.assertIsInstance(self.post1.comments, EmbeddedDocumentList)
        self.assertTrue(isinstance(self.post1.comments, EmbeddedDocumentList))

        # Ensure that the delete method returned 2 as the number of entries
        # deleted from the database
        self.assertEqual(number, 2)

    def test_empty_list_embedded_documents_with_unique_field(self):
        """
        Tests that only one document with an empty list of embedded documents
        that have a unique field can be saved, but if the unique field is
        also sparse than multiple documents with an empty list can be saved.
        """
        class EmbeddedWithUnique(EmbeddedDocument):
            number = IntField(unique=True)

        class A(Document):
            my_list = ListField(EmbeddedDocumentField(EmbeddedWithUnique))

        A(my_list=[]).save()
        self.assertRaises(NotUniqueError, lambda: A(my_list=[]).save())

        class EmbeddedWithSparseUnique(EmbeddedDocument):
            number = IntField(unique=True, sparse=True)

        class B(Document):
            my_list = ListField(EmbeddedDocumentField(EmbeddedWithSparseUnique))

        B(my_list=[]).save()
        B(my_list=[]).save()

    def test_filtered_delete(self):
        """
        Tests the delete method of a List of Embedded Documents
        after the filter method has been called.
        """
        comment = self.post1.comments[1]
        number = self.post1.comments.filter(author='user2').delete()
        self.post1.save()

        # Ensure that only the user2 comment was deleted.
        # < 2.6 Incompatible >
        # self.assertNotIn(
        #     comment, self.BlogPost.objects(id=self.post1.id)[0].comments
        # )
        self.assertTrue(
            comment not in self.BlogPost.objects(id=self.post1.id)[0].comments
        )
        self.assertEqual(
            len(self.BlogPost.objects(id=self.post1.id)[0].comments), 1
        )

        # Ensure that the user2 comment no longer exists in the list.
        # < 2.6 Incompatible >
        # self.assertNotIn(comment, self.post1.comments)
        self.assertTrue(comment not in self.post1.comments)
        self.assertEqual(len(self.post1.comments), 1)

        # Ensure that the delete method returned 1 as the number of entries
        # deleted from the database
        self.assertEqual(number, 1)

    def test_custom_data(self):
        """
        Tests that custom data is saved in the field object
        and doesn't interfere with the rest of field functionalities.
        """
        custom_data = {'a': 'a_value', 'b': [1, 2]}

        class CustomData(Document):
            a_field = IntField()
            c_field = IntField(custom_data=custom_data)

        a1 = CustomData(a_field=1, c_field=2).save()
        self.assertEqual(2, a1.c_field)
        self.assertFalse(hasattr(a1.c_field, 'custom_data'))
        self.assertTrue(hasattr(CustomData.c_field, 'custom_data'))
        self.assertEqual(custom_data['a'], CustomData.c_field.custom_data['a'])


if __name__ == '__main__':
    unittest.main()
