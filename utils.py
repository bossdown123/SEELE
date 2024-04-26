import requests
import pandas as pd
import simfin as sf
from simfin.names import *

class Earningsv2:
    def __init__(self, api_key, data_dir, stocks,config):
        self.api_key = api_key
        sf.set_api_key(self.api_key)
        sf.set_data_dir(data_dir)
        self.config=config
        self.stocks=stocks
        print('Fetching data...')
        if '*' in self.config:
            self.income = sf.load_income(variant='Quarterly', market='us')
            self.balance = sf.load_balance(variant='Quarterly', market='us')
            self.cashflow = sf.load_cashflow(variant='Quarterly', market='us')

            self.income = self.income[self.income.index.get_level_values('Ticker').isin(self.stocks)]
            self.balance = self.balance[self.balance.index.get_level_values('Ticker').isin(self.stocks)]
            self.cashflow = self.cashflow[self.cashflow.index.get_level_values('Ticker').isin(self.stocks)]

        if 'banks' in self.config:
            self.income_banks = sf.load_income_banks(variant='Quarterly', market='us')
            self.balance_banks = sf.load_balance_banks(variant='Quarterly', market='us')
            self.cashflow_banks = sf.load_cashflow_banks(variant='Quarterly', market='us')
            
            self.income_banks = self.income_banks[self.income_banks.index.get_level_values('Ticker').isin(self.stocks)]
            self.balance_banks = self.balance_banks[self.balance_banks.index.get_level_values('Ticker').isin(self.stocks)]
            self.cashflow_banks = self.cashflow_banks[self.cashflow_banks.index.get_level_values('Ticker').isin(self.stocks)]

        if 'insurance' in self.config:        
            self.income_insurance = sf.load_income_insurance(variant='Quarterly', market='us')
            self.balance_insurance = sf.load_balance_insurance(variant='Quarterly', market='us')
            self.cashflow_insurance = sf.load_cashflow_insurance(variant='Quarterly', market='us')
        
            self.income_insurance = self.income_insurance[self.income_insurance.index.get_level_values('Ticker').isin(self.stocks)]
            self.balance_insurance = self.balance_insurance[self.balance_insurance.index.get_level_values('Ticker').isin(self.stocks)]
            self.cashflow_insurance = self.cashflow_insurance[self.cashflow_insurance.index.get_level_values('Ticker').isin(self.stocks)]
        
        
        self.companies= sf.load_companies(market='us')
        self.banks=None
        self.insurance=None
        self.regular=None
        self.statements=None
        self.fetch_statement()
        
    def stockinfo(self):
        df_c=self.companies
        df_c=df_c[df_c.index.get_level_values('Ticker').isin(self.stocks)]
        self.banks=df_c[df_c['IndustryId'].astype(int).isin([104002,104007,])]
        self.insurance=df_c[df_c['IndustryId'].astype(int).isin([104004,104005,104006,104013,])]
        self.regular=df_c[~df_c['IndustryId'].astype(int).isin([104002,104004,104005,104006,104013,])]
    def combine_statements(self):
        combined = pd.concat([self.statements['*']['income'], self.statements['*']['balance'], self.statements['*']['cashflow']], axis=1)
        stocks_to_drop = [stock for stock in combined.index.get_level_values(0).unique() if combined.xs(stock, level=0).isnull().any().any()]
        #['C','BAC','GS','MS','WFC','CI','BRK-B','MMC','ELV','SCHW','AXP','PGR','JPM']
        self.stocks=list((set(self.stocks).difference(set(stocks_to_drop))))
        self.statements['*'] = combined.drop(index=stocks_to_drop, level=0) 
           
    def fetch_statement(self):

        self.statements={'*':{'income':None,'balance':None,'cashflow':None},}
        if '*' in self.config:
            self.statements['*']['income'] = self.income[self.config['*']['income']]

            self.statements['*']['balance'] = self.balance[self.config['*']['balance']]
            self.statements['*']['cashflow'] = self.cashflow[self.config['*']['cashflow']]
            
        if 'banks' in self.config:
            self.statements['banks']['income'] = self.income_banks[self.config['banks']['income']]
            self.statements['banks']['balance'] = self.balance_banks[self.config['banks']['balance']]
            self.statements['banks']['cashflow'] = self.cashflow_banks[self.config['banks']['cashflow']]

        if 'insurance' in self.config:        
            self.statements['insurance']['income'] = self.income_insurance[self.config['insurance']['income']]
            self.statements['insurance']['balance'] = self.balance_insurance[self.config['insurance']['balance']]
            self.statements['insurance']['cashflow'] = self.cashflow_insurance[self.config['insurance']['cashflow']]

        self.combine_statements()
        
                    
