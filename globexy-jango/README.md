# Развёртывание проекта на локальной машине

## Установка интерпретатора Python

Брать [здесь](https://www.python.org/downloads/release/python-352/) - последняя на момент написания. Если будет будет более новая версия, то и её можно. В начале установки выбрать добавление в пути.

После установки собственно интерпретатора, открыть "Командную строку" и выполнить `pip install virtualenv`. Так же, можно, но не обязательно, обновить сам `pip`: `python -m pip install --upgrade pip`.

## Установка Redis

Качать [отсюда](https://github.com/MSOpenTech/redis/releases). Качаете, ставите. Для локальной работы настройки по умолчанию вполне годятся, ставится как сервис и сразу запускается.

## Развёртывание сайта

1. Клонировать репозиторий `git@gitlab.0070.ru:andrey.henneberg/globexy-web.git`.
2. Открыть "Командную строку".
3. Перейти в директорию проекта.
4. `virtualenv.exe --prompt=[globexy-web] env`
5. `env\Scripts\activate.bat`
6. `pip install --index-url=http://pypi.python.org/simple/ --trusted-host pypi.python.org --upgrade -r requirements.txt`

    **NB:** *Ключи `--index-url=http://pypi.python.org/simple/` и `--trusted-host pypi.python.org` обязательны для обхода системы безопасности.*

7. Скопировать `globexy/settings_local.py.sample` в `globexy/settings_local.py`, раскоментировать настройки Redis, добавить настроек по вкусу.
8. `manage.py migrate`
9. `manage.py createsuperuser`

    Пароль надо выбирать не самый тупой, потому что с какой-то версии встроили проверку на тупые пароли.

10. `manage.py runserver`
11. PROFIT

## Интерфейс

[Интерфейс](http://gitlab.0070.ru/walek/HolyBomb) собран на Polymer, поэтому устанавливается в соседнюю директорию отдельным проектом, Инструкция в самом проекте. Настроить надо только расположение этого проекта, задав в файле `globexy/settings_local.py` путь до собранной версии: 

```
POLYMER_GUI = '../HolyBomb/build'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    POLYMER_GUI,
]
```

Для установки инструментов для сборки интерфейса использовать ключи `--ca=null --strict-ssl=false` для обхода системы безопасности.

# Работа с пользователем

## Аутентификация на сайте

Аутентификация производится отправкой формы по адресу /user/login методом POST. Ответ будет содержать JSON. В случае удачной аутентификации - `{"status": "success"}`, в случае ошибки - `{"status": "fail", "errors": error_object}`. `error_object` может быть строкой, содержащей сообщение об ошибке, или объектом со списком полей формы, для которых есть сообщения об ошибке.

## Выход из системы

Выход осуществляется GET-запросом на адрес /user/logout. При удачном завершении, в ответе будет `{"status": "success"}`, при неудачном `{'status': 'fail', 'errors': "сообщение об ошибке"}`.

## Запрос статуса пользователя

При GET-запросе на адрес /user/status сайт в ответе приходит JSON-объект с параметрами текущего пользователя. Для не аутентифицированного пользователя это будет

```
{
    'authenticated': False,
    'user': {
        'as_user_id': None,
        'username': '',
        'email': None,
        'phone': None,
        'first_name': None,
        'last_name': None
    }
}
```
Для аутентифицированного -

```
{
    "authenticated": True,
    "user": {
        "as_user_id': "57c526fa3e255093a6ee710d",
        "username": "user_name",
        "email': "user@email.com",
        "phone': "+1346578912",
        "first_name': "Firstname",
        "last_name': "Lastname"
    }
}
```
