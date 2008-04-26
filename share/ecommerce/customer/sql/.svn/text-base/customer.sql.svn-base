
drop table crm_data;
drop table customer;

create table customer (
    id bigint not null,
    version bigint not null,
    last_name text not null,
    first_name text not null,
    email text not null,
    primary key (id, version),
    unique (email),
    foreign key (id, version) references item(id, version) on delete cascade
);

create table crm_data (
    id bigint not null,
    version bigint default 1 not null,

    key   text not null,
    value text not null,

    foreign key (id, version) references customer(id, version) on delete cascade
);

