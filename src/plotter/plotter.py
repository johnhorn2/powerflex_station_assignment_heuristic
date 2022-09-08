from pydantic import BaseModel

# import plotly.graph_objects as go
import plotly.express as px

class Plotter(BaseModel):


    def get_soc_timeseries(self, dataframe):
        fig = px.line(dataframe, x="datetime", y=dataframe.columns,
                      hover_data={"datetime": "|%B %d, %Y %I:%M:%S"},
                      title='SOC at Depot',
                      width=1400, height=600)
        fig.update_xaxes(
            dtick="M1",
            tickformat="%b\n%Y",
            )

        fig.update_yaxes(
            tickformat= ',.0%',
            range= [0, 1]
        )

        # fig = go.Figure(
        #     data=[go.Bar(y=[2, 1, 3])],
        #     layout_title_text="A Figure Displayed with fig.show()"
        # )
        return fig