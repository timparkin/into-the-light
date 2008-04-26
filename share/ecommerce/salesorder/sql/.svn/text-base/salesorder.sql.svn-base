
drop sequence sales_order_id_seq;
drop sequence sales_order_item_id_seq;
drop table sales_order_item;
drop table sales_order;

create sequence sales_order_id_seq ;

create table sales_order (
    sales_order_id          bigint,
    order_num               text,

    status                  text,

    create_date             timestamp,
    processed_date          timestamp,

    total_price             numeric,

    -- weak reference to the customer
    customer_id             bigint,
    customer_version        bigint,

    customer_first_name     text,
    customer_last_name      text,
    customer_address        text,
    customer_postcode       text,
    customer_country        text,
    customer_phone_number   text,
    customer_email          text,

    payment_reference       text,

    delivery_name           text,
    delivery_address        text,
    delivery_postcode       text,
    delivery_country        text,

    primary key (sales_order_id)
);

create sequence sales_order_item_id_seq ;

create table sales_order_item (

    sales_order_item_id bigint,
    sales_order_id      bigint,

    code                text,
    description         text not null,

    quantity_ordered    int not null,
    quantity_dispatched int,

    unit_price          numeric not null,
    total_price         numeric not null,

    -- weak reference to the item
    item_id             bigint,
    item_version        bigint,

    primary key (sales_order_item_id),
    foreign key (sales_order_id) references sales_order(sales_order_id) on delete cascade
);

