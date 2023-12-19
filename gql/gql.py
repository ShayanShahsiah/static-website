import json
import re
from base64 import b64decode
from collections import namedtuple
from contextlib import suppress
from time import sleep

import ariadne
import ariadne.asgi
import mysql.connector
import requests
from graphql import GraphQLResolveInfo

type_defs = ariadne.load_schema_from_path('schema.graphql')

User = namedtuple('User', 'username password')
Book = namedtuple('Book', 'name description')
UserBook = namedtuple('UserBook', 'user_name book_name')

REST_HOST = 'http://host.docker.internal:8002'
SAFE_TOKEN = r'[a-zA-Z0-9_-]+'

class DBHandler:
	def __init__(self) -> None:
		while True:
			try:
				self._db = mysql.connector.connect(host='host.docker.internal', user='root', password='MyPass123', port=33061)
			except mysql.connector.errors.Error:
				print('DB connection failed, retrying after 1 second...')
				sleep(1)
			else:
				self.cursor = self._db.cursor()
				self.cursor.execute('USE usersdb')
				break

		# Wait until REST server is up and running
		while True:
			try:
				requests.head(f'{REST_HOST}/books')
			except OSError:
				print('REST connection failed, retrying after 1 second...')	
				sleep(1)
			else:
				break

	def get_users(self) -> list[User]:
		self.cursor.execute('SELECT * FROM Users')
		return [User(username, password) for username, password in self.cursor]

	def get_books(self, *, book_name: str | None = None, user_name: str | None = None) -> list[Book]:
		if book_name:
			if not re.match(SAFE_TOKEN, book_name):
				return []

			resp = requests.get(f'{REST_HOST}/books/{book_name}')

		elif user_name:
			if not re.match(SAFE_TOKEN, user_name):
				return []

			resp = requests.get(f'{REST_HOST}/users/{user_name}/books')

		else:
			resp = requests.get(f'{REST_HOST}/books')

		book_list = json.loads(resp.text)
		return [Book(book_dict['BookName'], book_dict['BookDescription']) for book_dict in book_list]

	def get_password(self, user: str) -> str | None:
		self.cursor.execute('SELECT UserPassword FROM Users WHERE UserName = %s', (user,))
		try:
			(password,), = self.cursor
			return password # type: ignore
		except ValueError:
			return None


db_handler = DBHandler()

def parse_user_pass(val: str | None) -> tuple[str, str] | None:
	if not val:
		return None

	try:
		auth_type, encoded = val.split()
	except ValueError:
		return None

	if auth_type != 'Basic':
		return None

	try:
		username, password = b64decode(encoded).decode().split(':')
	except ValueError:
		return None

	return username, password

def has_authorization(auth: str, username: str) -> bool:
	"""
	Determines whether the user with `auth` credentials is authorized to access/modify resources belonging to `username`	
	"""
	if p := parse_user_pass(auth):
		auth_username, password = p
		authed = password == db_handler.get_password(username)
		return authed and auth_username in (username, 'root')
	
	return False


query = ariadne.QueryType()

@query.field('users')
def resolve_users(_, info: GraphQLResolveInfo) -> list[User]:
	auth = info.context['request'].headers.get('authorization')
	if has_authorization(auth, 'root'):
		return db_handler.get_users()

	return []

@query.field('books')
def resolve_books(_, info: GraphQLResolveInfo) -> list[Book]:
	return db_handler.get_books()

@query.field('userBooks')
def resolve_user_books(_, info: GraphQLResolveInfo, username: str) -> list[Book]:
	auth = info.context['request'].headers.get('authorization')
	
	if has_authorization(auth, username):
		return db_handler.get_books(user_name=username)
	
	return []

mutation = ariadne.MutationType()

@mutation.field('addBook')
def resolve_addBook(_, info: GraphQLResolveInfo, name: str, username: str | None = None) -> bool:
	auth = info.context['request'].headers.get('authorization')
	if username and has_authorization(auth, username):
		with suppress(OSError):
			resp = requests.post(f'{REST_HOST}/users/{username}/books/{name}')
			resp.raise_for_status()
			return True

	elif not username and has_authorization(auth, 'root'):
		with suppress(OSError):
			resp = requests.post(f'{REST_HOST}/books/{name}')
			resp.raise_for_status()
			return True

	return False


schema = ariadne.make_executable_schema(type_defs, [query, mutation])
app = ariadne.asgi.GraphQL(schema, debug=True)