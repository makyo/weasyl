"""
Test suite for: resetpassword.py::def reset(form):
"""
import pytest
import bcrypt
import arrow

from weasyl.test import db_utils
from weasyl import resetpassword, login
from weasyl import define as d
from weasyl.error import WeasylError


class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)


def test_passwordMismatch_WeasylError_if_supplied_passwords_dont_match():
    user_name = "testReset0001"
    email_addr = "test_reset@weasyl.com"
    db_utils.create_user(email_addr=email_addr, username=user_name)
    token = "testtokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentest000002"
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=token,
               password='qwe', passcheck='asd')
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form)
    assert 'passwordMismatch' in str(err)


def test_passwordInsecure_WeasylError_if_password_length_insufficient():
    user_name = "testReset0002"
    email_addr = "test_reset@weasyl.com"
    db_utils.create_user(email_addr=email_addr, username=user_name)
    token = "testtokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentest000003"
    password = ''
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=token,
               password=password, passcheck=password)
    # Considered insecure...
    for i in range(0, login._PASSWORD):
        with pytest.raises(WeasylError) as err:
            resetpassword.reset(form)
        assert 'passwordInsecure' in str(err)
        password += 'a'
        form.password = password
        form.passcheck = password
    # Considered secure...
    password += 'a'
    form.password = password
    form.passcheck = password
    # Success at WeasylError/forgotpasswordRecordMissing; we didn't make one yet
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form)
    assert 'forgotpasswordRecordMissing' in str(err)


def test_forgotpasswordRecordMissing_WeasylError_if_reset_record_not_found():
    user_name = "testReset0003"
    email_addr = "test_reset@weasyl.com"
    db_utils.create_user(email_addr=email_addr, username=user_name)
    token = "testtokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentest000004"
    password = '01234567890123'
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=token,
               password=password, passcheck=password)
    # Technically we did this in the above test, but for completeness, target it alone
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form)
    assert 'forgotpasswordRecordMissing' in str(err)


def test_emailIncorrect_WeasylError_if_email_address_doesnt_match_stored_email():
    # Two parts: Set forgot password record; attempt reset with incorrect email
    #  Requirement: Get token set from request()
    user_name = "testReset0004"
    email_addr = "test_reset@weasyl.com"
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
                           month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError):
        resetpassword.request(form_for_request)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    # Force update link_time (required)
    resetpassword.prepare(pw_reset_token)
    email_addr_mismatch = "invalid-email@weasyl.com"
    form_for_reset = Bag(email=email_addr_mismatch, username=user_name, day=arrow.now().day,
                         month=arrow.now().month, year=arrow.now().year, token=pw_reset_token,
                         password=password, passcheck=password)
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form_for_reset)
    assert 'emailIncorrect' in str(err)


def test_emailIncorrect_WeasylError_if_username_doesnt_match_stored_username():
    # Two parts: Set forgot password record; attempt reset with incorrect username
    #  Requirement: Get token set from request()
    user_name = "testReset0005"
    email_addr = "test_reset@weasyl.com"
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
                           month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError):
        resetpassword.request(form_for_request)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    # Force update link_time (required)
    resetpassword.prepare(pw_reset_token)
    user_name_mismatch = "nottheaccountname123"
    form_for_reset = Bag(email=email_addr, username=user_name_mismatch, day=arrow.now().day,
                         month=arrow.now().month, year=arrow.now().year, token=pw_reset_token,
                         password=password, passcheck=password)
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form_for_reset)
    assert 'usernameIncorrect' in str(err)


def test_password_reset_fails_if_attempted_from_different_ip_address():
    # Two parts: Set forgot password record; attempt reset with incorrect IP Address in forgotpassword table vs. requesting IP
    #  Requirement: Get token set from request()
    user_name = "testReset0006"
    email_addr = "test_reset@weasyl.com"
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
                           month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError):
        resetpassword.request(form_for_request)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    # Change IP detected when request was made (required for test)
    d.engine.execute("UPDATE forgotpassword SET address = %(addr)s WHERE token = %(token)s",
                     addr="127.42.42.42", token=pw_reset_token)
    # Force update link_time (required)
    resetpassword.prepare(pw_reset_token)
    form_for_reset = Bag(email=email_addr, username=user_name, day=arrow.now().day,
                         month=arrow.now().month, year=arrow.now().year, token=pw_reset_token,
                         password=password, passcheck=password)
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form_for_reset)
    assert 'addressInvalid' in str(err)


def test_verify_success_if_correct_information_supplied():
    # Subtests:
    #  a) Verify 'authbcrypt' table has new hash
    #  b) Verify 'forgotpassword' row is removed.
    #  > Requirement: Get token set from request()
    user_name = "testReset0007"
    email_addr = "test_reset@weasyl.com"
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
                           month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError):
        resetpassword.request(form_for_request)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    # Force update link_time (required)
    resetpassword.prepare(pw_reset_token)
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=pw_reset_token,
               password=password, passcheck=password)
    resetpassword.reset(form)
    # 'forgotpassword' row should not exist after a successful reset
    row_does_not_exist = d.engine.execute("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    assert row_does_not_exist.first() is None
    bcrypt_hash = d.engine.scalar("SELECT hashsum FROM authbcrypt WHERE userid = %(id)s", id=user_id)
    assert bcrypt.checkpw(password.encode('utf-8'), bcrypt_hash.encode('utf-8'))
