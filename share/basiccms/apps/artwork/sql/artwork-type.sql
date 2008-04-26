drop table artwork;

create table artwork (
    id bigint not null,
    version bigint not null,
    title text not null,
    show boolean not null,
    available boolean not null,
    categories ltree[],
    foreign key (id, version) references item(id, version) on delete cascade
);
