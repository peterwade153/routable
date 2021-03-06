# routable

### DESCRIPTION
Django REST API powering routable.

The API is Built with Python 3.7, Django 3.0 and Django Rest Framework 3.11 and a SQLite Database.

### Installation
Assuming python is already installed.

1. Create a virtual env and activate it with the commands below.

```
python3 -m venv env

cd env && source bin/activate

```
2. Clone the application and change directory to routable with the commands below

```
git clone https://github.com/peterwade153/routable.git

cd routable

```

3. To Install application dependencies

```
pip install -r requirements.txt
```

4. To run migrations

```
make migrate
```
OR
```
python3 manage.py migrate
```

5. To Create a super user with credentials to access admin pages. 
```
make superuser
```
OR
```
python3 manage.py createsuperuser
```


6. To start Application
```
make start
```
OR
```
python3 manage.py runserver
```
The application can be accessed at `http://localhost:8000/` with the endpoints, as described below.

An API client like POSTMAN can be used to perform the actions below.


### Endpoints
Below are the available Endpoints and sample json payloads.

They are accessed by appending them to the base_url i.e (`http://localhost:8000/api/items` to create an item.).

The Endpoints with `uuid` in the url. Replace it with the actual generated item id.

The `Content-Type` should be set to `application/json`. 

Request | Endpoints             |       Functionality 
--------|-----------------------|--------------------------------
POST    |  `/items `            |  Creates a new Item. `payload` -	`{"amount" : 1234}`
POST    |  `/items/transaction` |  Creates a new Transaction. `payload` - `{"item":  "c5470044-a61d-4019-99ed-4c1d0dff793f", "status": "processing", "location": "origination_bank"}`  
PUT     |  `/items/move/uuid/`  |  Move Item. 
PUT     |  `/items/error/uuid/` |  Error Item transaction to error state.
PUT     |  `/items/fix/uuid/`   |  Fix Item with transaction in error state.


### Admin Pages
To access Admin pages visit http://localhost:8000/admin/

