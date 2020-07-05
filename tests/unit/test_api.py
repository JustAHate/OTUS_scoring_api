import pytest
from scoring_api import api
from datetime import datetime, timedelta


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, True, ''),
        (True, True, []),
        (True, True, 'spam'),
        (False, False, None),
        (False, False, 'eggs'),
        (True, False, 'spam'),
        (False, True, None),
        (False, True, ''),
        (False, True, ()),
        (False, True, 'eggs'),
        (True, False, [1, 2, 3]),
        (True, True, {'spam': 'eggs'}),
        (True, True, 42),
    )
)
def test_field_ok(required, nullable, value):
    class TestField:
        field = api.Field(required=required, nullable=nullable)
    obj = TestField()
    obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, False, None),
        (True, True, None),
        (False, False, ()),
        (True, False, ''),
        (False, False, ''),
        (True, False, []),
        (False, False, []),
        (True, False, {}),
        (False, False, {})
    )
)
def test_field_bad(required, nullable, value):
    class TestField:
        field = api.Field(required=required, nullable=nullable)
    obj = TestField()
    with pytest.raises(api.ValidationError):
        obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, True, ''),
        (True, False, 'spam'),
        (False, True, ''),
        (False, True, 'eggs'),
        (False, False, 'spam')
    )
)
def test_charfield_ok(required, nullable, value):
    class TestField:
        field = api.CharField(required=required, nullable=nullable)
    obj = TestField()
    obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, False, ''),
        (True, False, None),
        (False, True, 42),
        (False, True, {'spam': 'eggs'}),
        (False, True, [1, 2, 3])
    )
)
def test_charfield_bad(required, nullable, value):
    class TestField:
        field = api.CharField(required=required, nullable=nullable)
    obj = TestField()
    with pytest.raises(api.ValidationError):
        obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, True, {'spam': 'eggs'}),
        (False, True, {}),
        (True, True, {}),
        (False, True, None)
    )
)
def test_argumentsfield_ok(required, nullable, value):
    class TestField:
        field = api.ArgumentsField(required=required, nullable=nullable)
    obj = TestField()
    obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, False, {}),
        (True, False, None),
        (True, False, 'spam'),
        (True, False, 42),
        (True, False, [1, 2, 3]),
    )
)
def test_argumentsfield_bad(required, nullable, value):
    class TestField:
        field = api.ArgumentsField(required=required, nullable=nullable)
    obj = TestField()
    with pytest.raises(api.ValidationError):
        obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, False, 'example@email.com'),
        (True, True, ''),
        (False, False, None)
    )
)
def test_emailfield_ok(required, nullable, value):
    class TestField:
        field = api.EmailField(required=required, nullable=nullable)
    obj = TestField()
    obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, False, 'spam'),
        (True, False, ''),
        (True, False, 42),
        (True, False, {}),
        (True, False, (1, 2, 3))
    )
)
def test_emailfield_bad(required, nullable, value):
    class TestField:
        field = api.EmailField(required=required, nullable=nullable)
    obj = TestField()
    with pytest.raises(api.ValidationError):
        obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, True, '71234567890'),
        (True, True, ''),
        (False, True, None)
    )
)
def test_phonefield_ok(required, nullable, value):
    class TestField:
        field = api.PhoneField(required=required, nullable=nullable)
    obj = TestField()
    obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, True, None),
        (True, True, 'spam'),
        (True, True, {'spam': 'eggs'}),
        (True, True, [1, 2, 3]),
        (True, True, 42),
        (True, False, '')
    )
)
def test_phonefield_bad(required, nullable, value):
    class TestField:
        field = api.PhoneField(required=required, nullable=nullable)
    obj = TestField()
    with pytest.raises(api.ValidationError):
        obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, False, '01.01.1990'),
        (True, True, ''),
        (False, True, None)
    )
)
def test_datefield_ok(required, nullable, value):
    class TestField:
        field = api.DateField(required=required, nullable=nullable)
    obj = TestField()
    obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, False, ''),
        (True, True, None),
        (True, True, 'spam'),
        (True, True, {'spam': 'eggs'}),
        (True, True, [1, 2, 3]),
        (True, True, 42),
    )
)
def test_datefield_bad(required, nullable, value):
    class TestField:
        field = api.DateField(required=required, nullable=nullable)
    obj = TestField()
    with pytest.raises(api.ValidationError):
        obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (
            True,
            False,
            (datetime.now() - timedelta(days=70 * 365.25)).strftime('%d.%m.%Y')
        ),
        (True, True, ''),
        (False, True, None)
    )
)
def test_birthdayfield_ok(required, nullable, value):
    class TestField:
        field = api.BirthDayField(required=required, nullable=nullable)
    obj = TestField()
    obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, False, ''),
        (True, True, None),
        (True, True, 'spam'),
        (True, True, {'spam': 'eggs'}),
        (True, True, [1, 2, 3]),
        (True, True, 42),
        (
            True,
            False,
            (datetime.now() - timedelta(days=70 * 365.25 + 1)).strftime('%d.%m.%Y')
        ),
        (
            True,
            False,
            (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
        )
    )
)
def test_birthdayfield_bad(required, nullable, value):
    class TestField:
        field = api.BirthDayField(required=required, nullable=nullable)
    obj = TestField()
    with pytest.raises(api.ValidationError):
        obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, False, 0),
        (True, True, 1),
        (False, True, 2),
        (False, True, '')
    )
)
def test_gender_field_ok(required, nullable, value):
    class TestField:
        field = api.GenderField(required=required, nullable=nullable)
    obj = TestField()
    obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, False, ''),
        (True, True, 3),
        (False, True, -1),
        (True, True, None)
    )
)
def test_gender_field_bad(required, nullable, value):
    class TestField:
        field = api.GenderField(required=required, nullable=nullable)
    obj = TestField()
    with pytest.raises(api.ValidationError):
        obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, True, []),
        (True, False, [1, 2, 3]),
        (False, True, None),
    )
)
def test_clientids_field_ok(required, nullable, value):
    class TestField:
        field = api.ClientIDsField(required=required, nullable=nullable)
    obj = TestField()
    obj.field = value


@pytest.mark.parametrize(
    ('required', 'nullable', 'value'), (
        (True, True, None),
        (True, False, []),
        (False, True, (1, 2, 3)),
        (False, True, [1, 2, '3']),
        (False, True, {'spam': 'eggs'}),
        (False, True, 'spam'),
    )
)
def test_clientids_field_bad(required, nullable, value):
    class TestField:
        field = api.ClientIDsField(required=required, nullable=nullable)
    obj = TestField()
    with pytest.raises(api.ValidationError):
        obj.field = value
