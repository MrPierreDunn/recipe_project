from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import (MAX_EMAIL_LENGTH, MAX_FNAME_LENGTH, MAX_LNAME_LENGTH,
                        MAX_ROLE_LENGTH, MAX_USERNAME_LENGTH)
from .validators import validate_username_uniqueness

USER = 'user'
ADMIN = 'admin'
USER_ROLE = [
    ('user', USER),
    ('admin', ADMIN),
]


class MyUser(AbstractUser):
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=[validate_username_uniqueness],
        verbose_name='Имя пользователя',
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        verbose_name='Адрес электронной почты'
    )
    first_name = models.CharField(
        max_length=MAX_FNAME_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LNAME_LENGTH,
        verbose_name='Фамилия'
    )
    role = models.CharField(
        max_length=MAX_ROLE_LENGTH,
        choices=USER_ROLE,
        default='user',
        verbose_name='Роль пользователя'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        db_table = 'custom_user'
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=('username', 'email'), name='unique_username_email'
            )
        ]

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        MyUser,
        related_name='sub_user',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        MyUser,
        related_name='sub_author',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    subscribe_date = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True,
    )

    class Meta:
        db_table = 'subscription'
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'), name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='user_cant_follow_himself'
            ),
        ]

    def __str__(self):
        return f'Пользователь {self.user} подписался на {self.author}'
