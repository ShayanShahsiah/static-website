CREATE DATABASE usersdb;
CREATE DATABASE booksdb;

USE usersdb;

CREATE TABLE Users (
	UserName varchar(50) PRIMARY KEY,
	UserPassword varchar(50) NOT NULL
);

INSERT INTO Users VALUES ('root', '1234');
INSERT INTO Users VALUES ('John', '1234');
INSERT INTO Users VALUES ('Jack', '1234');
INSERT INTO Users VALUES ('Jane', '1234');
INSERT INTO Users VALUES ('Joe', '1234');

USE booksdb;

CREATE TABLE Books (
	BookName varchar(50) PRIMARY KEY,
	BookDescription varchar(500)
);

CREATE TABLE UserBooks (
	UserName varchar(50),
	BookName varchar(50),
	PRIMARY KEY (UserName, BookName)
);

INSERT INTO Books (BookName, BookDescription) VALUES ('Book1', 'Some desciption on Book1');
INSERT INTO Books (BookName, BookDescription) VALUES ('Book2', 'Some desciption on Book2');
INSERT INTO Books (BookName, BookDescription) VALUES ('Book3', 'Some desciption on Book3');
INSERT INTO Books (BookName, BookDescription) VALUES ('Book4', 'Some desciption on Book4');
 
INSERT INTO UserBooks VALUES ('John', 'Book1');
INSERT INTO UserBooks VALUES ('John', 'Book3');
INSERT INTO UserBooks VALUES ('Jack', 'Book2');
INSERT INTO UserBooks VALUES ('Jane', 'Book4');