class Earnings:
    def __init__(self):
        self.url = "https://www.dolthub.com/api/v1alpha1/post-no-preference/earnings/master"

    class ResponseWrapper:
        def __init__(self, data):
            self.data = data

        def __repr__(self):
            return print(self.data)
        
        @property
        def df(self):
            if 'rows' in self.data and len(self.data['rows']) > 0:
                df = pd.DataFrame(self.data['rows']).set_index('date')
                df.index = pd.to_datetime(df.index).tz_localize('UTC')
                unique_symbols = df['act_symbol'].unique()
                dfs = {}
                for symbol in unique_symbols:
                    symbol_df = df[df['act_symbol'] == symbol]
                    numeric_df = symbol_df.apply(pd.to_numeric, errors='coerce').drop(['act_symbol', 'period'], axis=1)
                    dfs[symbol] = numeric_df.add_prefix(f"{symbol}_")
                return pd.concat(dfs.values(), axis=1).ffill()
            else:
                return pd.DataFrame()  # Return an empty DataFrame if there are no rows
    def fetch_data(self, table, stocks, period, order='DESC', order_by='period', limit=1000, columns=None):
        response = requests.get(self.url, params=self.create_query(table, stocks, period, order, order_by, limit, columns))
        return self.ResponseWrapper(self.handle_response(response))

    def fetch_balance_sheet_assets(self, stocks, period='Quarter', order='DESC', order_by='period', limit=1000, columns=None):
        response = requests.get(self.url, params=self.create_query('balance_sheet_assets', stocks, period, order, order_by, limit, columns))
        return self.ResponseWrapper(self.handle_response(response))
    
    def fetch_balance_sheet_equity(self, stocks, period='Quarter',order='DESC',order_by='period',limit=1000, columns=None):
        response = requests.get(self.url, params=self.create_query('balance_sheet_equity', stocks, period, order, order_by, limit, columns))
        return self.ResponseWrapper(self.handle_response(response))
    
    def fetch_balance_sheet_liabilities(self, stocks, period='Quarter',order='DESC',order_by='period',limit=1000, columns=None):
        response = requests.get(self.url, params=self.create_query('balance_sheet_liabilities', stocks, period, order, order_by, limit, columns))
        return self.ResponseWrapper(self.handle_response(response))
    
    def fetch_cash_flow_statements(self, stocks, period='Quarter',order='DESC',order_by='period',limit=1000, columns=None):
        response = requests.get(self.url, params=self.create_query('cash_flow_statements', stocks, period, order, order_by, limit, columns))
        return self.ResponseWrapper(self.handle_response(response))
    
    def fetch_eps_estimate(self, stocks, period='Current Quarter',order='DESC',order_by='period',limit=1000, columns=None):
        response = requests.get(self.url, params=self.create_query('eps_estimate', stocks, period, order, order_by, limit, columns))
        return self.ResponseWrapper(self.handle_response(response))
        
    def fetch_income_statements(self, stocks, period='Quarter',order='DESC',order_by='period',limit=1000, columns=None):
        response = requests.get(self.url, params=self.create_query('income_statements', stocks, period, order, order_by, limit, columns))
        return self.ResponseWrapper(self.handle_response(response))

    def fetch_sales_estimate(self, stocks, period='Current Quarter',order='DESC',order_by='period',limit=1000, columns=None):
        if period not in ['Current Quarter', 'Next Quarter']:
            print('Period must be in the format "Current Quarter" or "Next Quarter"')
            return
        response = requests.get(self.url, params=self.create_query('sales_estimate', stocks, period, order, order_by, limit, columns))
        return self.ResponseWrapper(self.handle_response(response))

    def create_query(self, table, stocks, period='Quarter', order='DESC', order_by='period', limit=1000, columns=None):
        if not isinstance(stocks, list):
            stocks = [stocks]
        formatted_stocks = str(tuple(stocks)).rstrip(",)") + ")" if len(stocks) == 1 else str(tuple(stocks))
        selected_columns = 'date, act_symbol, period, '+', '.join(columns) if columns else '*'

        query = f"""
        SELECT {selected_columns}
        FROM `{table}`
        WHERE `act_symbol` IN {formatted_stocks}
        AND `period` = '{period}'
        ORDER BY `{order_by}` {order}
        LIMIT {limit};
        """
        return {'q': query}

    
    def handle_response(self, response):
        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: {response.status_code}"
        

