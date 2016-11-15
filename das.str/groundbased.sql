DROP TABLE stations CASCADE;
DROP TABLE products CASCADE;
DROP TABLE measurements CASCADE;

CREATE TABLE "stations"(
	"id" serial NOT NULL PRIMARY KEY, 
	"name" varchar(255) NOT NULL, 
	"latitude" numeric,
	"longitude" numeric,
	"height" numeric,
	UNIQUE (id)
); 

CREATE TABLE "products"(
	"id" serial NOT NULL PRIMARY KEY,
	"product" varchar(255) NOT NULL
);

CREATE TABLE "measurements"(
	"id" serial NOT NULL PRIMARY KEY,
	"stations_id" integer references stations (id),
	"observation_time_start" Timestamp with time zone,
	"observation_time_end" Timestamp with time zone,
	"observed_field"  integer references products (id),
	"value" numeric
);


INSERT INTO products (product) VALUES('Ozone');
INSERT INTO products (product) VALUES('NO2');
INSERT INTO products (product) VALUES('Aerosol');
INSERT INTO products (product) VALUES('SO2');
INSERT INTO products (product) VALUES('Temperature');
INSERT INTO products (product) VALUES('GHG');
INSERT INTO products (product) VALUES('Reactive Gases');
INSERT INTO products (product) VALUES('Pressure');
INSERT INTO products (product) VALUES('Humidity');
INSERT INTO products (product) VALUES('Rainfall Rate');
