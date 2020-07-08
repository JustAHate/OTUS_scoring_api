import pytest
from scoring_api import scoring
from scoring_api import store


@pytest.fixture()
def get_store():
    return store.Store('127.0.0.1', 6379, 5)


@pytest.mark.parametrize(
    ('phone', 'email', 'birthday', 'gender', 'first_name', 'last_name', 'return_value'), (
        ('71234567890', 'example@email.com', '10.10.2000', 1, 'Ivan', 'Ivanov', 5.0),
        (71234567890, '', '10.10.2000', 0, '', 'Ivanov', 1.5),
        (71234567890, '', '', 0, '', 'Ivanov', 1.5),
        (None, None, '10.10.2000', 1, 'Ivan', 'Ivanov', 2.0),
        ('', '', None, None, None, None, 0),
    )
)
def test_get_score(phone, email, birthday, gender, first_name, last_name, return_value, get_store):
    score = scoring.get_score(get_store, phone, email, birthday, gender, first_name, last_name)
    assert score == return_value


def test_get_interests_ok(get_store):
    with pytest.raises(store.StoreAccessException):
        interests = scoring.get_interests(get_store, 'spam')
        assert interests == []


def test_get_interests_bad():
    with pytest.raises(AttributeError):
        scoring.get_interests(None, 'spam')

