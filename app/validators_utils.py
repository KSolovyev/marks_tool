from voluptuous import Schema, Invalid


class Sequence(object):
    def __init__(self, validator):
        self.validator = Schema(validator)

    def __call__(self, v):
        if not isinstance(v, (list, tuple)):
            raise Invalid(u"Expected list or tuple, but have {value}".format(value=v))
        try:
            result = []
            for value in v:
                result.append(self.validator(value))
            return result
        except Invalid as e:
            raise Invalid(u"Raised an exception on line {v} : {ex}".format(v=v, ex=unicode(e)))
