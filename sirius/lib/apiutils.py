#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""


class ApiException(Exception):
    """Исключение в API-функции
    :ivar code: HTTP-код ответа и соответствующий код в метаданных
    :ivar message: текстовое пояснение ошибки
    """
    def __init__(self, code, message, **kwargs):
        self.code = code
        self.message = message
        self.extra = kwargs

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        if not self.extra:
            return u'<ApiException(%s, u\'%s\')>' % (self.code, self.message)
        else:
            return u'<ApiException(%s, u\'%s\', %s)' % (
                self.code,
                self.message,
                u', '.join(u'%s=%r' % (k, v) for k, v in self.extra.iteritems())
            )
