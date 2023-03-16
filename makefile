build:
	poetry build

install:
	poetry install

start:
	# poetry run example
	# poetry run flask --app example --debug run
	poetry run gunicorn --workers=4 --bind=127.0.0.1:5000 example:app
