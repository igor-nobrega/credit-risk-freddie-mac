{# Faixas usadas na EDA. O prefixo "a ", "b "... garante a ordem correta ao ordenar; "z missing" fica por ultimo. #}
{% macro fico_band(col) -%}
case when {{ col }} is null then 'z missing' when {{ col }} < 620 then 'a <620' when {{ col }} < 660 then 'b 620-659'
     when {{ col }} < 700 then 'c 660-699' when {{ col }} < 740 then 'd 700-739' when {{ col }} < 780 then 'e 740-779'
     else 'f >=780' end
{%- endmacro %}

{% macro ltv_band(col) -%}
case when {{ col }} is null then 'z missing' when {{ col }} <= 60 then 'a <=60' when {{ col }} <= 70 then 'b 61-70'
     when {{ col }} <= 80 then 'c 71-80' when {{ col }} <= 90 then 'd 81-90' when {{ col }} <= 95 then 'e 91-95'
     else 'f >95' end
{%- endmacro %}

{% macro dti_band(col) -%}
case when {{ col }} is null then 'z missing' when {{ col }} <= 20 then 'a <=20' when {{ col }} <= 30 then 'b 21-30'
     when {{ col }} <= 40 then 'c 31-40' when {{ col }} <= 45 then 'd 41-45' when {{ col }} <= 50 then 'e 46-50'
     else 'f >50' end
{%- endmacro %}

{% macro rate_band(col) -%}
case when {{ col }} is null then 'z missing' when {{ col }} < 3 then 'a <3' when {{ col }} < 4 then 'b 3-3.99'
     when {{ col }} < 5 then 'c 4-4.99' when {{ col }} < 6 then 'd 5-5.99' when {{ col }} < 7 then 'e 6-6.99'
     else 'f >=7' end
{%- endmacro %}

{% macro upb_band(col) -%}
case when {{ col }} is null then 'z missing' when {{ col }} < 100000 then 'a <100k' when {{ col }} < 200000 then 'b 100-199k'
     when {{ col }} < 300000 then 'c 200-299k' when {{ col }} < 500000 then 'd 300-499k' else 'e >=500k' end
{%- endmacro %}

{% macro mi_band(col) -%}
case when {{ col }} is null then 'z missing' when {{ col }} = 0 then 'a 0' when {{ col }} <= 20 then 'b 1-20'
     when {{ col }} <= 30 then 'c 21-30' else 'd >30' end
{%- endmacro %}

{% macro cat(col) -%}coalesce(cast({{ col }} as varchar), 'missing'){%- endmacro %}

{% macro era(col) -%}
case when {{ col }} <= 2003 then '1999-2003' when {{ col }} <= 2008 then '2004-2008' when {{ col }} <= 2011 then '2009-2011'
     when {{ col }} <= 2017 then '2012-2017' when {{ col }} <= 2021 then '2018-2021' else '2022-2023' end
{%- endmacro %}