from sklearn.preprocessing import *
            
import pandas as pd
class MultiScalerOld:
    def __init__(self, scaler_config=None):
        self.scalers = scaler_config
        #print("Scaler configuration initialized.")

    def is_fit_called(self, obj):
        return hasattr(obj, "n_features_in_")

    def fit(self, df):
        df = df.copy()
        #print("Fitting scalers...")
        for scale_set in self.scalers:
            for scaler in scale_set['procedures']:
                scaler.fit(df[scale_set['features']])
                df[scale_set['features']] = scaler.transform(df[scale_set['features']])
                #print(f"Fitted and transformed features: {scale_set['features']} with {scaler}")
        return self
    
    def transform(self, df):
        df = df.copy()
        #print("Transforming data...")
        for scale_set in self.scalers:
            missing_cols = [col for col in scale_set['features'] if col not in df.columns]
            if missing_cols:
                #print(f"Missing columns added: {missing_cols}")
                df_missing = pd.DataFrame(0, index=df.index, columns=missing_cols)
                df = pd.concat([df, df_missing], axis=1)
                
            for scaler in scale_set['procedures']:
                df[scale_set['features']] = scaler.transform(df[scale_set['features']])
                #print(f"Applied transformation for features: {scale_set['features']} using {scaler}")
        return df
    
    def fit_transform(self, df):
        df = df.copy()
        #print("Fit transforming data...")
        for scale_set in self.scalers:
            for scaler in scale_set['procedures']:
                df[scale_set['features']] = scaler.fit_transform(df[scale_set['features']])
                print(f"Fitted and transformed features: {scale_set['features']} with {scaler}")
        return df

    def inverse_transform(self, df):
        df = df.copy()
        #print("Inverse transforming data...")
        for scale_set in self.scalers:
            missing_cols = [col for col in scale_set['features'] if col not in df.columns]
            if missing_cols:
                df_missing = pd.DataFrame(df.mean().mean(), index=df.index, columns=missing_cols)
                df = pd.concat([df, df_missing], axis=1)
                #print(f"Missing columns filled for inverse transform: {missing_cols}")
                
            for scaler in reversed(scale_set['procedures']):
                df[scale_set['features']] = scaler.inverse_transform(df[scale_set['features']])
                #print(f"Inverse transformed features: {scale_set['features']} using {scaler}")
        return df

import pandas as pd
import numpy as np
from sklearn.base import TransformerMixin
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from typing import List, Dict, Optional

