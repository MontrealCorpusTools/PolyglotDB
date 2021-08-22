from polyglotdb import CorpusContext
from polyglotdb.query.base.func import Average, Count, Min, Max, InterquartileRange, Stdev, Sum, Median, Quantile


def test_query_aggregate_count(timed_config):
    with CorpusContext(timed_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa').count()
        assert (q == 3)


def test_query_duration_aggregate_average(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        result = q.aggregate(Average(g.phone.duration))
        assert (abs(result - 0.08) < 0.001)


def test_query_duration_aggregate_average_group_by(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label.in_(['aa', 'ae']))
        q = q.order_by(g.phone.label)
        results = q.group_by(g.phone.label.column_name('label')).aggregate(Average(g.phone.duration))

        assert (len(results) == 2)
        assert (results[0]['label'] == 'aa')
        assert (abs(results[0]['average_duration'] - 0.08) < 0.001)

        assert (results[1]['label'] == 'ae')
        assert (abs(results[1]['average_duration'] - 0.193) < 0.001)


def test_query_count_group_by(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label.in_(['aa', 'ae']))
        q = q.order_by(g.phone.label)
        results = q.group_by(g.phone.label.column_name('label')).aggregate(Count())
        assert (len(results) == 2)
        print(results)
        assert (results[0]['label'] == 'aa')
        assert (results[0]['count_all'] == 3)

        assert (results[1]['label'] == 'ae')
        assert (results[1]['count_all'] == 7)


def test_min(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone)
        result = q.aggregate(Min(g.phone.duration))
        print(result)
        assert (abs(result - 0.0165) < 0.0001)


def test_max(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone)
        result = q.aggregate(Max(g.phone.duration))
        print(result)
        assert (abs(result - 0.7141982077865059) < 0.0001)


def test_iqr(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone)
        result = q.aggregate(InterquartileRange(g.phone.duration))
        print(result)
        assert (abs(result - 0.06985377627008615) < 0.001)  # Differences in output between this and R are greater


def test_stdev(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone)
        result = q.aggregate(Stdev(g.phone.duration))
        print(result)
        assert (abs(result - 0.09919653455576248) < 0.0001)


def test_sum(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone)
        result = q.aggregate(Sum(g.phone.duration))
        print(result)
        assert (abs(result - 19.810184959164687) < 0.0001)


def test_median(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone)
        result = q.aggregate(Median(g.phone.duration))
        print(result)
        assert (abs(result - 0.07206877027163117) < 0.0001)


def test_quantile(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone)
        result = q.aggregate(Quantile(g.phone.duration, 0.4))
        print(result)
        assert (abs(result - 0.06135379031168853) < 0.0001)
