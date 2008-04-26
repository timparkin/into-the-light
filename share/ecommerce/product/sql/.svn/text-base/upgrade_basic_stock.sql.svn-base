begin;

alter table basic_stock drop constraint basic_stock_pkey;

alter table basic_stock add column option_code text;

update basic_stock set option_code = '';

alter table basic_stock add constraint basic_stock_pkey primary key (product_id, option_code);


commit;
