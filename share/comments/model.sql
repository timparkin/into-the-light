create table comment (

    id bigint not null,
    version bigint not null,
    relates_to_id bigint not null,
    relates_to_version bigint not null,
    posted timestamp with time zone not null,
    approved boolean not null,
    
    foreign key (id, version) references item(id, version) on delete cascade,
    foreign key (relates_to_id, relates_to_version) references item(id, version) on delete cascade
);
create rule poop_cleanup as on delete to comment do
    delete from item where id=old.id and version=old.version;


---<ADDUSERNAME> grant select, insert, update, delete on comment to <USERNAME>;

