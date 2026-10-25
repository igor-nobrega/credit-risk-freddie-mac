{% test unique_combination(model, columns) %}
{# Falha para cada combinacao de colunas que aparece mais de uma vez. #}
select {{ columns | join(', ') }}, count(*) as n_rows
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
