import pandas as pd
import sqlite3


def get_departure_kpis(late_minute_threshold: int) -> pd.DataFrame:
    con = sqlite3.connect('test.db')
    sql = """
        with aggs as
        (
            select
                random_sort,
                n_dcfc,
                vehicles,
                l2_station,
                CAST(count(1) AS REAL) as total_cnt,
                CAST(
                    sum(
                        case when departure_deltas >= {late_minute_threshold}
                        then 1
                        else 0
                        end
                    ) AS REAL)
                     as late_cnt
                    
        from
            late_departures
        group by
            1, 2, 3, 4
        ) 
        select 
            random_sort,
            n_dcfc,
            vehicles,
            l2_station,
            100.0*(late_cnt / total_cnt) as pct_late
        from aggs;
        """
    sql_formatted = sql.format(late_minute_threshold=late_minute_threshold)
    df = pd.read_sql_query(sql_formatted, con)

    return df


def get_power_stats() -> pd.DataFrame:
    con = sqlite3.connect('test.db')
    sql = """
        select 
            n_dcfc,
            random_sort,
            l2_station,
            vehicles,
            max_power,
            min_power,
            avg_power
        from 
            power_stats
    """
    df = pd.read_sql_query(sql, con)

    return df

