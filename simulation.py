import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
# streamlit run C:\Users\User\Documents\GitHub\master_thesis_202425\simulation.py
import First_class


note = {"USA": "Knoxville, Tennessee",
        "USA_info": "Value taken for the city of Knoxville, Tennessee",
        "USA_temp_ref": "https://www.visualcrossing.com/weather/weather-data-services/knoxville/metric/2023-01-01/"
                        "2023-12-31#",
        "USA_heat": 21394.18,
        "USA_heat_ref": "https://experience.arcgis.com/experience/cbf6875974554a74823232f84f563253?src=%E2%80%B9%"
                        "20Consumption%20%20%20%20%20%20Residential%20Energy%20Consumption%20Survey%20(RECS)-b2",
        "Germany": "Weimar, Thuringia",
        "Germany_info": "Value taken for the city of Weimar, Thuringia",
        "Germany_temp_ref": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/"
                            "air_temperature/historical/",
        "Germany_heat": 12216,
        "Germany_heat_ref": "https://www.destatis.de/EN/Themes/Society-Environment/Environment/Environmental-"
                            "Economic-Accounting/private-households/Tables/energy-heating-households.html",
        }

st.title('Test Test Test')
if "my_instance" not in st.session_state:
    st.session_state.my_instance = First_class.MyClass()
    st.button("Run load page !")

else:
    Class = st.session_state.my_instance

    st.header("Location of the DC")
    country_name = st.selectbox(
        "DC country location",
        ("USA", "Germany"),
    )
    st.write(note[country_name+"_info"])
    st.link_button("Link to the hourly 2023 outdoor temperature",
                   note[country_name+"_temp_ref"])
    Class.country_chose(country_name)

    st.header("Specification of the DC")
    surface = st.number_input("Insert the surface area of the DC (m2)", value=2500)
    heat_losses = st.number_input("Insert the heat losses par surface area (kW/m2)", value=15)
    Class.set_dc_cara(surface, heat_losses)
    st.write(Class.Q, 'kW of heat realised by the DC and going to the heat network')

    st.header("Specification of the heat network")
    Heated_temp = st.slider("Heated water minimum temperature (°C)", 20, 40, 30)
    Class.set_heated_water_temp(Heated_temp)
    if st.checkbox("add minimum delta T?"):
        Delta = st.slider("Minimum delta between cold and heated water (°C)", 5, 15, 10)
        Class.set_delta_t(Delta)
    else:
        Class.set_delta_t(0.0)

    Cold_water = st.selectbox(
        "Cold water profile",
        ("Base load", "Curve"),
    )
    Class.cold_water_chose(Cold_water)

    Class.run_flux_dc()
    fig = go.Figure(
        data=go.Scatter(
            x=Class.df.index,
            y=Class.df["Cold Water Temp"],
            name="Cold Temp [°C]",
            line=dict(color='blue'),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=Class.df.index,
            y=Class.df["Heated Water Temp"],
            name="Expected Heated Temp [°C]",
            line=dict(color='red'),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=Class.df.index,
            y=Class.df["Flux out DC"],
            yaxis="y2",
            name="Flow rate [m3/h]",
            line=dict(color='grey'),
        )
    )
    fig.update_layout(
        title="Water flux profile out of the Data Center",
        legend=dict(orientation="h"),
        yaxis=dict(
            title=dict(text="Temp [°C]"),
            side="left",
            range=[0, 45],
        ),
        yaxis2=dict(
            title=dict(text="Flow rate [m3/h]"),
            side="right",
            range=[0, 9000],
            overlaying="y",
            tickmode="sync",
        ),
    )
    st.plotly_chart(fig)
    st.write(Class.df["Flux out DC"].mean(), 'm3/h mean.')

    st.subheader("Usage of the hot water")
    Heated_water = st.selectbox(
        "Heated water consumption",
        ("All consumed", "Heat demand curve"),
    )
    Class.heated_water_chose(Heated_water)

    if Heated_water == "Heat demand curve":
        st.write("the typical household heat demand in ", note[country_name], " is set to ", note[country_name+'_heat'],
                 "kWh.")
        st.link_button("Link to the household heat demand",
                       note[country_name+"_heat_ref"])

        Heat_demand = Class.heat_calculation(note[country_name+'_heat'])
        fig = go.Figure(
            data=go.Scatter(
                x=Class.df.index,
                y=Class.df["Heat demand"],
                name="Heat demand [kW]",
                line=dict(color='blue'),
            )
        )
        fig.update_layout(
            title="Heat demand for one typical household.",
            legend=dict(orientation="h"),
            yaxis=dict(
                title=dict(text="Heat demand [kW]"),
                side="left",
                range=[0, 18],
            ),
        )
        st.plotly_chart(fig)

        st.write("The output water is set to the Cold Water Profile.")
        Surplus_heated_water = st.selectbox(
            "What is done with the surplus heated water?",
            ("Cooling Tower", "Thermal energy storage"),
        )
        if Surplus_heated_water == "Thermal energy storage":
            Heat_storage = st.slider("Volume of the Heat storage in hundred cubic meter", 1, 1000, 100)*100
            st.write(Heat_storage, " cubic meter")
            st.link_button("Reference",
                           "https://www.nachhaltigwirtschaften.at/resources/pdf/task28_2_6_Thermal_Energy_Storage.pdf")
            Class.surplus_heated_water_chose(Surplus_heated_water, Heat_storage)
        else:
            Class.surplus_heated_water_chose(Surplus_heated_water, 0)
        if st.button("Run Simulation"):
            Class.run_calculation()
            fig = go.Figure(
                data=go.Scatter(
                    x=Class.df.index,
                    y=Class.df["Needed flux"],
                    name="Heat demand [m3/h]",
                    line=dict(color='red'),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=Class.df.index,
                    y=Class.df["Flux out DC"],
                    name="Flow rate out of DC [m3/h]",
                    line=dict(color='blue'),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=Class.df.index,
                    y=Class.df["Stored"],
                    name="Thermal energy stored",
                    line=dict(color='grey'),
                )
            )
            fig.update_layout(
                title="Final run",
                legend=dict(orientation="h"),
                yaxis=dict(
                    title=dict(text="Flux [m3/h]"),
                    side="left",
                    range=[0, 18],
                ),
            )
            st.plotly_chart(fig)
