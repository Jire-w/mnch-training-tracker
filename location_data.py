import pandas as pd
import streamlit as st

class LocationData:
    def __init__(self):
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load location data from CSV"""
        try:
            self.df = pd.read_csv('woreda.csv')
            # Clean the data - handle NaN values and strip whitespace
            self.df['Region'] = self.df['Region'].str.strip().fillna('')
            self.df['Zone'] = self.df['Zone'].str.strip().fillna('')
            self.df['Woreda'] = self.df['Woreda'].str.strip().fillna('')
            print("Location data loaded successfully!")
            print(f"Total records: {len(self.df)}")
            print(f"Regions: {len(self.df['Region'].unique())}")
            
            # Debug: Print first few records
            print("First 5 records:")
            print(self.df.head())
            
        except Exception as e:
            st.error(f"Error loading location data: {e}")
            # Create empty dataframe if file not found
            self.df = pd.DataFrame(columns=['Region', 'Zone', 'Woreda'])
    
    def get_regions(self):
        """Get unique regions"""
        if self.df is not None and not self.df.empty:
            regions = sorted([r for r in self.df['Region'].unique() if r])
            print(f"Available regions: {len(regions)}")
            return regions
        return []
    
    def get_zones_by_region(self, region):
        """Get zones for a specific region"""
        if self.df is not None and not self.df.empty and region:
            zones = sorted([z for z in self.df[self.df['Region'] == region]['Zone'].unique() if z])
            print(f"Zones for '{region}': {len(zones)} - {zones[:3]}...")  # Show first 3 zones
            return zones
        return []
    
    def get_woredas_by_zone(self, region, zone):
        """Get woredas for a specific zone in a region"""
        if self.df is not None and not self.df.empty and region and zone:
            woredas = sorted([w for w in self.df[(self.df['Region'] == region) & 
                                               (self.df['Zone'] == zone)]['Woreda'].unique() if w])
            print(f"Woredas for '{region}' -> '{zone}': {len(woredas)} - {woredas[:3]}...")  # Show first 3 woredas
            return woredas
        return []

# Global instance
location_data = LocationData()