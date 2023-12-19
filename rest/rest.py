import json
import logging
import re
import signal
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep

import mysql.connector

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)

URL_TOKEN = r'[a-zA-Z0-9_-]+'

class DBHandler:
	def __init__(self) -> None:
		while True:
			try:
				self._db = mysql.connector.connect(host='host.docker.internal', user='root', password='MyPass123', port=33061)
			except mysql.connector.errors.Error:
				logging.warning('DB connection failed, retrying after 1 second...')
				sleep(1)
			else:
				self.cursor = self._db.cursor()
				self.cursor.execute('USE booksdb')
				break

	def get_books(self, *, book_name: str | None = None, user_name: str | None = None) -> list[dict]:
		if book_name and user_name:
			self.cursor.execute(
				'SELECT BookName, BookDescription FROM UserBooks JOIN Books USING (BookName) WHERE UserName = %s AND BookName = %s', (user_name, book_name))
		elif book_name:
			self.cursor.execute('SELECT * FROM Books WHERE BookName = %s', (book_name,))
		elif user_name:
			self.cursor.execute(
				'SELECT BookName, BookDescription FROM UserBooks JOIN Books USING (BookName) WHERE UserName = %s', (user_name,))
		else:
			self.cursor.execute('SELECT * FROM Books')

		cols = self.cursor.column_names
		return [dict(zip(cols, row)) for row in self.cursor]

	def add_book(self, book_name: str, book_description: str, user_name: str | None = None) -> None:
		try:
			self.cursor.execute('INSERT INTO Books VALUES (%s, %s)', (book_name, book_description))
		except mysql.connector.errors.Error:
			if not user_name:
				raise


		if user_name:
			self.cursor.execute(
				'INSERT INTO UserBooks VALUES (%s, %s)', (user_name, book_name))

	def close(self):
		self.cursor.close()
		self._db.commit()
		self._db.close()


class WebRequestHandler(BaseHTTPRequestHandler):
	db_handler = DBHandler()

	def log_message(self, format, *args):
		return	

	def do_HEAD(self):
		logging.info('Received HEAD request')

		self.send_response(200)
		self.send_header('Content-Type', 'application/json')
		self.end_headers()

	def do_GET(self):
		logging.info('Received GET request')

		if m := re.fullmatch(f'/users/({URL_TOKEN})/books/({URL_TOKEN})/?', self.path):
			user_name, book_name, = m.groups()

			if books := self.db_handler.get_books(user_name=user_name, book_name=book_name):
				self.send_response(200)
				self.send_header('Content-Type', 'application/json')
				self.end_headers()
				self.wfile.write(json.dumps(books[0]).encode())
			else:
				self.send_error(404)

		elif m := re.fullmatch(f'/users/({URL_TOKEN})/books/?', self.path):
			user_name, = m.groups()
			self.send_response(200)
			self.send_header('Content-Type', 'application/json')
			self.end_headers()
			books = self.db_handler.get_books(user_name=user_name)
			self.wfile.write(json.dumps(books).encode())

		elif re.fullmatch(f'/books/?', self.path):
			self.send_response(200)
			self.send_header('Content-Type', 'application/json')
			self.end_headers()
			books = self.db_handler.get_books()
			self.wfile.write(json.dumps(books).encode())

		elif m := re.fullmatch(f'/books/({URL_TOKEN})/?', self.path):
			book_name, = m.groups()

			if books := self.db_handler.get_books(book_name=book_name):
				self.send_response(200)
				self.send_header('Content-Type', 'application/json')
				self.end_headers()
				self.wfile.write(json.dumps(books[0]).encode())
			else:
				self.send_error(404)

		else:
			self.send_error(400)

	def do_POST(self):
		if m := re.fullmatch(f'/books/({URL_TOKEN})/?', self.path):
			book_name, = m.groups()

			self.db_handler.add_book(book_name, '')
			self.send_response(201)
			self.send_header('Content-Type', 'application/json')
			self.end_headers()
			books = self.db_handler.get_books(book_name=book_name)
			self.wfile.write(json.dumps(books[0]).encode())

		elif m := re.fullmatch(f'/users/({URL_TOKEN})/books/({URL_TOKEN})/?', self.path):
			user_name, book_name, = m.groups()

			self.db_handler.add_book(book_name, '', user_name=user_name)
			self.send_response(201)
			self.send_header('Content-Type', 'application/json')
			self.end_headers()
			books = self.db_handler.get_books(user_name=user_name, book_name=book_name)
			self.wfile.write(json.dumps(books[0]).encode())

		else:
			self.send_error(400)


if __name__ == '__main__':
	addr = ('0.0.0.0', 8001)
	server = HTTPServer(addr, WebRequestHandler)
	logging.info(f'Serving on {addr}')

	signal.signal(signal.SIGTERM, lambda *_: exec('raise KeyboardInterrupt'))

	try:
		server.serve_forever()
	except KeyboardInterrupt:
		logging.info('Exitting gracefully...')
	finally:
		WebRequestHandler.db_handler.close()
