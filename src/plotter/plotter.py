from pydantic import BaseModel

import plotly.graph_objects as go
# import plotly.express as px
from plotly.subplots import make_subplots

import numpy as np


class Plotter(BaseModel):


    def get_soc_timeseries(self, df_soc, df_status, dictionary_of_assigned_reservations):

        res_assignments = dictionary_of_assigned_reservations
        vehicle_ids = list(df_soc.columns)[1:]
        n_vehicles = len(vehicle_ids)

        n_plots = len(vehicle_ids)
        subplot_titles = []
        for id in vehicle_ids:
            subplot_titles.append('vehicle: ' + str(id) + '<br> (%) SOC')
            subplot_titles.append('reservations')

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
            rows= 2*(n_vehicles), # (overlayed) 1 for soc, 1 for status, (new row) 1 for assigned reservations
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

        row_placement = -1
        for plot_num, vehicle_id in enumerate(vehicle_ids, start=0):
            row_placement += 2

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
                    hover_values = [
                                'created <br>' + str(res.created_at_timestamp_utc),
                                'assigned <br>' + str(res.assigned_at_timestamp_utc),
                                'requested_departure <br>' + str(res.departure_timestamp_utc)
                                ]
                    text_values = ['created', 'assigned', 'departure']
                    fig.add_trace(
                        go.Scatter(
                            mode='markers+text',
                            x=[
                                res.created_at_timestamp_utc,
                                res.assigned_at_timestamp_utc,
                                res.departure_timestamp_utc
                               ],
                            y=np.ones(shape=3),
                            hovertemplate=hover_values,
                            text=text_values,
                            textposition=['top left', 'middle center', 'bottom right'],
                            # hovertemplate= '%{x}</i>: :%{y:.2f}'
                        ),
                            row=row_placement+1,
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






        # fig = px.line(dataframe, x="datetime", y=dataframe.columns,
        #               hover_data={"datetime": "|%B %d, %Y %I:%M:%S"},
        #               title='SOC at Depot',
        #               width=1400, height=600)
        # fig.update_xaxes(
        #     dtick='H1',
        #     tickformat='%d %H:%M'
        #     )

        # fig.update_yaxes(
        #     tickformat= ',.0%',
        #     range= [0, 1.05]
        # )

        # fig.update_layout(
        #     yaxis_title='(%) SOC at Depot',
        #     legend_title_text='vehicle_id'
        # )

        # fig = go.Figure(
        #     data=[go.Bar(y=[2, 1, 3])],
        #     layout_title_text="A Figure Displayed with fig.show()"
        # )
        return fig


    # def get_reservation_completion(self, dataframe):