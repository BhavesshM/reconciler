import re
import zipfile
import pandas as pd
import numpy as np
import numbers
import math

import plotly.graph_objects as go
import plotly.io as pio
import plotly.subplots as sp
import seaborn as sns
import matplotlib.pyplot as plt

pio.renderers.default = 'browser'


class DataReconciler:
    def __init__(self, active_roster_file, active_data_file):
        self.active_roster = pd.read_excel(active_roster_file)
        self.active_data = pd.read_excel(active_data_file)
        self.active_roster['error'] = ''
        self.active_data['error'] = ''
    
    def sort_data(self):
        relation_order = ["Self", "Spouse", "Son", "Daughter", "Mother", "Father", "Mother-In-Law", "Father-In-Law"]
        
        # for df in [self.active_roster, self.active_data]:
        #     df['Emp No'] = df['Emp No'].apply(lambda x: int(x) if x.isdigit() else x)
        #     df['Emp No'] = df['Emp No'].apply(lambda x: str(x) if not x.isdigit() else x)
            
        self.active_roster['Relation_order'] = self.active_roster['Relation'].apply(lambda x: relation_order.index(x.title()))
        self.active_data['Relation_order'] = self.active_data['Relation'].apply(lambda x: relation_order.index(x.title()))
        
        self.active_roster = self.active_roster.sort_values(by=['Emp No', 'Relation_order']).drop('Relation_order', axis=1)
        self.active_data = self.active_data.sort_values(by=['Emp No', 'Relation_order']).drop('Relation_order', axis=1)
    
    def clean_data(self):
        for df in [self.active_roster, self.active_data]:
            df['Emp No'] = df['Emp No'].apply(lambda x: int(x) if isinstance(x, numbers.Number) and not math.isnan(x) else str(x).lower())
            
            df['Name'] = df['Name'].apply(lambda x: ' '.join([word.lower() for word in str(x).split()]))
            df['Name'] = df['Name'].apply(lambda x: re.sub(r'[^a-zA-Z1-9\s]', '', str(x)).strip().lower())
            
            # df['error'] = None  # Initialize the error column to None
            
            df['DOB'] = pd.to_datetime(df['DOB'], dayfirst=True, errors='coerce')
            df.loc[df['DOB'].isnull(), 'error'] += 'Invalid date; '
            
            # Check if the DOB format is dd-mmm-yyyy
            
            df['DOB_format'] = df['DOB'].dt.strftime('%d-%b-%Y')
            df.loc[df['DOB_format'] != df['DOB'].dt.strftime('%d-%b-%Y'), 'error'] += 'Invalid date format; '

            df['Base Sum Insured'] = df['Base Sum Insured']
            df.loc[df['Base Sum Insured'].apply(lambda x: not isinstance(x, (int, float))), 'error'] += 'Invalid SI; '
            
            df['Gender'] = df['Gender'].fillna(np.nan) 
            df['Gender'] = df['Gender'].astype(str)
            df['Gender'] = df['Gender'].apply(lambda x: x.strip().lower() if isinstance(x, str) else x)

            df.loc[df['Gender'].apply(lambda x: x.upper() not in ['M', 'F', 'MALE', 'FEMALE','NAN']), 'error'] += 'Invalid Gender; '
            df['Gender'] = df['Gender'].apply(lambda x: 'Male' if x.upper() == 'M' else 'Female' if x.upper() == 'F' else x)
            df['Gender'] = df['Gender'].astype(str).str.lower()
            
            df['Relation'] = df['Relation'].apply(lambda x: x.strip().lower())

            df.loc[(df['Relation'].str.lower() == 'child') & (df['Gender'].str.lower() == 'female'), 'Relation'] = 'Daughter'
            df.loc[(df['Relation'].str.lower() == 'child') & (df['Gender'].str.lower() == 'male'), 'Relation'] = 'Son'
            df.loc[(df['Relation'].str.lower() == 'parent') & (df['Gender'].str.lower() == 'female'), 'Relation'] = 'Mother'
            df.loc[(df['Relation'].str.lower() == 'parent') & (df['Gender'].str.lower() == 'male'), 'Relation'] = 'Father'
            df.loc[(df['Relation'].str.lower() == 'parent-in-law') & (df['Gender'].str.lower() == 'female'), 'Relation'] = 'Mother-in-Law'
            df.loc[(df['Relation'].str.lower() == 'parent-in-law') & (df['Gender'].str.lower() == 'male'), 'Relation'] = 'Father-in-Law'
            df.loc[(df['Relation'].str.lower() == 'husband') | (df['Relation'].str.lower() == 'wife'),'Relation'] = 'Spouse'
            # df.loc[(df['Relation'].str.lower() == 'wife'),'Relation'] = 'Spouse'

            df['Relation'] = df['Relation'].astype(str).str.lower()            

    def create_key(self, columns):
        for df in [self.active_roster, self.active_data]:
            df.loc[df['remarks'].isnull(), 'key'] = df.apply(lambda row: '_'.join([str(row[col]) for col in columns]), axis=1)

    def match_records(self, key_column, remarks):
        for index, row in self.active_roster.iterrows():
            if row[key_column] in self.active_data[key_column].values and row['remarks'] is None:
                self.active_roster.loc[index, 'remarks'] = remarks
                self.active_data.loc[self.active_data[key_column] == row[key_column], 'remarks'] = remarks

    def reconcile(self):
        # with self.active_roster.open('rb') as f:
        #     active_roster = f.read()
        # with self.active_data.open('rb') as f:
        #     active_data = f.read()
            
        self.clean_data()

        self.sort_data()

        self.active_roster['remarks'] = None
        self.active_data['remarks'] = None

        #Exact Match
        self.create_key(['Emp No', 'Relation', 'Name', 'DOB', 'Gender', 'Base Sum Insured'])
        
        # Check for duplicates in active_roster
        duplicates_roster = self.active_roster[self.active_roster.duplicated(['key'], keep='first')]
        self.active_roster.loc[duplicates_roster.index, 'remarks'] = 'Duplicate'

        # Check for duplicates in active_data
        duplicates_data = self.active_data[self.active_data.duplicated(['key'], keep='first')]
        self.active_data.loc[duplicates_data.index, 'remarks'] = 'Duplicate'

        print(duplicates_data)
        print(self.active_data.loc[self.active_data['remarks']=='Duplicate'])        
        
        self.match_records('key','Matched')


        # 1 Column Exclusion

        # Name Correction
        self.create_key(['Emp No', 'Relation', 'DOB', 'Gender', 'Base Sum Insured'])
        self.match_records('key','Name Correction')

        # DOB Correction
        self.create_key(['Emp No', 'Name', 'Relation', 'Gender', 'Base Sum Insured'])
        self.match_records('key','DOB Correction')

        # Gender Correction
        self.create_key(['Emp No', 'Name', 'Relation', 'DOB', 'Base Sum Insured'])
        self.match_records('key','Gender Correction')

        # Need to be commented
        # EMP ID Correction
        # self.create_key(['Name', 'Relation', 'DOB', 'Gender', 'Base Sum Insured'])
        # self.match_records('key','EMP ID Correction')
 
        # SI Correction
        self.create_key(['Emp No', 'Name', 'Relation', 'DOB', 'Gender'])
        self.match_records('key','SI Correction')

        # Relation Correction
        self.create_key(['Emp No', 'Name', 'DOB', 'Gender', 'Base Sum Insured'])
        self.match_records('key','Relation Correction')

        # 2 Columns Exclusion 

        # # EMP ID and Relation Correction
        # self.create_key([ 'Name', 'DOB', 'Gender', 'Base Sum Insured'])
        # self.match_records('key','EMP ID and Relation Correction')

        # # EMP ID and Name Correction
        # self.create_key([ 'Relation', 'DOB', 'Gender', 'Base Sum Insured'])
        # self.match_records('key','EMP ID and Name Correction')

        # # EMP ID and DOB Correction
        # self.create_key([ 'Relation', 'Name', 'Gender', 'Base Sum Insured'])
        # self.match_records('key','EMP ID and DOB Correction')

        # # EMP ID and SI Correction
        # self.create_key([ 'Relation', 'Name', 'DOB', 'Gender'])
        # self.match_records('key','EMP ID and SI Correction')

        # # EMP ID and Gender Correction
        # self.create_key([ 'Relation', 'Name', 'DOB',  'Base Sum Insured'])
        # self.match_records('key','EMP ID and Gender Correction')

        # Name and Relation Correction
        self.create_key(['Emp No', 'DOB', 'Gender', 'Base Sum Insured'])
        self.match_records('key','Relation and Name Correction')

        # DOB and Relation Correction
        self.create_key(['Emp No','Name', 'Gender', 'Base Sum Insured'])
        self.match_records('key','Relation and DOB Correction')

        # Gender and Relation Correction
        self.create_key(['Emp No','Name', 'DOB', 'Base Sum Insured'])
        self.match_records('key','Relation and Gender Correction')

        # SI and Relation Correction
        self.create_key(['Emp No','Name', 'DOB', 'Gender'])
        self.match_records('key','Relation and SI Correction')

        # Name and DOB Correction
        self.create_key(['Emp No', 'Relation', 'Gender', 'Base Sum Insured'])
        self.match_records('key','Name and DOB Correction')

        # Name and Gender Correction
        self.create_key(['Emp No', 'Relation', 'DOB', 'Base Sum Insured'])
        self.match_records('key','Name and Gender Correction')

        # Name and SI Correction
        self.create_key(['Emp No', 'Relation', 'DOB', 'Gender'])
        self.match_records('key','Name and SI Correction')

        # DOB and Gender Correction
        self.create_key(['Emp No', 'Relation', 'Name', 'Base Sum Insured'])
        self.match_records('key','DOB and Gender Correction')

        # DOB and SI Correction
        self.create_key(['Emp No', 'Relation', 'Name', 'Gender'])
        self.match_records('key','DOB and SI Correction')

        # Gender and SI Correction
        self.create_key(['Emp No', 'Relation', 'Name', 'DOB'])
        self.match_records('key','Gender and SI Correction')


        # 3 Columns Exclusion 

        # #EMP ID and Relation and Name Correction
        # self.create_key(['DOB', 'Gender', 'Base Sum Insured'])
        # self.match_records('key','EMP ID and Relation and Name Correction')

        # #EMP ID and Relation and DOB Correction
        # self.create_key(['Name', 'Gender', 'Base Sum Insured'])
        # self.match_records('key','EMP ID and Relation and DOB Correction')

        # # EMP ID and Relation and Gender 
        # self.create_key(['Name', 'DOB', 'Base Sum Insured'])
        # self.match_records('key','EMP ID and Relation and Gender Correction')

        # # EMP ID and Relation and SI
        # self.create_key(['Name', 'DOB', 'Gender'])
        # self.match_records('key','EMP ID and Relation and SI Correction')

        # # EMP ID - Name - DOB
        # self.create_key([ 'Relation', 'Gender', 'Base Sum Insured'])
        # self.match_records('key','EMP ID and Name and DOB Correction')

        # # EMP ID - Name - Gender
        # self.create_key([ 'Relation', 'DOB', 'Base Sum Insured'])
        # self.match_records('key','EMP ID and Name and Gender Correction')

        # # EMP ID - Name - SI
        # self.create_key([ 'Relation', 'DOB', 'Gender'])
        # self.match_records('key','EMP ID and Name and SI Correction')

        # # EMP ID - DOB - SI
        # self.create_key([ 'Relation', 'Name', 'Gender'])    
        # self.match_records('key','EMP ID and DOB and SI Correction')

        # # EMP ID - DOB - Gender
        # self.create_key([ 'Relation', 'Name', 'Base Sum Insured'])
        # self.match_records('key','EMP ID and DOB and Gender Correction')

        # # EMP ID - Gender - SI
        # self.create_key([ 'Relation', 'Name', 'DOB'])
        # self.match_records('key','EMP ID and Gender and SI Correction')

        # Relation - Name - DOB
        # self.create_key([ 'Emp No', 'Gender', 'Base Sum Insured'])
        # self.match_records('key','Relation and Name and DOB Correction')

        # Relation - Name - Gender
        self.create_key([ 'Emp No', 'DOB', 'Base Sum Insured'])
        self.match_records('key','Relation and Name and Gender Correction')

        # Relation - Name - SI
        self.create_key([ 'Emp No', 'DOB', 'Gender'])
        self.match_records('key','Relation and Name and SI Correction')

        # Relation - DOB - Gender
        self.create_key([ 'Emp No', 'Name', 'Base Sum Insured'])
        self.match_records('key','Relation and DOB and Gender Correction')

        # Relation - DOB - SI
        self.create_key([ 'Emp No', 'Name', 'Gender'])
        self.match_records('key','Relation and DOB and SI Correction')

        # Name - DOB - Gender
        self.create_key([ 'Emp No', 'Relation', 'Base Sum Insured'])
        self.match_records('key','Name and DOB and Gender Correction')

        # Name - DOB - SI
        self.create_key([ 'Emp No', 'Relation', 'Gender'])
        self.match_records('key','Name and DOB and SI Correction')

        # DOB - Gender - SI
        self.create_key([ 'Emp No', 'Relation', 'Name'])
        self.match_records('key','DOB and Gender and SI Correction')

        self.active_roster.loc[self.active_roster['remarks'].isnull(), 'remarks'] = 'Not found in insurer active data'
        self.active_data.loc[self.active_data['remarks'].isnull(), 'remarks'] = 'Not found in active roster data'

    def create_summary (self, final_ar):
        summary_roster = final_ar['Remarks'].value_counts().reset_index()
        summary_roster.columns = ['Remarks', 'Count']
        summary_roster.loc['Grand Total'] = ['Grand Total', summary_roster['Count'].sum()]
        return summary_roster

    def standardize_roster (self,final_ar):
        final_ar = final_ar[['Emp No', 'Relation', 'Name', 'DOB', 'Gender', 'Base Sum Insured','key', 'remarks']]
        final_ar.columns = [col.title() for col in final_ar.columns]
        final_ar['Name'] = final_ar['Name'].apply(lambda x: x.title())
        final_ar['Relation'] = final_ar['Relation'].apply(lambda x: x.title())
        final_ar['Gender'] = final_ar['Gender'].apply(lambda x: x.title())
        final_ar['Dob'] = final_ar['Dob'].dt.strftime('%d-%b-%Y')
        
        return final_ar


    def save_results(self, zip_file, active_roster_filename, active_data_filename, error_zip_file, error_roster_filename, error_data_filename):
                
        try:
            if (self.active_roster['error'] != '').any() or (self.active_data['error'] != '').any():
                raise ValueError("Error in file, cannot save results")
            
            final_ar = self.standardize_roster(self.active_roster)
            final_ad = self.standardize_roster(self.active_data)

            summary_roster = self.create_summary(final_ar)
            summary_data = self.create_summary(final_ad)

            with zipfile.ZipFile(zip_file, 'w') as zip:
                with zip.open(active_roster_filename, 'w') as roster_file:
                    with pd.ExcelWriter(roster_file) as writer:
                        final_ar.to_excel(writer, sheet_name='Active Roster', index=False)
                        summary_roster.to_excel(writer, sheet_name='Summary', index=False)

                with zip.open(active_data_filename, 'w') as data_file:
                    with pd.ExcelWriter(data_file) as writer:
                        final_ad.to_excel(writer, sheet_name='Active Data', index=False)
                        summary_data.to_excel(writer, sheet_name='Summary', index=False)

            # print('Returning output')            
            return zip_file

        except ValueError as e:
                print(f"Error: {str(e)}")
                error_roster = self.active_roster[self.active_roster['error']!=''][['Emp No', 'Relation', 'Name', 'DOB', 'Gender', 'Base Sum Insured', 'error']]
                error_data = self.active_data[self.active_data['error']!=''][['Emp No', 'Relation', 'Name', 'DOB', 'Gender', 'Base Sum Insured', 'error']]
                
                try:
                    with zipfile.ZipFile(error_zip_file, 'w') as error_zip:
                        with error_zip.open(error_roster_filename, 'w') as error_roster_file:
                            with pd.ExcelWriter(error_roster_file) as writer:
                                error_roster.to_excel(writer, sheet_name='Error Roster', index=False)
                        
                        with error_zip.open(error_data_filename, 'w') as error_data_file:
                            with pd.ExcelWriter(error_data_file) as writer:
                                error_data.to_excel(writer, sheet_name='Error Data', index=False)
                except Exception as e:
                    print(f"Error writing error files: {str(e)}")
        # print('Returning Error')        
        return error_zip_file 
    
    def create_graph(self):
            final_ar = self.standardize_roster(self.active_roster)
            final_ad = self.standardize_roster(self.active_data)

            summary_roster = self.create_summary(final_ar)
            summary_data = self.create_summary(final_ad)
            
            self.create_semi_pie_chart(summary_roster, summary_data)

        
    
    def create_semi_pie_chart(self, summary_roster, summary_data):
        # Define custom colors for the pie charts
        custom_colors = [
            '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', 
            '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'
        ]
        
        # Create the subplots
        fig = sp.make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]], subplot_titles=("Active Roster", "Active Data"),
                            horizontal_spacing=0.2, vertical_spacing=0.2)

        # Create the first pie chart for Active Roster
        fig.add_trace(go.Pie(
            labels=summary_roster[summary_roster['Remarks'] != 'Grand Total']['Remarks'].tolist(),
            values=summary_roster[summary_roster['Remarks'] != 'Grand Total']['Count'].tolist(),
            textinfo='value',
            insidetextorientation='radial',
            marker=dict(colors=custom_colors),  # Add a white color for the dummy slice
            direction='clockwise',  # Direction of the pie chart
            rotation=90  # Start angle of the pie chart
        ), row=1, col=1)

        # Create the second pie chart for Active Data
        fig.add_trace(go.Pie(
            labels=summary_data[summary_data['Remarks'] != 'Grand Total']['Remarks'].tolist(),
            values=summary_data[summary_data['Remarks'] != 'Grand Total']['Count'].tolist(),
            textinfo='value',
            insidetextorientation='radial',
            marker=dict(colors=custom_colors),  # Add a white color for the dummy slice
            direction='clockwise',  # Direction of the pie chart
            rotation=90  # Start angle of the pie chart
        ), row=1, col=2)

        # Update the layout
        fig.update_layout(height=500, width=1000, showlegend=True,
                        margin=dict(l=100, r=100, t=100, b=100))

        # Show the plot
        fig.show()

                                      
if __name__ == '__main__':
    # print('Father-In-Law'.lower())
    # reconciler = DataReconciler(
    #     r'C:\Users\Shrikant Pansare\Documents\Project\Recon\Demo\Active roster.xlsx',
    #     r'C:\Users\Shrikant Pansare\Documents\Project\Recon\Demo\active data.xlsx')
    # reconciler.reconcile()
    # reconciler.save_results(
    #     r'C:\Users\Shrikant Pansare\Documents\Project\Recon\Demo\active_roster_updated.xlsx',
    #     r'C:\Users\Shrikant Pansare\Documents\Project\Recon\Demo\active_data_updated.xlsx'
    # )
    pass