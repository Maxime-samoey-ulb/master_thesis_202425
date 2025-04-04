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
        "USA_heat": 11634.921,
        "USA_heat_ref": "https://experience.arcgis.com/experience/cbf6875974554a74823232f84f563253?src=%E2%80%B9%"
                        "20Consumption%20%20%20%20%20%20Residential%20Energy%20Consumption%20Survey%20(RECS)-b2",
        "Germany": "Weimar, Thuringia",
        "Germany_info": "Value taken for the city of Weimar, Thuringia",
        "Germany_temp_ref": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/"
                            "air_temperature/historical/",
        "Germany_heat": 12216,
        "Germany_heat_ref": "https://www.destatis.de/EN/Themes/Society-Environment/Environment/Environmental-"
                            "Economic-Accounting/private-households/Tables/energy-heating-households.html",
        "Custom": "Custom Country",
        "Custom_heat": 12216,
        "Custom_heat_ref": "https://www.destatis.de/EN/Themes/Society-Environment/Environment/Environmental-"
                            "Economic-Accounting/private-households/Tables/energy-heating-households.html",

        }

st.title('Master thesis: DC as prosumer for 5GDHC')
if "my_instance" not in st.session_state:
    st.session_state.my_instance = First_class.MyClass()
    st.button("Run load page !")

else:
    Class = st.session_state.my_instance

    expander = st.expander("Before going further")
    expander.write('''
        About this project
    ''')

    st.header("Parameters : ")

    st.subheader("Specification of the DC")
    col_surface, col_heat = st.columns([1, 1])
    surface = col_surface.number_input("Insert the surface area of the DC (m2)", value=2000)
    heat_losses = col_heat.number_input("Insert the heat losses par surface area (kW/m2)", value=15)
    Class.set_dc_cara(surface, heat_losses)
    st.write(Class.Q, 'kW of heat realised by the DC and going to the heat network')

    st.subheader("Specification of the heat network")
    Heated_temp = st.slider("Heated water temperature (°C)", 20, 40, 30)
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

    st.subheader("Location of the DC")
    DC_country_location = st.radio("Outdoor temp for the given location",
                                   ["USA", "Germany", "Custom"],
                                   horizontal=True)
    if st.checkbox("show outdoor temperature profile?"):
        fig = go.Figure(
            data=go.Scatter(
                x=Class.df.index,
                y=Class.df["Outdoor air temp"],
                name="Outdoor temperature",
                line=dict(color='lightblue'),
            )
        )
        fig.update_layout(
            title="Outdoor temperature in " + str(note[DC_country_location]) + " for the year 2023.",
            legend=dict(orientation="h"),
            yaxis=dict(
                title=dict(text="Temperature [°C]"),
                side="left",
                range=[-15, 35],
            ),
        )
        st.plotly_chart(fig)

    st.write(note[DC_country_location+"_info"])
    st.link_button("Link to the hourly 2023 outdoor temperature",
                   note[DC_country_location+"_temp_ref"])
    Class.country_chose(DC_country_location)

    st.subheader("Load profile")
    col1, col2 = st.columns([1, 1])
    with col1:
        set_disabled = True
        Load_country_location = st.radio("Load profile",
                                         ["USA", "Germany", "Custom"],
                                         horizontal=True)
    with col2:
        if Load_country_location == "Custom":
            set_disabled = False
        heat_demand = st.number_input("insert the custom mean annual heat demand per household in kWh",
                                      value=note['USA_heat'],
                                      disabled=set_disabled,
                                      )
        note.update({'Custom_heat': heat_demand})

    st.write("The typical household heat demand in ", note[Load_country_location], " is set to ",
             note[Load_country_location+'_heat'], "kWh.")
    st.link_button("Link to the household heat demand",
                   note[Load_country_location+"_heat_ref"])

    Heat_demand = Class.heat_calculation(note[Load_country_location+'_heat'])
    fig = go.Figure(
        data=go.Scatter(
            x=Class.df.index,
            y=Class.df["Heat demand"],
            name="Heat demand [kW]",
            line=dict(color='lightgreen'),
        )
    )
    fig.update_layout(
        title="Heat demand for one typical household.",
        legend=dict(orientation="h"),
        yaxis=dict(
            title=dict(text="Heat demand [kW]"),
            side="left",
            range=[0, 9],
        ),
    )
    st.plotly_chart(fig)

    st.subheader("Usage of the hot water")
    Heated_water = st.selectbox(
        "Heated water consumption",
        ("All consumed", "Cooling Tower", "Hot water storage", "Thermal heating storage"),
    )
    Class.heated_water_chose(Heated_water)

    st.header("to move")
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
            name="Hot Temp [°C]",
            line=dict(color='pink'),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=Class.df.index,
            y=Class.df["Flux out DC"],
            yaxis="y2",
            name="Flow rate [m3/h]",
            line=dict(color='indianred'),
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

    Heat_storage = 0
    if Heated_water != "All consumed":
        st.write("The output water is set to the Cold Water Profile.")
        if Heated_water == "Hot water storage" or Heated_water == "Thermal heating storage":
            Heat_storage = st.slider("Volume of the Heat storage in hundred cubic meter", 1, 1000, 100)*100
            st.write(Heat_storage, " cubic meter")
            st.link_button("Reference for hot water storage",
                           "https://www.nachhaltigwirtschaften.at/resources/pdf/task28_2_6_Thermal_Energy_Storage.pdf")
            st.link_button("Reference for thermal heating storage",
                           "https://www.pv-magazine.com/2022/07/06/europes-largest-power-to-heat-plant/")
        Class.set_storage_capacity(Heat_storage)

    if st.button("Run Simulation"):
        Class.run_calculation()
        fig = go.Figure(
            data=go.Scatter(
                x=Class.df.index,
                y=Class.df["Flux out DC"],
                name="Flow rate out of DC [m3/h]",
                line=dict(color='indianred'),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=Class.df.index,
                y=Class.df["Flux out DC"] if Heated_water == "All consumed" else Class.df["Needed flux"],
                name="Heat demand [m3/h]",
                line=dict(color='green'),
            )
        )
        if Heated_water == "Hot water storage":
            fig.add_trace(
                go.Scatter(
                    x=Class.df.index,
                    y=Class.df["Stored"],
                    yaxis="y2",
                    name="Hot water stored [m3]",
                    line=dict(color='grey'),
                )
            )
        elif Heated_water == "Thermal heating storage":
            fig.add_trace(
                go.Scatter(
                    x=Class.df.index,
                    y=Class.df["Stored"],
                    yaxis="y2",
                    name="Thermal energy stored [°C]",
                    line=dict(color='grey'),
                )
            )
        fig.update_layout(
            title="Final run",
            legend=dict(orientation="h"),
            yaxis=dict(
                title=dict(text="Flux [m3/h]"),
                side="left",
                range=[0, 4500],
            ),
        )
        if Heated_water == "Hot water storage":
            fig.update_layout(
                yaxis2=dict(
                    title=dict(text="Volume [m3]"),
                    side="right",
                    range=[0, Heat_storage*9/8],
                    overlaying="y",
                    tickmode="sync",
                ),
            )
        elif Heated_water == "Thermal heating storage":
            fig.update_layout(
                yaxis2=dict(
                    title=dict(text="Temperature [°C]"),
                    side="right",
                    range=[0, 112.5],
                    overlaying="y",
                    tickmode="sync",
                ),
            )
        st.plotly_chart(fig)
