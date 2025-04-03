# FED Database

## Overview
The FED Database is a data management pipeline for FED data, combining the power of Python/Django for backend operations with the flexibility of Vue.js for a responsive frontend experience. This document outlines the setup steps for both Django and Vue.js to get your FED Database environment up and running

## Prerequisites
Before you begin, ensure you have the following installed:
- Python (3.8 or later)
- Node.js (14.x or later)
- npm (6.x or later)
- MySQL or MariaDB
- Git

## Setup

### MySQL/MariaDB Database Setup

1. **Install MySQL or MariaDB**
   - Follow the installation instructions for your specific operating system.
   - [MySQL Download](https://dev.mysql.com/downloads/mysql/)
   - [MariaDB Download](https://mariadb.org/download/)

2. **Create a New Database**
   - Open your database management tool (like MySQL Workbench or phpMyAdmin).
   - Create a new database for the project, e.g., `fed_database`.

3. **Configure Database Settings in Django**
   - Navigate to your Django project's `settings.py`.
   - Update the `DATABASES` setting to use your MySQL/MariaDB database.
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.mysql',
             'NAME': 'fed_database',
             'USER': 'your_database_user',
             'PASSWORD': 'your_database_password',
             'HOST': 'localhost',
             'PORT': '3306',
         }
     }
     ```

### Django Backend Setup

1. **Clone the Repository**
   - `git clone https://github.com/mwblab/fed_database.git`
   - `cd fed_database`

2. **Set Up a Virtual Environment** 
   - `bash install.sh`
   - `source django-vue/bin/activate`

3. **Install django dependency** 
   - install pip from https://pip.pypa.io/en/stable/installation/ 
   - `python -m pip install django;`
   - `pip install django-extensions`
   - `pip install djangorestframework`
   - `pip install pymysql`
   - `pip install django-cors-headers`
   - `pip install mysqlclient`

4. **Initialize Database**
   - `cd django-vue`
   - `python manage.py makemigrations`
   - `python manage.py migrate`

5. **Run the Backend Server**
   - `python3 manage.py runserver 0.0.0.0:3000`

### Vue.js Frontend Setup

1. **Navigate to the Frontend Directory**
   - `cd frontend`

2. **Install Node Modules**
   - `npm install webpack-dev-server`
   - `npm install --save xlsx`
   - `npm install` 

3. **Update backend IP
   - `cd config`
   - `node update_backend_config.js`
   - type backend IP in the prompt

4. **Run the Vue.js Frontend Server**
   - Edit port and host IP in config/index.js file.
   - run server
   - `npm run dev`

## Usage

To use FED Database, navigate to `http://host_IP:port` in your web browser.

## Contributing
Contributions to FED Database are welcome! 


