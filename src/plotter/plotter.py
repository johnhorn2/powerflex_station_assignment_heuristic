import pandas as pd
from pydantic import BaseModel

import plotly.graph_objects as go
from plotly.graph_objects import Figure
from plotly.subplots import make_subplots

import numpy as np


class Plotter(BaseModel):


    def get_soc_timeseries(self, df_soc, df_status, dictionary_of_assigned_reservations, dictionary_of_assigned_stations, station_fleet):

        res_assignments = dictionary_of_assigned_reservations
        vehicle_ids = list(df_soc.columns)[1:]
        n_vehicles = len(vehicle_ids)

        n_plots = len(vehicle_ids)
        subplot_titles = []
        for id in vehicle_ids:
            subplot_titles.append('vehicle: ' + str(id) + '<br> (%) SOC')
            # subplot_titles.append('reservations')

        # set colors per status
        def set_color(status):
            if (status == 'driving'):
                return "blue"
            elif (status == 'charging'):
                return "green"
            elif (status == 'parked'):
                return "grey"
            elif (status == 'finished_charging'):
                return "yellow"
            elif (status == 'NA'):
                return "white"

        # we have n_vehicles SOC time series
        # as well as n_vehicles status bars below each timeseries
        fig = make_subplots(
            rows= 1*(n_vehicles), # (overlayed) 1 for soc, 1 for status, (new row) 1 for assigned reservations
            # rows=n_vehicles,
            cols=1,
            subplot_titles=subplot_titles,
            shared_xaxes=True
        )

        # fig.add_trace(go.Scatter(
        #     x=[0, 1, 2],
        #     y=[2, 2, 2],
        #     mode="markers+text",
        #     name="Markers and Text",
        #     text=["Text D", "Text E", "Text F"],
        #     textposition="bottom center"
        # ))

        row_placement = 0
        for plot_num, vehicle_id in enumerate(vehicle_ids, start=0):
            row_placement += 1

            fig.add_trace(
                go.Scatter(
                    x=df_soc['datetime'],
                    y=df_soc[vehicle_id],
                    hovertemplate= '%{x}</i>: SOC:%{y:.2f}'
                ),
                    row=row_placement,
                    col=1
            )

            # if plot_num == 0:
            #     axis_num = ''
            # else:
            #     axis_num = str(plot_num)
            #
            # second_axis_num = str(plot_num + 1)

            # fig['layout']['xaxis' + axis_num]['title'] = 'Label x-axis 1'
            # fig['layout']['yaxis' + axis_num]['title'] = '(%) SOC'


            fig.add_trace(
               go.Bar(
                   x=df_status['datetime'],
                   y=np.ones(shape=len(df_status['datetime'])),
                   marker={'color':  df_status[plot_num].map(lambda x: set_color(x))},
                   hovertemplate=df_status[plot_num],
                   opacity=0.2
               ),
                row=row_placement,
                col=1
            )

            # plot timeline of every reservation per vehicle
            # todo: mark cancelled reservations by modifying res object to have a status: 'created' | 'cancelled'

            # assumes the vehicle had a reservation assigned to it
            try:
                for res in dictionary_of_assigned_reservations[vehicle_id]:
                    # regular reservations
                    if res.walk_in == False:
                        hover_values = [
                                    'created <br>' + str(res.created_at_timestamp_utc),
                                    'assigned <br>' + str(res.assigned_at_timestamp_utc),
                                    'requested_departure <br>' + str(res.departure_timestamp_utc),
                                    'reservation id <br>' + str(res.id[0:5]),
                                    ]
                        text_values = [
                            res.id[0:5] + ' created',
                            res.id[0:5] + ' assigned',
                            res.id[0:5] + ' departure',
                            res.id[0:5] + ' arrival'
                        ]
                    elif res.walk_in == True:
                        hover_values = [
                            'walk-in <br>' + str(res.created_at_timestamp_utc),
                            'walk-in assigned <br>' + str(res.assigned_at_timestamp_utc),
                            'walk-in departure <br>' + str(res.departure_timestamp_utc)
                        ]
                        text_values = ['walk-in', 'walk-in assigned', 'walk-in departure']




                    fig.add_trace(
                        go.Scatter(
                            mode='markers+text',
                            x=[
                                res.created_at_timestamp_utc,
                                res.assigned_at_timestamp_utc,
                                res.departure_timestamp_utc,
                                res.arrival_timestamp_utc,
                               ],
                            y=[1, 0.8, 0.6, 0.4], #np.ones(shape=4),
                            hovertemplate=hover_values,
                            text=text_values,
                            textposition=['top left', 'middle center', 'bottom right'],
                            # hovertemplate= '%{x}</i>: :%{y:.2f}'
                        ),
                            row=row_placement,
                            col=1
                    )

                    # fig['layout']['yaxis' + second_axis_num]['title'] = 'reservation'
            # vehicle never had a reservation assigned to it
            except KeyError:
                pass


            # assumes the vehicle had a reservation assigned to it
            try:
                for vehicle in dictionary_of_assigned_stations[vehicle_id]:
                    # regular reservations
                    evse_type = str(station_fleet.stations[vehicle.connected_station_id].type)
                    hover_values = [
                                'request sent: ' + str(vehicle.updated_at) + '<br> type: ' + evse_type
                                ]
                    text_values = [evse_type]

                    fig.add_trace(
                        go.Scatter(
                            mode='text',
                            x=[
                                vehicle.updated_at
                               ],
                            # we want the points to take the lower half of the plot as the top half already has reservations
                            y=[0.2],
                            hovertemplate=hover_values,
                            text=text_values,
                            textposition=['middle center'],
                            # hovertemplate= '%{x}</i>: :%{y:.2f}'
                        ),
                            row=row_placement,
                            col=1
                    )

                    # fig['layout']['yaxis' + second_axis_num]['title'] = 'reservation'
            # vehicle never had a reservation assigned to it
            except KeyError:
                pass


        fig.update_xaxes(
            dtick='H1',
            tickformat='Day:%d %H:%M'
            )

        fig.update_yaxes(
            tickformat=',.0%',
            range= [0, 1.4]
        )

        # fig.update_layout(
        #     yaxis_title='(%) SOC at Depot',
        #     legend_title_text='vehicle_id'
        # )

        fig.update_layout(height=n_plots*200, title_text="Vehicle (%) SOC Over Time")
        return fig


    # def get_reservation_completion(self, dataframe):

    @classmethod
    def get_x_y_z(cls, df_results: pd.DataFrame, z_field_name: str) -> (np.ndarray, np.ndarray, np.ndarray):
        # Prep Z for Heuristic
        ev_cnt_ordered_list = sorted(df_results.vehicles.unique())
        evse_cnt_ordered_list = sorted(df_results.l2_station.unique())

        evse_dim = len(evse_cnt_ordered_list)
        ev_dim = len(ev_cnt_ordered_list)
        new_shape = (evse_dim, ev_dim)

        # ---------------------------------------

        z = np.ones(new_shape)

        for evse_idx in range(0,evse_dim):
            for ev_idx in range(0, ev_dim):
                evse_val = evse_cnt_ordered_list[evse_idx]
                ev_val = ev_cnt_ordered_list[ev_idx]

                # z_val = df_results[(df_results['l2_station'] == evse_val) & (df_results['vehicles'] == ev_val)].pct_late.values
                z_val = df_results[(df_results['l2_station'] == evse_val) & (df_results['vehicles'] == ev_val)][z_field_name].values
                z[evse_idx,ev_idx]= z_val

        x = evse_cnt_ordered_list
        y = ev_cnt_ordered_list

        z = z.transpose()

        return x, y ,z


    @classmethod
    def get_hourly_power_bar_chart_bldg(cls, df_bldg: pd.DataFrame, bldg_type, sqft, county) -> Figure:

        fig = go.Figure(data=[
            go.Bar(x=df_bldg["hour"], y=df_bldg['total_kwh'])
            ],
        )

        fig.update_layout(scene = dict(
            xaxis_title='Hour of Day',
            yaxis_title='Building Power (kW)',
            # width=700,
            # margin=dict(r=20, b=10, l=10, t=10),
            )
        )

        fig.update_layout(
            title={'y':0.9,
                   'yanchor': 'top'
                   }
        )

        fig.update_layout(
            title='Building Hourly Power (kW) <br> Building Type: {bldg_type} | SQFT: {sqft} | County: {county}'.format(
                bldg_type=bldg_type,
                sqft=sqft,
                county=county
            ),
            xaxis_tickfont_size=14,
            yaxis=dict(
                title='BLDG Max Hourly Power (kW)',
                titlefont_size=16,
                tickfont_size=14,
            ),
            xaxis=dict(
                title='Hour of the Day',
                titlefont_size=16,
                tickfont_size=14,
            ),
            legend=dict(
                x=0,
                y=1.0,
                bgcolor='rgba(255, 255, 255, 0)',
                bordercolor='rgba(255, 255, 255, 0)'
            ),
            barmode='group',
            bargap=0.15,  # gap between bars of adjacent location coordinates.
            bargroupgap=0.1  # gap between bars of the same location coordinate.
        )

        return fig

    @classmethod
    def get_hourly_power_bar_chart(cls, df_results: pd.DataFrame, random_sort: bool, n_dcfc: int, l2_station: int, vehicles: int) -> Figure:

        df_filtered = df_results[
            (df_results['n_dcfc'] == n_dcfc) & \
            (df_results['l2_station'] == l2_station) & \
            (df_results['random_sort'] == random_sort) & \
            (df_results['vehicles'] == vehicles)
            ]


        fig = go.Figure(data=[
            go.Bar(x=df_filtered["hour"], y=df_filtered['max_hourly_power_kw'])
            ],
        )

        fig.update_layout(scene = dict(
            xaxis_title='Hour of Day',
            yaxis_title='EVSE Power (kW)',
            # width=700,
            # margin=dict(r=20, b=10, l=10, t=10),
            )
        )

        fig.update_layout(
            title={'y':0.9,
                   'yanchor': 'top'
                   }
        )

        fig.update_layout(
            title='EVSE Hourly Power (kW) <br> {l2_station} L2 EVSEs | {n_dcfc} DCFCs | {vehicles} EVs'.format(
                l2_station=l2_station,
                n_dcfc=n_dcfc,
                vehicles=vehicles
            ),
            xaxis_tickfont_size=14,
            yaxis=dict(
                title='EVSE Max Hourly Power (kW)',
                titlefont_size=16,
                tickfont_size=14,
            ),
            xaxis=dict(
                title='Hour of the Day',
                titlefont_size=16,
                tickfont_size=14,
            ),
            legend=dict(
                x=0,
                y=1.0,
                bgcolor='rgba(255, 255, 255, 0)',
                bordercolor='rgba(255, 255, 255, 0)'
            ),
            barmode='group',
            bargap=0.15,  # gap between bars of adjacent location coordinates.
            bargroupgap=0.1  # gap between bars of the same location coordinate.
        )

        return fig
    @classmethod
    def get_power_3d_surface_figure(cls, df_results: pd.DataFrame) -> Figure:

        x, y, z = cls.get_x_y_z(df_results, 'max_power')

        fig = go.Figure(data=[
            go.Surface(z=z, x=x, y=y, opacity=1.0,
                       hovertemplate = "EVSE cnt: %{x}" + "<br>EV cnt: %{y}" + "<br>%{z} Max Power Draw"),
        ],

        )
        fig.update_layout(title='Peak Power Draw (kW)',autosize=True,
                          width=500, height=500,
                          margin=dict(l=65, r=50, b=65, t=90),
                          )
        fig.update_layout(scene = dict(
            xaxis_title='# EVSE',
            yaxis_title='# EV',
            zaxis_title='Peak Power Draw (kw)'),
            width=700,
            margin=dict(r=20, b=10, l=10, t=10),
        )

        fig.update_layout(
            title={'y':0.9,
                   'yanchor': 'top'
                   }
        )

        return fig, x, y ,z


    @classmethod
    def get_kpi_3d_surface_figure(cls, df_results: pd.DataFrame) -> Figure:

        x, y, z = cls.get_x_y_z(df_results, 'pct_late')

        z = z / 100.0

        fig = go.Figure(data=[
            go.Surface(z=z, x=x, y=y, opacity=1.0,
                       hovertemplate = "EVSE cnt: %{x}" + "<br>EV cnt: %{y}" + "<br>%{z:.2f}% Late Departures"),
        ],

        )
        fig.update_layout(title='Percent Hour Late',autosize=True,
                          width=500, height=500,
                          margin=dict(l=65, r=50, b=65, t=90),
                          )
        fig.update_layout(scene = dict(
            xaxis_title='# EVSE',
            yaxis_title='# EV',
            zaxis_title='Pct Hour Late'),
            width=700,
            margin=dict(r=20, b=10, l=10, t=10),
        )

        fig.update_layout(scene = dict (
            zaxis = dict(
                range=[0,1],
                tickformat='.1%'
                         )
        )

        )

        fig.update_layout(
            title={'y':0.9,
                   'yanchor': 'top'
                   }
        )

        return fig
