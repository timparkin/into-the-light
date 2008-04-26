
drop sequence voucher_definition_id_seq;
drop sequence voucher_id_seq;

drop table voucher;
drop table voucher_definition;


create sequence voucher_definition_id_seq;

create table voucher_definition (
    voucher_definition_id   bigint primary key,
    code                    text not null,
    count                   integer,
    multiuse                bool,
    start_date              date,
    end_date                date,
    amount                  text not null,

    unique (code)
);

create sequence voucher_id_seq;

create table voucher (
    voucher_id              bigint,
    voucher_definition_id   bigint,
    code                    text primary key,
    used                    timestamp,
    previous_used           timestamp,

    foreign key (voucher_definition_id) references voucher_definition(voucher_definition_id) on delete cascade
);
