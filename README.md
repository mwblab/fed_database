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

access website

`http://128.173.224.170:5000/#/`

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




# Dev issue

## Cannot read properties of undefined: 

https://github.com/Belphemur/vue-json-csv/issues/170
use vue-json-csv 1.2.12


## date picker

https://www.npmjs.com/package/vue2-datepicker


## bootstrap vue

https://bootstrap-vue.org/docs

## import python code

https://iq-inc.com/importerror-attempted-relative-import/

## async

https://javascript.info/async-await

https://www.letswrite.tw/promise-async-await/

## file uploader

https://medium.com/js-dojo/how-to-build-a-file-manager-storage-web-app-with-django-rest-framework-and-vue-js-e89a83318e9c

https://safrazik.github.io/vue-file-agent/

https://github.com/safrazik/vue-file-agent#advanced-usage

## csv downloader

https://belphemur.github.io/vue-json-csv/

https://www.npmjs.com/package/vue-json-csv

## vue awesome

https://github.com/vuejs/awesome-vue#csv

## fetch, sample

https://jasonwatmore.com/post/2022/06/09/vue-fetch-http-put-request-examples

https://blog.logrocket.com/how-to-build-vue-js-app-django-rest-framework/#setting-up-vuejs-client-app


# tbd

reset db, print progress frontend, don't dup hr,day,rolling (db cal running flag), atomic roll back, study cohort UI, cal day progress table

check 00, 01 data and date incorrect csv

