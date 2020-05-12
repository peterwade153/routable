start:
	python3 manage.py runserver

migrations:
	python3 manage.py makemigrations

migrate:
	python3 manage.py migrate

test:
	python3 manage.py test

superuser:
	python3 manage.py createsuperuser