from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import (
    UserAttributeSimilarityValidator,
    NumericPasswordValidator,
    CommonPasswordValidator
)

class CustomMinimumLengthValidator:
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _('パスワードは最低 %(min_length)d 文字以上である必要があります。'),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return _('パスワードは最低 %(min_length)d 文字以上である必要があります。') % {'min_length': self.min_length}

class CustomUserAttributeSimilarityValidator(UserAttributeSimilarityValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            raise ValidationError(_('あなたの個人情報と似ているパスワードにはできません。'))

    def get_help_text(self):
        return _('あなたの個人情報と似ているパスワードにはできません。')

class CustomCommonPasswordValidator(CommonPasswordValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            raise ValidationError(_('よく使われるパスワードにはできません。'))

    def get_help_text(self):
        return _('よく使われるパスワードにはできません。')

class CustomNumericPasswordValidator(NumericPasswordValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            raise ValidationError(_('数字だけのパスワードにはできません。'))

    def get_help_text(self):
        return _('数字だけのパスワードにはできません。')
