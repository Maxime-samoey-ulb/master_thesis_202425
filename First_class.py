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
        self.nbr_household = int
        # self.ref_table = pd.DataFrame()
        # self.df = pd.DataFrame()
        self.ref_table = pd.read_csv("temperature_data.csv", index_col=0).ffill()
        self.ref_table.index = pd.to_datetime(self.ref_table.index, format='%Y-%m-%d %H:%M:%S')
        self.df = pd.DataFrame(index=self.ref_table.index, columns=["Cold Water Temp", "Heated Water Temp",
                                                                    "Delta temp", "Flux out DC", "Outdoor air temp",
                                                                    "Heat demand", "Needed flux", "Delta flux",
                                                                    "Stored", "Through CT", "Too short"])
        self.area = float  # in square meters
        self.heat_loss = float  # in kW per square meters
        self.Q = 1.0  # in kW
        self.heated_temp = 30.0  # in °C
        self.delta = 0.0  # in °C
        self.cold_water_profile = str
        self.network_type = str
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

    def heat_calculation(self, heat_demand, nbr_household: int):
        self.nbr_household = nbr_household
        self.df["Heat demand"] = bdew.HeatBuilding(
                                 self.df.index,
                                 temperature=self.df["Outdoor air temp"],
                                 shlp_type="MFH",
                                 building_class=2,
                                 wind_class=0,
                                 annual_heat_demand=heat_demand,
                                 name="EFH",
        ).get_bdew_profile()
        self.df["Needed flux"] = self.df["Heat demand"]*self.nbr_household/(1.16*self.df["Delta temp"])
        self.df["Delta flux"] = self.df["Flux out DC"] - self.df["Needed flux"]

    def set_storage(self, network_type: str, heated_water: str, storage: int):
        self.network_type = network_type
        self.storage_type = heated_water
        self.storage_capacity = storage

    def run_calculation(self):
        if self.network_type == "DC - network":
            self.df["Down scale DC"] = self.df["Flux out DC"]
            self.df.loc[self.df["Flux out DC"] > self.df["Needed flux"], "Down scale DC"] = self.df["Needed flux"]
        delta_flux_list = self.df["Delta flux"].tolist()
        through_ct = []
        too_short = []
        if self.storage_type == "Volumetric storage":
            old_store = 0.0
            store = []
            for i in range(8760):
                to_store = delta_flux_list[i]
                for_ct = 0
                not_enough = 0
                if i != 0:
                    old_store = store[i-1]
                new_store = to_store + old_store
                if new_store > self.storage_capacity:
                    for_ct = new_store - self.storage_capacity
                    new_store = self.storage_capacity
                elif 0 > new_store:
                    not_enough = new_store
                    new_store = 0
                store.append(new_store)
                through_ct.append(for_ct)
                too_short.append(not_enough)
            self.df["Stored"] = pd.Series(index=self.df.index, data=store)
        elif self.storage_type == "Thermal storage":
            delta_temp_list = self.df["Delta temp"].tolist()
            cold_water_list = self.df["Cold Water Temp"].tolist()
            old_temp = 30.0
            temp = []
            for i in range(8760):
                for_ct = 0
                not_enough = 0
                if i != 0:
                    old_temp = temp[i-1]
                if delta_flux_list[i] >= 0:
                    added_energy = delta_flux_list[i] * 1.16 * delta_temp_list[i]
                    delta_temp = added_energy/(1.16*self.storage_capacity)
                else:
                    extracted_energy = delta_flux_list[i] * 1.16 * (old_temp - cold_water_list[i])
                    delta_temp = extracted_energy/(1.16*self.storage_capacity)
                new_temp = delta_temp + old_temp
                if new_temp > self.max_temp:
                    excess_energy = (new_temp - self.max_temp) * 1.16 * self.storage_capacity
                    for_ct = excess_energy/(1.16 * delta_temp_list[i])
                    new_temp = self.max_temp
                elif 30 > new_temp:
                    lack_energy = (new_temp - 30) * 1.16 * self.storage_capacity
                    not_enough = lack_energy/(1.16 * delta_temp_list[i])
                    new_temp = 30
                temp.append(new_temp)
                through_ct.append(for_ct)
                too_short.append(not_enough)
            self.df["Stored"] = pd.Series(index=self.df.index, data=temp)
        else:
            for i in range(8760):
                for_ct = 0
                not_enough = 0
                if delta_flux_list[i] > 0:
                    for_ct = delta_flux_list[i]
                else:
                    not_enough = delta_flux_list[i]
                through_ct.append(for_ct)
                too_short.append(not_enough)
        self.df["Too short"] = pd.Series(index=self.df.index, data=too_short)
        self.df["Through CT"] = pd.Series(index=self.df.index, data=through_ct)

