
drop table registered_user;

create table registered_user (
    id          bigint not null,
    version     bigint not null,
    first_name  text,
    surname     text,
    optin       text,
    email       text,

    foreign key (id, version) references item(id, version) on delete cascade
);


