from pydantic import BaseModel

import plotly.graph_objects as go
# import plotly.express as px
from plotly.subplots import make_subplots

import numpy as np


class Plotter(BaseModel):


    def get_soc_timeseries(self, df_soc, df_status):


        vehicle_ids = list(df_soc.columns)[1:]
        n_vehicles = len(vehicle_ids)

        n_plots = len(vehicle_ids)
        subplot_titles = ['vehicle: ' + str(id) for id in vehicle_ids]

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
            rows= 2*(n_vehicles),
            # rows=n_vehicles,
            cols=1,
            subplot_titles=subplot_titles
        )

        for idx, vehicle_id in enumerate(vehicle_ids, start=0):

            fig.add_trace(
                go.Scatter(
                    x=df_soc['datetime'],
                    y=df_soc[vehicle_id],
                    hovertemplate= '%{x}</i>: SOC:%{y:.2f}'
                ),
                    row=idx+1,
                    col=1
            )


            fig.add_trace(
               go.Bar(
                   x=df_status['datetime'],
                   y=np.ones(shape=len(df_status['datetime'])),
                   marker={'color':  df_status[idx].map(lambda x: set_color(x))},
                   hovertemplate=df_status[idx],
                   opacity=0.2
               ),
                row= idx + 1,
                col=1
            )

        fig.update_xaxes(
            dtick='H1',
            tickformat='Day:%d %H:%M'
            )

        fig.update_yaxes(
            tickformat=',.0%',
            range= [0, 1.05]
        )

        fig.update_layout(
            yaxis_title='(%) SOC at Depot',
            legend_title_text='vehicle_id'
        )

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