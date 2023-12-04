from django.db import models

class CommaSeparatedCharField(models.CharField):
    description = "A comma-separated list of values."

    def from_db_value(self, value, expression, connection):
        if value is None:
            return []
        return value.split(", ")

    def to_python(self, value):
        if isinstance(value, list):
            return value
        if value is None:
            return []
        return [item.strip() for item in value.split(",")]

    def get_prep_value(self, value):
        if not value:
            return ""
        return ", ".join(value)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)
