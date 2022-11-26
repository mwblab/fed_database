# automice


## run dev RESTful server

`python manage.py runserver 0.0.0.0:3000`

available port: 3000, 5000
3000 for RESTful, 5000 for vue

## run vue dev server

`cd frontend`

`npm run dev`

run on port 5000

you can update host, port in frontend/config/index.js 

## django dev

`cd django-vue`

`source ./bin/activate`

`python manage.py migrate`

`python manage.py runserver`

## create migration

`python manage.py makemigrations`

`python manage.py migrate`

## create data migration

# https://docs.djangoproject.com/en/4.1/howto/initial-data/

`python manage.py makemigrations --empty auto`



