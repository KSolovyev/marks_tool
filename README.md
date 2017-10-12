

# Скриптик для автоматической простановки оценок в ведомости park.mail.ru

Если вы хоть раз делали это на протяжении семестра, у вас не возникнет вопроса "зачем?"

## Настройка среды
1. Для работы нужен python 2.7. Обычно он установлен по умолчанию, но если нет:
https://www.python.org/download/releases/2.7/

2. Дальше ставим virtualenv
https://virtualenv.pypa.io/en/stable/installation/

3. Устанавливаем зависимости. В папке проекта выполнить
`pip install -r requirements.txt`

Среда готова


## Выставляем параметры
1. Здесь понадобиться браузер chrome, YA.bro или аналог с инструментами разработчика. Включаем вкладку с сетевыми вызовами.

2. Идем на park.mail.ru, открываем Личный кабинет и ищим вызов на `https://park.mail.ru/rest_api/discipline_versions/<DISCIPLINE>/students/`.
Он может отображаться, как просто `/students/`. Тогда на него надо кликнуть и посмотреть подробности.
Запоминаем цифру DISCIPLINE из адреса, она нам еще понадобится. 

3. Щелкаем правой кнопкой на этом вызове и нажимаем Copy -> Copy Request Headers и вставляем в любимый текстовый редактор.
 
4. Из заголовков нам понадобятся два параметра из Cookie. `csrf_token` и `sessionid_gtp`. 
Копируем их и запоминаем

## Таблица с оценками
Предлагается использовать файл в одном из двух форматов: JSON и CSV:
```json
{
  "Иванов Пупк":[25, 13],
  "Сергеев Илья":[25,2,4]
}
```
или
```text
Иванов Пупк,25,22
Сергеев Илья,25,2,4
```

Соответственно первая оценка попадет в первую колонку на портале, вторая - во вторую, и т.д.



## Запуск
`marks.py --csrf <csrf_token> --cookie <sessionid_gtp> --discipline <DISCIPLINE> FILE`

здесь FILE - json или csv файл с оценками. 

больше параметров можно узнать через marks.py --help

Если в конце написало, что 
```
All marks were successfully set
```
То оценки должны появится на портале
