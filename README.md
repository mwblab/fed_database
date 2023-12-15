# Fed Database


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

if add table, update auto/models.py

`python manage.py makemigrations`

`python manage.py migrate`

## create data migration

# https://docs.djangoproject.com/en/4.1/howto/initial-data/

`python manage.py makemigrations --empty auto`


## reset tables

`python ../manage.py runscript reset_data`

https://django-extensions.readthedocs.io/en/latest/runscript.html

## access db web

http://128.173.224.170:8080/
Server: 0.0.0.0
Username: automiceuser
Database: automicedb

20230830 update: remove adminer docker version and run the adminer on nginx server

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


# restart docker

sudo systemctl restart snap.docker.dockerd.service



# install adminer naive version

https://www.vultr.com/docs/how-to-install-adminer-on-ubuntu-20-04/

php8.1-fpm
https://portal.databasemart.com/kb/a2136/how-to-install-php-8_1-for-nginx-on-ubuntu-20_04.aspx


