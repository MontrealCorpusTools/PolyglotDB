
def generate_withs(query, all_withs):
    statements = [withs_to_string(all_withs)]
    for c in query._criterion:
        for a in c.attributes:
            if a.with_alias not in all_withs:
                statement = a.annotation.subquery(all_withs)
                statements.append(statement)

                all_withs.update(a.with_aliases)
    for a in query._columns + query._group_by + query._additional_columns:
        if a.with_alias not in all_withs:
            statement = a.annotation.subquery(all_withs)
            statements.append(statement)

            all_withs.update(a.with_aliases)
    for agg in query._aggregate:
        if agg.collapsing:
            continue
        a = agg.attribute
        if a.with_alias not in all_withs:
            statement = a.annotation.subquery(all_withs)
            statements.append(statement)

            all_withs.update(a.with_aliases)
    return '\n'.join(statements)

def withs_to_string(withs):
    return 'WITH ' + ', '.join(withs)
