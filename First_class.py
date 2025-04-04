import pandas as pd
import demandlib.bdew as bdew
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# streamlit run C:\Users\User\Documents\GitHub\master_thesis_202425\simulation.py


def set_table(country):
    # path = f"{country}_ref.csv"
    # table = pd.read_csv(path, index_col=0)
    table = pd.read_csv("temperature_data.csv", index_col=0)
    table.index = pd.to_datetime(table.index, format='%Y-%m-%d %H:%M:%S')
    return table


class MyClass:
    def __init__(self):
        self.country = str
        # self.ref_table = pd.DataFrame()
        # self.df = pd.DataFrame()
        self.ref_table = pd.read_csv("temperature_data.csv", index_col=0).ffill()
        self.ref_table.index = pd.to_datetime(self.ref_table.index, format='%Y-%m-%d %H:%M:%S')
        self.df = pd.DataFrame(index=self.ref_table.index, columns=["Cold Water Temp", "Heated Water Temp",
                                                                    "Delta temp", "Flux out DC", "Outdoor air temp",
                                                                    "Heat demand", "Needed flux", "Delta flux", "Stored"])
        self.area = float  # in square meters
        self.heat_loss = float  # in kW per square meters
        self.Q = 1.0  # in kW
        self.heated_temp = 30.0  # in °C
        self.delta = 0.0  # in °C
        self.cold_water_profile = str
        self.storage_type = str
        self.storage_capacity = 0
        self.max_temp = 98.0

    def set_dc_cara(self, area, heat_loss):
        self.area = area
        self.heat_loss = heat_loss
        self.Q = heat_loss * area  # in kW

    def set_heat_network_temp(self, temp: int, cold_water: str, delta: float):
        self.heated_temp = temp
        self.cold_water_profile = cold_water
        # cw_temp = self.ref_table[f'{self.country}_CW_temperature']
        cw_temp = self.ref_table['USA_CW_temperature']
        if cold_water == "Base load":
            self.df["Cold Water Temp"] = cw_temp.mean()
        else:
            self.df["Cold Water Temp"] = cw_temp
        self.delta = delta

        self.heated_water_calculation()

    def heated_water_calculation(self):
        self.df.loc[self.df["Cold Water Temp"] + self.delta >= self.heated_temp, "Heated Water Temp"] = (
                    self.df["Cold Water Temp"] + self.delta)
        self.df.loc[self.heated_temp >= self.df["Cold Water Temp"] + self.delta, "Heated Water Temp"] = self.heated_temp
        self.df["Delta temp"] = self.df["Heated Water Temp"] - self.df["Cold Water Temp"]
        self.df["Flux out DC"] = self.Q/(1.16*self.df["Delta temp"])

    def country_chose(self, country: str):
        self.country = country
        self.df["Outdoor air temp"] = self.ref_table[f"{self.country}_air_temperature"]

    def heat_calculation(self, heat_demand):
        self.df["Heat demand"] = bdew.HeatBuilding(
                                 self.df.index,
                                 temperature=self.df["Outdoor air temp"],
                                 shlp_type="MFH",
                                 building_class=2,
                                 wind_class=0,
                                 annual_heat_demand=heat_demand,
                                 name="EFH",
        ).get_bdew_profile()

    def set_storage(self, heated_water: str, storage: int):
        self.storage_type = heated_water
        self.storage_capacity = storage

    def run_calculation(self):
        self.df["Needed flux"] = self.df["Heat demand"]*10000/(1.16*self.df["Delta temp"])
        self.df["Delta flux"] = self.df["Flux out DC"] - self.df["Needed flux"]
        if self.storage_type == "Volumetric storage":
            old_store = 0.0
            store = []
            for i in range(8760):
                to_store = self.df.iloc[i]["Delta flux"]
                if i != 0:
                    old_store = store[i-1]
                new_store = to_store + old_store
                if new_store > self.storage_capacity:
                    new_store = self.storage_capacity
                elif 0 > new_store:
                    new_store = 0
                store.append(new_store)
            self.df["Stored"] = pd.Series(index=self.df.index, data=store)
        elif self.storage_type == "Thermal storage":
            old_temp = 30.0
            temp = []
            for i in range(8760):
                if i != 0:
                    old_temp = temp[i-1]
                if self.df.iloc[i]["Delta flux"] >= 0:
                    added_energy = self.df.iloc[i]["Delta flux"] * 1.16 * self.df.iloc[i]["Delta temp"]
                    delta_temp = added_energy/(1.16*self.storage_capacity)
                else:
                    extracted_energy = self.df.iloc[i]["Delta flux"] * 1.16 * (old_temp - self.df.iloc[i]["Cold Water Temp"])
                    delta_temp = extracted_energy/(1.16*self.storage_capacity)
                new_temp = delta_temp + old_temp
                if new_temp > self.max_temp:
                    new_temp = self.max_temp
                elif 30 > new_temp:
                    new_temp = 30
                temp.append(new_temp)
            self.df["Stored"] = pd.Series(index=self.df.index, data=temp)

