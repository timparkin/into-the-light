drop table basic_stock ;

create table basic_stock (
    product_id      bigint,
    product_version bigint default 1,

    option_code     text,

    in_stock        int default 0 not null,

    foreign key (product_id, product_version) references item(id, version) on delete cascade,
    primary key (product_id, option_code)
);
