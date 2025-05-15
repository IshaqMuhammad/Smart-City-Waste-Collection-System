create table city (
	city_ID SERIAL primary key,
	city_name VARCHAR(10) not null,
	city_latitude DOUBLE precision not null check (city_latitude between -90 and 90),
	City_longitude DOUBLE precision not null check (city_longitude between -180 and 180)
);

create table location (
	location_ID SERIAL primary key,
	city_ID Int,
	location_name VARCHAR(10) not null,
	location_latitude DOUBLE precision not null check (location_latitude between -90 and 90),
	location_longitude DOUBLE precision not null check (location_longitude between -180 and 180),
	foreign key (city_ID) references city(city_ID) ON DELETE CASCADE
);

create table pre_avaliable_map (
	map_ID serial primary key,
	map_name VARCHAR(10) not null unique,
	map_latitude DOUBLE precision not null check (map_latitude between -90 and 90),
	map_longitude DOUBLE precision not null check (map_longitude between -180 and 180)
);

select * from pre_avaliable_map;

drop 