import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
# streamlit run C:\Users\User\Documents\GitHub\master_thesis_202425\simulation.py
import First_class


note = {"USA": "Knoxville, Tennessee",
        "USA_info": "Temperature taken for the city of Knoxville, Tennessee",
        "USA_temp_ref": "https://www.visualcrossing.com/weather/weather-data-services/knoxville/metric/2023-01-01/"
                        "2023-12-31#",
        "USA_heat": 11634.921,
        "USA_heat_ref": "https://experience.arcgis.com/experience/cbf6875974554a74823232f84f563253?src=%E2%80%B9%"
                        "20Consumption%20%20%20%20%20%20Residential%20Energy%20Consumption%20Survey%20(RECS)-b2",
        "Germany": "Weimar, Thuringia",
        "Germany_info": "Temperature taken for the city of Weimar, Thuringia",
        "Germany_temp_ref": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/"
                            "air_temperature/historical/",
        "Germany_heat": 12216,
        "Germany_heat_ref": "https://www.destatis.de/EN/Themes/Society-Environment/Environment/Environmental-"
                            "Economic-Accounting/private-households/Tables/energy-heating-households.html",
        "Custom": "Custom Country",
        "Custom_info": "Temperature taken for a custom city",
        "Custom_temp_ref": "",
        "Custom_heat": 10000,
        "Custom_heat_ref": "",

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
    col1_heat, col2_heat, col3_heat = st.columns([1, 1, 1])
    Heated_temp = col1_heat.slider("Heated water temperature (°C)", 20, 40, 30)
    Cold_water = col2_heat.selectbox(
        "Cold water profile",
        ("Base load", "Curve"),
    )
    with col3_heat:
        if Cold_water == "Base load":
            Delta = 0
            st.write("Minimal temperature delta (°C)")
            st.write("0°C")
        else:
            Delta = st.slider("Minimal temperature delta (°C)", 0, 15, 10)
    Class.set_heat_network_temp(Heated_temp, Cold_water, Delta)
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
    st.write("Mean flow rate: ", Class.df["Flux out DC"].mean(), 'm3/h.')

    st.subheader("Location of the DC")
    DC_country_location = st.radio("Outdoor temp for the given location",
                                   ["USA", "Germany", "Custom"],
                                   horizontal=True)
    Class.country_chose(DC_country_location)
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

    col1_temp, col2_temp = st.columns([10, 9])
    col1_temp.write(note[DC_country_location+"_info"])
    col2_temp.link_button("Link to the hourly 2023 outdoor temperature",
                          note[DC_country_location+"_temp_ref"])

    st.subheader("Load profile")
    st.write("The output water is set to the Cold Water Profile.")
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
            range=[0, 6.75],
        ),
    )
    st.plotly_chart(fig)

    st.write("The typical household heat demand in ", note[Load_country_location], " is set to ",
             note[Load_country_location+'_heat'], "kWh.")
    st.link_button("Link to the household heat demand",
                   note[Load_country_location+"_heat_ref"])

    st.subheader("Network configuration")
    network_type = st.radio(
        "What's the network element present for this simulation?",
        ("DC - network", "DC - CT - network",
         "DC - CT - storage - network"),
        horizontal=True
    )
    storage_capacity = 0
    storage_type = "None"
    if network_type == "DC - network":
        st.image("network_DC_load.png", caption="The minimal infrastructure: the Data center and the heat network.")
    elif network_type == "DC - CT - network":
        st.image("network_DC_load_CT.png", caption="The infrastructure containing the Data center, "
                                                   "a cooling tower and the heat network.")
    elif network_type == "DC - CT - storage - network":
        st.image("network_DC_load_storage.png", caption="The infrastructure containing the Data center, "
                                                        "a cooling tower, a storage and the heat network.")

        storage_type = st.radio(
            "What type of storage??",
            ("Volumetric storage", "Thermal storage"),
            horizontal=True
        )
        col1_storage, col2_storage = st.columns([1, 1])
        col1_storage.link_button("Reference for volumetric storage",
                                 "https://www.nachhaltigwirtschaften.at/resources/pdf"
                                 "/task28_2_6_Thermal_Energy_Storage.pdf")
        col2_storage.link_button("Reference for thermal storage",
                                 "https://www.pv-magazine.com/2022/07/06/europes-largest-power-to-heat-plant/")
        storage_capacity = st.slider("Volume of the storage in hundred cubic meter", 1, 1000, 100)*100
        st.write(storage_capacity, " cubic meter")
    Class.set_storage(storage_type, storage_capacity)

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
                y=Class.df["Flux out DC"] if network_type == "DC - network" else Class.df["Needed flux"],
                name="Heat demand [m3/h]",
                line=dict(color='green'),
            )
        )
        if storage_type == "Volumetric storage":
            fig.add_trace(
                go.Scatter(
                    x=Class.df.index,
                    y=Class.df["Stored"],
                    yaxis="y2",
                    name="Hot water stored [m3]",
                    line=dict(color='grey'),
                )
            )
        elif storage_type == "Thermal storage":
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
        if storage_type == "Volumetric storage":
            fig.update_layout(
                yaxis2=dict(
                    title=dict(text="Volume [m3]"),
                    side="right",
                    range=[0, storage_capacity*9/8],
                    overlaying="y",
                    tickmode="sync",
                ),
            )
        elif storage_type == "Thermal storage":
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
