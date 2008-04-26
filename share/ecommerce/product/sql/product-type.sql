create table product (
    id bigint not null,
    version bigint not null,
    title text not null,
    code text not null,
    show boolean not null,
    available boolean not null,
    categories ltree[],
    foreign key (id, version) references item(id, version) on delete cascade
);