class AdaptiveMultiScalerUpdated():
    def __init__(self, scaler_config=None):
        self.scalers = scaler_config if scaler_config is not None else []

    def fit(self, df, y=None):
        for scaler_set in self.scalers:
            existing_features = [feature for feature in scaler_set['features'] if feature in df.columns]
            if not existing_features:
                continue
            for scaler in scaler_set['procedures']:
                scaler.fit(df[existing_features])
        return self

    def transform(self, df):
        df_transformed = df.copy()
        original_columns = df.columns.tolist()
        
        for scaler_set in self.scalers:
            # Add missing columns with zeros
            for feature in scaler_set['features']:
                if feature not in df_transformed.columns:
                    df_transformed[feature] = 0
            
            existing_features = [feature for feature in scaler_set['features'] if feature in df_transformed.columns]
            if not existing_features:
                continue
                
            for scaler in scaler_set['procedures']:
                df_transformed[existing_features] = scaler.transform(df_transformed[existing_features])
        
        # Remove the added columns, retaining only the original columns
        return df_transformed[original_columns]

    def inverse_transform(self, df):
        df_inversed = df.copy()
        original_columns = df.columns.tolist()
        
        for scaler_set in reversed(self.scalers):
            # Add missing columns with zeros
            for feature in scaler_set['features']:
                if feature not in df_inversed.columns:
                    df_inversed[feature] = 0
                    
            existing_features = [feature for feature in scaler_set['features'] if feature in df_inversed.columns]
            if not existing_features:
                continue
                
            for scaler in reversed(scaler_set['procedures']):
                df_inversed[existing_features] = scaler.inverse_transform(df_inversed[existing_features])
        
        # Remove the added columns, retaining only the original columns
        return df_inversed[original_columns]



from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class GlobalMinMaxScaler(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.global_min_ = None
        self.global_max_ = None
    
    def fit(self, X, y=None):
        self.global_min_ = np.min(X)
        self.global_max_ = np.max(X)
        return self
    
    def transform(self, X):
        if self.global_min_ is None or self.global_max_ is None:
            raise ValueError("This GlobalMinMaxScaler instance is not fitted yet. Call 'fit' with appropriate arguments before using this method.")
        X_scaled = (X - self.global_min_) / (self.global_max_ - self.global_min_)
        return X_scaled
    
    def inverse_transform(self, X):
        # Inverse transform the scaled data
        X_inv_scaled = X * (self.global_max_ - self.global_min_) + self.global_min_
        return X_inv_scaled
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

class CustomMaxAbsScaler(BaseEstimator, TransformerMixin):
    def __init__(self, feature_range=(-1, 1)):
        self.feature_range = feature_range
        self.max_abs_ = None
        self.scale_ = None
        self.min_ = None
    
    def fit(self, X, y=None):
        # Compute the maximum absolute value for each feature
        self.max_abs_ = np.max(np.abs(X), axis=0)
        
        # Calculate the scale_ factor to adjust the range of the data
        self.scale_ = (self.feature_range[1] - self.feature_range[0]) / 2.0
        
        # Calculate the minimum value to shift the scaled data into the target range
        self.min_ = self.feature_range[0]
        
        return self
    
    def transform(self, X):
        # Ensure the scaler was fitted
        if self.max_abs_ is None:
            raise ValueError("This CustomMaxAbsScaler instance is not fitted yet.")
        
        # Scale the data and adjust to the target range
        X_scaled = (X / self.max_abs_) * self.scale_
        X_shifted = X_scaled + self.min_ + self.scale_
        
        return X_shifted

    def inverse_transform(self, X):
        # Reverse the scaling and shifting operations
        X_shifted_back = X - (self.min_ + self.scale_)
        X_orig = X_shifted_back / self.scale_ * self.max_abs_
        return X_orig


from numpy.lib.stride_tricks import as_strided

def window_array(array, y, window_row_length):

    if not isinstance(y, np.ndarray):
        y = np.array(y)
    rows, cols = array.shape 
    stride_row, stride_col = array.strides
    n_windows_row = rows - window_row_length + 1
    X_windowed = as_strided(array, shape=(n_windows_row, window_row_length, cols), 
                            strides=(stride_row, stride_row, stride_col))
    y_windowed = y[window_row_length:]  # Adjusting the slice to align as specified
    return X_windowed[:-1], y_windowed[:n_windows_row]

    